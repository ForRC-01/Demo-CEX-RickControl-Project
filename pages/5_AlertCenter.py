import streamlit as st
import sqlite3
from datetime import datetime

# 页面配置
st.set_page_config(page_title="告警中心", layout="wide")
st.title("🚨 告警中心仪表盘")
st.caption("统一告警管理平台 | 对应报告 3.3")

# ==================== 详情处理弹窗函数 ====================
@st.dialog("🚨 告警详情处理")
def show_detail_dialog(alert):
    # 【修复报错点】：在弹窗内部建立连接，防止主线程关闭导致报错
    with sqlite3.connect("risk_control.db") as d_conn:
        dc = d_conn.cursor()
        
        st.write(f"**用户ID**: `{alert['user_id']}`")
        st.write(f"**金额**: **{alert['amount']:,.0f} USDT**")
        st.write(f"**告警类型**: {alert['reason']}")
        st.write(f"**发生时间**: {alert['time']}")
        
        st.text_area("处理报告（风控人员填写）", placeholder="请输入处理意见...", height=150)
        
        col_btn1, col_btn2 = st.columns(2)
        with col_btn1:
            if st.button("✅ 完成处理 (演示)", type="primary"):
                # 更新数据库状态
                dc.execute("UPDATE risk_alerts SET status='已处理' WHERE user_id=? AND tx_time=?", 
                          (alert['user_id'], alert['time']))
                d_conn.commit()
                st.success("✅ 状态已更新为已处理")
                st.rerun()
        with col_btn2:
            if st.button("❌ 关闭"):
                st.rerun()

# ==================== 主页面逻辑 ====================
conn = sqlite3.connect("risk_control.db")
c = conn.cursor()

# 统计指标
total = c.execute("SELECT COUNT(*) FROM risk_alerts").fetchone()[0]
unprocessed = c.execute("SELECT COUNT(*) FROM risk_alerts WHERE status='未处理'").fetchone()[0]

m_col1, m_col2, m_col3 = st.columns(3)
with m_col1: st.metric("总告警", total)
with m_col2: st.metric("未处理", unprocessed, "🔴")
with m_col3: st.metric("已处理", total - unprocessed, "✅")

st.markdown("---")

# 筛选器
st.subheader("🔍 告警筛选")
f_col1, f_col2, f_col3 = st.columns(3)
with f_col1:
    status_filter = st.selectbox("状态", ["全部", "未处理", "已处理"])
with f_col2:
    type_filter = st.selectbox("告警类型", ["全部", "大额交易", "短时频繁交易", "跨设备登录交易", "高风险用户"])
with f_col3:
    user_filter = st.text_input("用户ID筛选", placeholder="输入ID按回车")

st.markdown("---")

# ==================== 数据获取与合并去重 ====================
# 1. 获取数据库真实数据
dynamic_rows = c.execute("SELECT id, user_id, amount, tx_type, tx_time, status FROM risk_alerts").fetchall()
raw_alerts = [{"id": r[0], "user_id": r[1], "amount": r[2], "reason": r[3], "time": r[4], "status": r[5]} for r in dynamic_rows]

# 2. 静态展示数据
static_alerts = [
    {"id": 9991, "user_id": 1976, "amount": 60000, "reason": "大额交易 (≥50,000 USDT)", "time": "2026-05-04 18:00:01", "status": "未处理"},
    {"id": 9992, "user_id": 5678, "amount": 250000, "reason": "大额提币 + 命中地址黑名单", "time": "2026-05-04 10:30:54", "status": "未处理"},
    {"id": 9993, "user_id": 1002, "amount": 50050, "reason": "大额交易 (≥50,000 USDT)", "time": "2026-05-04 10:30:54", "status": "已处理"}
]

# 3. 核心去重：数据库数据和静态案例合并，以 (用户ID + 时间秒) 为唯一键
seen = set()
all_alerts = []
for alert in raw_alerts + static_alerts:
    # 强制将时间转为字符串进行去重匹配
    unique_key = (alert["user_id"], str(alert["time"]))
    if unique_key not in seen:
        seen.add(unique_key)
        all_alerts.append(alert)

# 按时间倒序排序
all_alerts.sort(key=lambda x: str(x["time"]), reverse=True)

# ==================== 列表渲染 ====================
st.subheader("📋 告警记录列表")

for alert in all_alerts:
    # 筛选逻辑应用
    if status_filter != "全部" and alert["status"] != status_filter: continue
    if user_filter and str(alert["user_id"]) != user_filter: continue
    if type_filter != "全部" and type_filter not in alert["reason"]: continue

    with st.container(border=True):
        col_a, col_b, col_c = st.columns([5, 2, 2])
        status = alert["status"]
        with col_a:
            # 这里的图标严格跟随 status 字段，不再根据用户ID硬编码
            icon = "✅" if status == "已处理" else "🔴"
            st.write(f"{icon} **用户ID: {alert['user_id']}** | 金额: **{alert['amount']:,.0f} USDT** | 类型: {alert['reason']} | 时间: {alert['time']}")
        with col_b:
            st.write(f"**状态**: {status}")
        with col_c:
            # 只有未处理状态才显示按钮
            if status == "未处理":
                if st.button("🔍 查看详情进行处理", key=f"btn_{alert['user_id']}_{alert['time']}"):
                    show_detail_dialog(alert)
            else:
                st.write("---")

conn.close()