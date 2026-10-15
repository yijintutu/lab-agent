import asyncio
import hashlib
import json
import re
from datetime import date, datetime, time

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.common.exceptions import BusinessException
from app.common.response import PageResponse
from app.database import SessionLocal
from app.models.equipment import Equipment
from app.models.lab import Lab
from app.models.reservation import Reservation
from app.models.reservation_idempotency import ReservationIdempotency
from app.models.user import User
from app.schemas.reservation import ReservationCreateRequest, ReservationResponse

_DATE_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_TIME_PATTERN = re.compile(r"^(?:[01]\d|2[0-3]):[0-5]\d$")


def _validate_iso_date(value: str) -> date:
    if not _DATE_PATTERN.fullmatch(value):
        raise BusinessException(message="预约日期格式必须为 YYYY-MM-DD", code=400)
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise BusinessException(message="预约日期无效", code=400) from exc


def _validate_hhmm(value: str, field_name: str) -> time:
    if not _TIME_PATTERN.fullmatch(value):
        raise BusinessException(
            message=f"{field_name}格式必须为 HH:mm（24小时制）", code=400
        )
    return time.fromisoformat(value)


def _reservation_request_hash(user_id: int, data: ReservationCreateRequest) -> str:
    payload = {
        "user_id": user_id,
        "lab_id": data.lab_id,
        "equipment_id": data.equipment_id,
        "date": data.date,
        "start_time": data.start_time,
        "end_time": data.end_time,
        "remark": data.remark,
    }
    canonical = json.dumps(payload, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _get_idempotent_reservation(
    db: Session,
    current_user: User,
    idempotency_key: str,
    request_hash: str,
    *,
    lock: bool = False,
) -> Reservation | None:
    query = db.query(ReservationIdempotency).filter(
        ReservationIdempotency.idempotency_key == idempotency_key
    )
    if lock:
        query = query.with_for_update()
    existing = query.first()
    if not existing:
        return None
    if existing.user_id != current_user.id or existing.request_hash != request_hash:
        raise BusinessException(message="预约请求标识已被其他请求使用", code=409)
    reservation_query = db.query(Reservation).filter(
        Reservation.id == existing.reservation_id
    )
    if lock:
        reservation_query = reservation_query.with_for_update()
    reservation = reservation_query.first()
    if not reservation:
        raise BusinessException(message="预约幂等记录不完整，请联系管理员", code=500)
    return reservation


def validate_reservation(
    db: Session,
    data: ReservationCreateRequest,
    *,
    lock_lab: bool = False,
) -> tuple[Lab, Equipment | None]:
    """Run the business checks without creating a reservation row."""
    reservation_date = _validate_iso_date(data.date)
    start_time = _validate_hhmm(data.start_time, "预约开始时间")
    end_time = _validate_hhmm(data.end_time, "预约结束时间")
    if end_time <= start_time:
        raise BusinessException(message="预约结束时间必须晚于开始时间", code=400)

    now = datetime.now()
    if reservation_date < now.date():
        raise BusinessException(message="预约日期不能小于当前的日期", code=400)
    current_minute = now.time().replace(second=0, microsecond=0)
    if reservation_date == now.date() and start_time <= current_minute:
        raise BusinessException(message="预约开始时间必须晚于当前时间", code=400)

    lab_query = db.query(Lab).filter(Lab.id == data.lab_id)
    if lock_lab:
        lab_query = lab_query.with_for_update()
    lab = lab_query.first()
    if not lab:
        raise BusinessException(message="实验室不存在", code=404)
    if lab.status != 1:
        raise BusinessException(message="实验室已关闭", code=409)
    if lab.open_time and start_time < _validate_hhmm(lab.open_time, "实验室开放时间"):
        raise BusinessException(message="预约时间不能早于实验室的开放时间", code=400)
    if lab.close_time and end_time > _validate_hhmm(lab.close_time, "实验室关闭时间"):
        raise BusinessException(message="预约时间不能晚于实验室的关闭时间", code=400)

    equipment: Equipment | None = None
    if data.equipment_id is not None:
        equipment = (
            db.query(Equipment).filter(Equipment.id == data.equipment_id).first()
        )
        if not equipment:
            raise BusinessException(message="实验室设备不存在", code=404)
        if equipment.lab_id != lab.id:
            raise BusinessException(message="设备不属于所选实验室", code=400)
        if equipment.status != 1:
            raise BusinessException(message="实验室设备正在维修", code=409)

    overlap_query = db.query(Reservation).filter(
        Reservation.lab_id == data.lab_id,
        Reservation.date == data.date,
        Reservation.status.in_([0, 1]),
        Reservation.start_time < data.end_time,
        Reservation.end_time > data.start_time,
    )
    if data.equipment_id is not None:
        overlap_query = overlap_query.filter(
            Reservation.equipment_id == data.equipment_id
        )
    else:
        overlap_query = overlap_query.filter(Reservation.equipment_id.is_(None))
    if overlap_query.first():
        raise BusinessException(message="该时段已预约", code=409)
    return lab, equipment


def create_reservation(
    db: Session,
    current_user: User,
    data: ReservationCreateRequest,
    *,
    idempotency_key: str | None = None,
) -> Reservation:
    """Create a reservation through the existing business-service boundary.

    On MySQL, the parent lab row lock serializes reservation writes for the same
    lab. The idempotency row makes a graph retry safe after a successful DB commit.
    """
    request_hash = _reservation_request_hash(current_user.id, data)
    if idempotency_key is not None:
        if not idempotency_key.strip() or len(idempotency_key) > 128:
            raise BusinessException(message="预约幂等键无效", code=400)

    try:
        # Do not issue a normal consistent read before this locking read. Under
        # MySQL REPEATABLE READ, that could establish a stale snapshot before a
        # competing request commits while this transaction waits for the lab.
        # Locking the parent row serializes same-lab writes first.
        lab = (
            db.query(Lab)
            .filter(Lab.id == data.lab_id)
            .with_for_update()
            .first()
        )
        if not lab:
            raise BusinessException(message="实验室不存在", code=404)
        if idempotency_key is not None:
            existing_reservation = _get_idempotent_reservation(
                db,
                current_user,
                idempotency_key,
                request_hash,
                lock=True,
            )
            if existing_reservation:
                db.rollback()
                return existing_reservation
        lab, _equipment = validate_reservation(db, data, lock_lab=False)
        reservation = Reservation(
            user_id=current_user.id,
            lab_id=lab.id,
            equipment_id=data.equipment_id,
            date=data.date,
            start_time=data.start_time,
            end_time=data.end_time,
            remark=data.remark,
            status=0,
        )
        db.add(reservation)
        db.flush()
        if idempotency_key is not None:
            db.add(
                ReservationIdempotency(
                    idempotency_key=idempotency_key,
                    request_hash=request_hash,
                    user_id=current_user.id,
                    reservation_id=reservation.id,
                )
            )
        db.commit()
        db.refresh(reservation)
        return reservation
    except IntegrityError as exc:
        db.rollback()
        if idempotency_key is not None:
            existing_reservation = _get_idempotent_reservation(
                db, current_user, idempotency_key, request_hash
            )
            if existing_reservation:
                return existing_reservation
        raise BusinessException(message="预约提交冲突，请刷新后重试", code=409) from exc


def get_reservation_page_list(
    db: Session,
    current_user: User,
    page: int,
    page_size: int,
    status: int | None = None,
):
    """查询预约的记录"""
    query = db.query(Reservation)
    if current_user.role != "admin":
        query = query.filter(Reservation.user_id == current_user.id)
    if status is not None:
        query = query.filter(Reservation.status == status)
    total = query.count()
    items = (
        query.order_by(Reservation.id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    result = []
    for item in items:
        res = ReservationResponse.model_validate(item)
        res.user_name = item.user.name if item.user else None
        res.lab_name = item.lab.name if item.lab else None
        res.equipment_name = item.equipment.name if item.equipment else None
        res.type = "设备" if item.equipment_id else "实验室"
        result.append(res)

    return PageResponse(list=result, total=total)


def cancel_reservation(db: Session, current_user: User, reservation_id: int):
    """学生取消预约"""
    item = db.query(Reservation).filter(Reservation.id == reservation_id).first()
    if not item:
        raise BusinessException(message="预约记录不存在")
    if item.user_id != current_user.id:
        raise BusinessException(message="无权限", code=403)
    if item.status != 0:
        raise BusinessException(message="当前状态无法取消")
    item.status = 3
    db.commit()


def audit_reservation(db: Session, reservation_id: int, status: int):
    """管理员审核预约"""
    if status not in [1, 2]:
        raise BusinessException(message="审核状态错误")
    item = db.query(Reservation).filter(Reservation.id == reservation_id).first()
    if not item:
        raise BusinessException(message="预约记录不存在")
    if item.status != 0:
        raise BusinessException(message="当前状态不支持审核")
    item.status = status
    db.commit()


# 定期扫描过期预约
def expire_pending_reservations():
    db = SessionLocal()
    try:
        now = datetime.now()
        today = now.strftime("%Y-%m-%d")
        now_time = now.strftime("%H:%M")
        items = db.query(Reservation).filter(Reservation.status == 0).all()
        changed = False
        for item in items:
            if item.date < today or (item.date == today and item.end_time <= now_time):
                item.status = 3
                changed = True
        if changed:
            db.commit()
    finally:
        db.close()


async def run_expire_scan():
    """60秒扫描一次过期预约"""
    while True:
        expire_pending_reservations()
        await asyncio.sleep(60)
