import streamlit as st
import sqlite3
import random
from datetime import datetime

st.set_page_config(page_title="CEX 风险控制仪表盘", layout="wide")
st.title("🔥 CEX 风险控制仪表盘")
st.caption(f"基于 SlowMist 安全实践要求 | 当前时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

st.success("✅ 项目框架初始化成功！")

conn = sqlite3.connect("risk_control.db")
c = conn.cursor()

# ==================== 指标卡片 ====================
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("总资产 (USDT)", "248,392", "+2.4%")
with col2:
    st.metric("风险总分", "23", "-4")
with col3:
    st.metric("今日告警", "9", "🔴")
with col4:
    st.metric("提币通过率", "96.8%", "+0.8%")

st.markdown("---")

# ==================== 测试数据管理 ====================
with st.expander("🧹 测试数据管理", expanded=False):
    st.warning("⚠️ 此操作将清除所有模拟的订单、提现申请和告警记录")
    if st.button("🗑️ 一键清除所有测试数据", type="secondary"):
        c.execute("DELETE FROM orders")
        c.execute("DELETE FROM withdrawals")
        c.execute("DELETE FROM risk_alerts")
        conn.commit()
        st.success("✅ 已清除所有测试数据！页面即将刷新...")
        st.rerun()

# ==================== 模拟实时交易系统 ====================
st.subheader("📈 模拟实时交易系统（订单撮合）")
st.caption("模拟用户下单 → 实时进入 AML 引擎检测")

with st.expander("🛒 发起模拟交易订单", expanded=True):
    col_a, col_b = st.columns(2)
    with col_a:
        user_id = st.number_input("用户 ID", min_value=1000, value=6147, step=1)
        order_type = st.selectbox("交易类型", ["buy", "sell"])
    with col_b:
        amount = st.number_input("交易金额 (USDT)", min_value=5.0, value=6000.0, step=1.0)  # ← 已放宽限制
        asset = st.selectbox("资产", ["USDT", "BTC", "ETH"])

    if st.button("🚀 提交订单（模拟撮合）", type="primary"):
        c.execute("""
            INSERT INTO orders (user_id, order_type, amount, asset, price, status)
            VALUES (?, ?, ?, ?, ?, 'completed')
        """, (user_id, order_type, amount, asset, round(random.uniform(0.8, 1.2), 4)))
        conn.commit()
        
        if amount >= 50000:
            st.error(f"🚨 大额交易告警！金额 {amount:,.0f} USDT")
            c.execute("""
                INSERT INTO risk_alerts (user_id, amount, address, tx_type, tx_time)
                VALUES (?, ?, ?, ?, ?)
            """, (user_id, amount, "0x34......ab7865", "大额交易", datetime.now().strftime("%Y-%m-%d %H:%M")))
            conn.commit()
            st.success("✅ 订单已撮合 + 告警已推送！")
        else:
            st.success("✅ 订单正常撮合完成（无异常）")
        
        st.rerun()

# ==================== 实时交易监控面板 ====================
st.subheader("📊 实时交易监控面板")
st.caption("展示所有历史订单 + 大额交易检测")

orders = c.execute("""
    SELECT user_id, order_type, amount, asset, created_at 
    FROM orders 
    ORDER BY created_at DESC LIMIT 10
""").fetchall()

if orders:
    for uid, otype, amt, ast, t in orders:
        status_color = "🔴" if amt >= 50000 else "🟢"
        tx_type = "BUY" if otype == "buy" else "SELL"
        st.write(f"{status_color} **用户 {uid}** | {tx_type} {amt:,.0f} {ast} | {t}")
else:
    st.info("暂无订单，快去上方发起模拟交易吧！")

st.markdown("---")

# ==================== 今日实时告警预览（只显示最近24小时大额告警） ====================
st.subheader("🚨 今日实时告警预览（联动 AML）")
st.caption("主要展示最近24小时内的大额交易告警")

# 只显示最近24小时的大额交易（≥50000 USDT）
recent_alert_orders = c.execute("""
    SELECT user_id, order_type, amount, asset, created_at 
    FROM orders 
    WHERE amount >= 50000 
      AND created_at >= datetime('now', '-24 hours')
    ORDER BY created_at DESC LIMIT 8
""").fetchall()

if recent_alert_orders:
    for uid, otype, amt, ast, t in recent_alert_orders:
        tx_type = "BUY" if otype == "buy" else "SELL"
        st.error(f"""
            **用户ID: {uid}** | {tx_type} **{amt:,.0f} {ast}** | 时间: {t}
        """, icon="🚨")
else:
    st.info("最近24小时内暂无大额告警记录")

st.info("👈 完整多规则告警管理（含频繁交易、跨设备等）请前往 **AML 反洗钱监控** 页面")

conn.close()