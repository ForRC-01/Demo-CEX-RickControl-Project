import streamlit as st
import sqlite3
from datetime import datetime

st.set_page_config(page_title="告警中心", layout="wide")
st.title("🚨 告警中心仪表盘")
st.caption("统一告警管理平台 | 对应报告 3.3")

# ==================== 1. 详情处理弹窗（仅查看模式） ====================
@st.dialog("🚨 告警详情处理")
def show_detail_dialog(alert):
    st.write(f"**用户ID**: `{alert['user_id']}`")
    st.write(f"**金额**: **{alert['amount']:,.0f} USDT**")
    st.write(f"**告警类型**: {alert['reason']}")
    st.write(f"**发生时间**: {alert['time']}")
    
    st.text_area("处理报告", placeholder="请输入处理意见、依据、后续措施等...", height=150)
    
    # 纯演示按钮，不操作数据库
    if st.button("✅ 完成处理 (演示)", type="primary"):
        st.info("提示：当前为演示预览模式，处理功能暂未开启。")

# ==================== 2. 详情处理报告预览弹窗（针对1002） ====================
@st.dialog("📋 告警处理报告预览")
def show_report_dialog(alert):
    st.write(f"**用户ID**: `{alert['user_id']}`")
    st.write(f"**金额**: **{alert['amount']:,.0f} USDT**")
    st.write(f"**告警原因**: {alert['reason']}")
    st.write(f"**处理时间**: {alert['time']}")
    
    st.markdown("---")
    # 自动填充处理内容
    st.text_area("处理报告内容", value="经检查，无风险。", height=120, disabled=True)
    
    if st.button("关闭"):
        st.rerun()

# ==================== 数据准备 ====================
conn = sqlite3.connect("risk_control.db")
c = conn.cursor()

# 获取数据库动态数据
dynamic_rows = c.execute("SELECT id, user_id, amount, tx_type, tx_time, status FROM risk_alerts").fetchall()
raw_alerts = [{"id": r[0], "user_id": r[1], "amount": r[2], "reason": r[3], "time": r[4], "status": r[5]} for r in dynamic_rows]

# 静态演示案例数据
static_alerts = [
    {"id": 9991, "user_id": 1976, "amount": 60000, "reason": "大额交易 (≥50,000 USDT)", "time": "2026-05-04 18:00:01", "status": "未处理"},
    {"id": 9992, "user_id": 5678, "amount": 250000, "reason": "大额交易 (≥50,000 USDT) + 命中地址黑名单", "time": "2026-05-04 10:30:54", "status": "未处理"},
    {"id": 9993, "user_id": 1002, "amount": 50050, "reason": "大额交易 (≥50,000 USDT)", "time": "2026-05-04 10:30:54", "status": "已处理"}
]

# 合并 + 精确去重（用户ID + 秒级时间）
seen = set()
all_alerts = []
for alert in raw_alerts + static_alerts:
    # 唯一键：用户ID + 完整时间字符串
    unique_key = (alert["user_id"], str(alert["time"]))
    if unique_key not in seen:
        seen.add(unique_key)
        all_alerts.append(alert)

# 按时间倒序排序
all_alerts.sort(key=lambda x: str(x["time"]), reverse=True)

# ==================== 统计指标 ====================
# 基于去重后的列表计算统计数据
total_c = len(all_alerts)
unprocessed_c = len([a for a in all_alerts if a["status"] == "未处理"])
processed_c = total_c - unprocessed_c

col1, col2, col3 = st.columns(3)
with col1: st.metric("总告警", total_c)
with col2: st.metric("未处理", unprocessed_c, "🔴")
with col3: st.metric("已处理", processed_c, "✅")

st.markdown("---")

# ==================== 筛选器区域 ====================
st.subheader("🔍 告警筛选")
f_col1, f_col2, f_col3 = st.columns(3)
with f_col1:
    status_filter = st.selectbox("状态", ["全部", "未处理", "已处理"])
with f_col2:
    type_filter = st.selectbox("告警类型", ["全部", "大额交易", "短时频繁交易", "跨设备登录交易", "高风险用户"])
with f_col3:
    user_filter = st.text_input("用户ID筛选", placeholder="输入用户ID按回车")

# ==================== 告警列表渲染 ====================
st.subheader("📋 告警记录列表")

for alert in all_alerts:
    # 应用筛选逻辑
    if status_filter != "全部" and alert["status"] != status_filter:
        continue
    if type_filter != "全部" and type_filter not in alert["reason"]:
        continue
    if user_filter and str(alert["user_id"]) != user_filter:
        continue

    with st.container(border=True):
        col_a, col_b, col_c = st.columns([5, 2, 2])
        uid = alert["user_id"]
        status = alert["status"]
        
        with col_a:
            icon = "✅" if status == "已处理" else "🔴"
            # 此处 alert['reason'] 已在首页和AML页同步为带阈值的格式
            st.write(f"{icon} **用户ID: {uid}** | 金额: **{alert['amount']:,.0f} USDT** | 类型: {alert['reason']} | 时间: {alert['time']}")
        
        with col_b:
            st.write(f"**状态**: {status}")
            
        with col_c:
            # 按钮显示逻辑判定
            if status == "未处理":
                if st.button("🔍 查看详情进行处理", key=f"btn_p_{uid}_{alert['time']}"):
                    show_detail_dialog(alert)
            elif status == "已处理" and uid == 1002:
                # 针对 1002 静态数据展示处理报告
                if st.button("🔍 查看处理报告", key=f"btn_r_{uid}_{alert['time']}"):
                    show_report_dialog(alert)
            else:
                # 其他已处理数据（如有）仅展示分割线
                st.write("---")

conn.close()