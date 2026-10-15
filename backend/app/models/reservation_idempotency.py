from sqlalchemy import ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class ReservationIdempotency(Base):
    """Idempotency record for an agent-initiated reservation write."""

    __tablename__ = "reservation_idempotency"
    __table_args__ = (
        UniqueConstraint("idempotency_key", name="uq_reservation_idempotency_key"),
        UniqueConstraint(
            "reservation_id", name="uq_reservation_idempotency_reservation"
        ),
        {"comment": "预约写入幂等记录"},
    )

    idempotency_key: Mapped[str] = mapped_column(String(128), nullable=False)
    request_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"), nullable=False, index=True
    )
    reservation_id: Mapped[int] = mapped_column(
        ForeignKey("reservations.id"), nullable=False
    )
