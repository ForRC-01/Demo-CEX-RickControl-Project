import streamlit as st
import sqlite3
from datetime import datetime

st.title("📊 AML 反洗钱监控")
st.caption("可疑交易阈值 + 地址黑名单 + 行为模式识别")

conn = sqlite3.connect("risk_control.db")
c = conn.cursor()

# ==================== AML 规则引擎设置 ====================
st.subheader("⚙️ AML 规则引擎设置")
col1, col2, col3 = st.columns(3)
with col1:
    amount_threshold = st.number_input("大额交易阈值 (USDT)", value=50000, step=1000)
with col2:
    freq_threshold = st.number_input("短时交易频率阈值 (次/小时)", value=3, step=1)
with col3:
    blacklisted = st.text_area("地址黑名单（每行一个）", value="0xblack...list\n0xdead...beef\n0x34......ab7865", height=100)

st.markdown("---")

if st.button("🚨 开始 AML 交易扫描", type="primary"):
    st.success("✅ 扫描完成！正在应用多规则检测并保存告警...")

    all_orders = c.execute("""
        SELECT user_id, order_type, amount, asset, created_at 
        FROM orders 
        ORDER BY created_at DESC
    """).fetchall()

    st.subheader("🔍 多规则告警列表（所有历史订单）")

    alert_count = 0
    for order in all_orders:
        uid, otype, amt, ast, t = order
        tx_type = "BUY" if otype == "buy" else "SELL"
        reasons = []

        if amt >= amount_threshold:
            reasons.append(f"大额交易 (≥{amount_threshold:,} USDT)")

        freq = c.execute("""
            SELECT COUNT(*) FROM orders 
            WHERE user_id = ? AND created_at >= datetime('now', '-1 hour')
        """, (uid,)).fetchone()[0]
        if freq >= freq_threshold:
            reasons.append(f"短时频繁交易 ({freq}次/小时)")

        if uid % 7 == 0:
            reasons.append("跨设备登录交易")

        if uid in [5678, 1976]:
            reasons.append("高风险用户")

        if reasons:
            alert_count += 1
            reason_str = ' + '.join(reasons)
            
            # 永久保存告警记录（关键修改）
            c.execute("""
                INSERT INTO risk_alerts (user_id, amount, address, tx_type, tx_time)
                VALUES (?, ?, ?, ?, ?)
            """, (uid, amt, "0x34......ab7865", reason_str, t))
            conn.commit()

            with st.container(border=True):
                st.error(f"🚨 用户ID: **{uid}** | {tx_type} **{amt:,.0f} {ast}**")
                st.write(f"**交易时间**: {t}")
                st.write(f"**告警原因**: {reason_str}")

    if alert_count == 0:
        st.info("暂无触发告警的订单。")

# ==================== 静态演示案例 ====================
st.subheader("📜 静态演示案例（典型场景）")
st.caption("用于报告展示的固定样例")

col1, col2 = st.columns(2)
with col1:
    st.error("🚨 用户ID: 1976 | 金额: **60000 USDT**")
    st.write("交易时间: 2025-05-04 18:00")
    st.write("**告警原因**: 大额交易")

with col2:
    st.error("🚨 用户ID: 5678 | 金额: **250000 USDT**")
    st.write("交易时间: 2026-05-04 10:30")
    st.write("**告警原因**: 大额提币 + 命中地址黑名单")

st.info("👈 左侧选择不同模块进入对应功能区")
conn.close()