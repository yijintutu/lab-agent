# -*- coding: utf-8 -*-
"""
实验室管理系统 - 测试数据初始化脚本（幂等，可重复运行）

目标状态：8 间实验室，每间 4 台设备，共 32 台设备。
- lab1：更新为「计算机基础实验室」（原「人工智能实验室」）
- lab2：更新为「电子实验室」（原测试垃圾数据「21地方」），删除其垃圾设备
- lab3 ~ lab8：依次新建 物理 / 化学 / 生物 / 人工智能 / 机器人 / 软件工程 实验室
仅使用标准库，无需安装第三方包。
"""

import json
import urllib.request
import urllib.error

BASE_URL = "http://127.0.0.1:8000/api"
USERNAME = "admin"
PASSWORD = "88888888"

# ------------------------- 目标数据 -------------------------
# key 为期望的实验室 id（当前库 max(id)=2，按顺序新建后自增 id 正好为 3~8）
LABS = {
    1: {
        "name": "计算机基础实验室",
        "description": "配备开发主机与GPU服务器，适合编程与深度学习实验",
        "location": "实验楼 A301",
        "capacity": 30,
        "open_time": "08:00",
        "close_time": "18:00",
        "status": 1,
    },
    2: {
        "name": "电子实验室",
        "description": "电子实验室",
        "location": "综合实验楼201",
        "capacity": 20,
        "open_time": "08:00",
        "close_time": "18:00",
        "status": 1,
    },
    3: {
        "name": "物理实验室",
        "description": "物理实验室",
        "location": "综合实验楼202",
        "capacity": 20,
        "open_time": "08:00",
        "close_time": "18:00",
        "status": 1,
    },
    4: {
        "name": "化学实验室",
        "description": "化学实验室",
        "location": "综合实验楼301",
        "capacity": 20,
        "open_time": "08:00",
        "close_time": "18:00",
        "status": 1,
    },
    5: {
        "name": "生物实验室",
        "description": "生物实验室",
        "location": "综合实验楼302",
        "capacity": 20,
        "open_time": "08:00",
        "close_time": "18:00",
        "status": 1,
    },
    6: {
        "name": "人工智能实验室",
        "description": "人工智能实验室",
        "location": "综合实验楼401",
        "capacity": 30,
        "open_time": "08:00",
        "close_time": "18:00",
        "status": 1,
    },
    7: {
        "name": "机器人实验室",
        "description": "机器人实验室",
        "location": "综合实验楼402",
        "capacity": 20,
        "open_time": "09:00",
        "close_time": "17:00",
        "status": 1,
    },
    8: {
        "name": "软件工程实验室",
        "description": "软件工程实验室",
        "location": "综合实验楼501",
        "capacity": 40,
        "open_time": "08:00",
        "close_time": "20:00",
        "status": 1,
    },
}

# 每间实验室的 4 台设备：(名称, 描述, 规格, 数量, 状态)
EQUIPMENTS = {
    1: [
        ("RTX4090", "深度学习训练显卡", "24G 显存", 2, 1),
        ("开发主机", "学生上机编程", "i7 / 32G / 1T SSD", 20, 1),
        ("投影仪", "讲课演示", "1080P", 1, 1),
        ("千兆交换机", "机房组网", "24 口", 1, 1),
    ],
    2: [
        ("示波器", "电路波形观测", "100MHz 双通道", 8, 1),
        ("信号发生器", "信号源实验", "DDS 60MHz", 6, 1),
        ("数字万用表", "电子测量", "4 位半", 10, 0),
        ("直流稳压电源", "电路供电", "30V 5A", 8, 1),
    ],
    3: [
        ("光学实验台", "几何光学实验", "1.2m 隔振台", 4, 1),
        ("氦氖激光器", "干涉衍射实验", "632.8nm", 2, 1),
        ("力学轨道", "牛顿定律实验", "气垫导轨 1.5m", 3, 1),
        ("分光计", "光谱测量", "0.1° 精度", 4, 1),
    ],
    4: [
        ("电子天平", "试剂称量", "0.1mg", 6, 1),
        ("离心机", "样品分离", "4000rpm", 2, 1),
        ("通风橱", "有机实验", "1.5m", 3, 1),
        ("pH 计", "溶液酸碱度", "0.01pH", 4, 1),
    ],
    5: [
        ("显微镜", "细胞观察", "1000x 光学", 10, 1),
        ("恒温培养箱", "菌种培养", "室温 ~ 60℃", 2, 1),
        ("移液器", "微量取样", "0.5-10μL", 20, 1),
        ("PCR 仪", "基因扩增", "96 孔", 1, 0),
    ],
    6: [
        ("GPU 训练服务器", "大模型微调", "2 * RTX4090 / 128G", 1, 1),
        ("RTX4090（人工智能实验室）", "深度学习训练显卡", "24G 显存", 4, 1),
        ("深度相机", "视觉数据采集", "RealSense D435i", 3, 1),
        ("标注工作站", "数据集标注", "i9 / 64G", 6, 1),
    ],
    7: [
        ("UR5 机械臂", "工业机械臂教学", "负载 5kg", 2, 1),
        ("Livox 激光雷达", "SLAM 建图", "Mid-360", 3, 1),
        ("RealSense 深度相机", "视觉抓取", "D435i", 4, 1),
        ("Jetson Orin", "边缘计算", "32G", 4, 1),
    ],
    8: [
        ("开发主机（软件工程实验室）", "项目实训", "i7 / 32G / 1T SSD", 40, 1),
        ("显示器", "双屏开发", "27 寸 2K", 40, 1),
        ("投影仪（软件工程实验室）", "答辩演示", "1080P", 2, 1),
        ("代码服务器", "Git 与 CI", "8 核 / 32G", 1, 1),
    ],
}


# ------------------------- HTTP 工具 -------------------------
def request(method, path, token=None, body=None):
    url = BASE_URL + path
    data = json.dumps(body).encode("utf-8") if body is not None else None
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header("Content-Type", "application/json")
    if token:
        req.add_header("Authorization", "Bearer " + token)
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            result = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        detail = e.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"{method} {path} -> HTTP {e.code}: {detail}")
    # 统一响应体 {code, message, data}
    if isinstance(result, dict) and "code" in result and result["code"] != 200:
        raise RuntimeError(f"{method} {path} -> 业务错误 code={result['code']}: {result.get('message')}")
    return result.get("data") if isinstance(result, dict) else result


def get_all(path, token):
    """拉取全部分页数据"""
    items, page, page_size = [], 1, 100
    while True:
        data = request("GET", f"{path}?page={page}&page_size={page_size}", token)
        batch = data.get("list", [])
        items.extend(batch)
        if len(items) >= data.get("total", 0) or not batch:
            break
        page += 1
    return items


# ------------------------- 主流程 -------------------------
def main():
    # 1. 登录
    login_data = request("POST", "/auth/login",
                         body={"username": USERNAME, "password": PASSWORD})
    token = login_data["token"]
    print("[1/4] 登录成功")

    # 2. 实验室：存在则更新，不存在则按顺序新建
    existing_labs = {lab["id"]: lab for lab in get_all("/lab/list", token)}
    lab_id_map = {}  # 期望序号 -> 真实 id
    for expected_id in sorted(LABS):
        info = LABS[expected_id]
        if expected_id in existing_labs:
            request("PUT", f"/lab/{expected_id}", token, info)
            lab_id_map[expected_id] = expected_id
            print(f"      更新实验室 id={expected_id} {info['name']}")
        else:
            created = request("POST", "/lab", token, info)
            real_id = created["id"]
            lab_id_map[expected_id] = real_id
            print(f"      新建实验室 id={real_id} {info['name']}")
    print(f"[2/4] 实验室就绪，共 {len(lab_id_map)} 间")

    # 3. 设备：按 (lab_id, name) 对齐，多余的删除，缺失的新建
    existing_eq = get_all("/equipment/list", token)
    eq_index = {(e["lab_id"], e["name"]): e for e in existing_eq}

    # 3.1 删除目标清单之外的设备（如 lab2 的垃圾设备「电饭锅都」）
    target_keys = set()
    for expected_lab_id, eq_list in EQUIPMENTS.items():
        real_lab_id = lab_id_map[expected_lab_id]
        for name, _, _, _, _ in eq_list:
            target_keys.add((real_lab_id, name))

    for e in existing_eq:
        if (e["lab_id"], e["name"]) not in target_keys:
            request("DELETE", f"/equipment/{e['id']}", token)
            print(f"      删除多余设备 id={e['id']} lab_id={e['lab_id']} {e['name']}")

    # 3.2 新建缺失设备
    created_count = 0
    for expected_lab_id in sorted(EQUIPMENTS):
        real_lab_id = lab_id_map[expected_lab_id]
        for name, desc, spec, qty, status in EQUIPMENTS[expected_lab_id]:
            if (real_lab_id, name) in eq_index:
                continue
            request("POST", "/equipment", token, {
                "lab_id": real_lab_id,
                "name": name,
                "description": desc,
                "spec": spec,
                "quantity": qty,
                "status": status,
            })
            created_count += 1
            print(f"      新建设备 lab_id={real_lab_id} {name} x{qty} status={status}")
    print(f"[3/4] 设备处理完成，本次新建 {created_count} 台")

    # 4. 回读校验
    final_labs = get_all("/lab/list", token)
    final_eq = get_all("/equipment/list", token)
    per_lab = {}
    for e in final_eq:
        per_lab[e["lab_id"]] = per_lab.get(e["lab_id"], 0) + 1
    print("[4/4] 最终校验：")
    for lab in sorted(final_labs, key=lambda x: x["id"]):
        print(f"      id={lab['id']} {lab['name']} -> 设备 {per_lab.get(lab['id'], 0)} 台")
    print(f"      实验室合计 {len(final_labs)} 间，设备合计 {len(final_eq)} 台")

    ok = len(final_labs) == 8 and len(final_eq) == 32 and all(
        per_lab.get(lab_id, 0) == 4 for lab_id in [lab_id_map[i] for i in range(1, 9)]
    )
    print("结果：" + ("全部符合预期 ✔" if ok else "存在偏差，请检查上方明细 ✘"))


if __name__ == "__main__":
    main()
