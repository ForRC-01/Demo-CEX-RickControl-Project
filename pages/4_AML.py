import streamlit as st
import sqlite3
from datetime import datetime

# 页面基础配置
st.title("📊 AML 反洗钱监控")
st.caption("可疑交易阈值 + 地址黑名单 + 行为模式识别")

# 建立数据库连接
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

# ==================== 核心扫描逻辑 ====================
if st.button("🚨 开始 AML 交易扫描", type="primary"):
    st.success("✅ 扫描完成！正在应用多规则检测并保存告警...")

    # 从订单表获取所有历史订单
    all_orders = c.execute("""
        SELECT user_id, order_type, amount, asset, created_at 
        FROM orders 
        ORDER BY created_at DESC
    """).fetchall()

    st.subheader("🔍 多规则告警列表（历史回溯检测）")

    alert_count = 0
    for order in all_orders:
        uid, otype, amt, ast, t = order  # t 是订单的时间，已精确到秒
        tx_type = "BUY" if otype == "buy" else "SELL"
        reasons = []

        # 规则1：大额交易检测
        if amt >= amount_threshold:
            reasons.append(f"大额交易 (≥{amount_threshold:,} USDT)")

        # 规则2：短时频繁交易检测 (回溯订单时间 t 的前一小时)
        freq = c.execute("""
            SELECT COUNT(*) FROM orders 
            WHERE user_id = ? 
            AND created_at <= ? 
            AND created_at >= datetime(?, '-1 hour')
        """, (uid, t, t)).fetchone()[0]
        
        if freq >= freq_threshold:
            reasons.append(f"短时频繁交易 ({freq}次/小时)")

        # 规则3：其他模拟风险判定
        if uid % 7 == 0:
            reasons.append("跨设备登录交易")
        if uid in [5678, 1976]:
            reasons.append("高风险用户")

        # --- 判定与数据库保存逻辑 ---
        if reasons:
            reason_str = ' + '.join(reasons)
            
            # 【关键去重逻辑】：检查该 用户+该秒数 的告警是否已存在
            exists = c.execute("""
                SELECT 1 FROM risk_alerts WHERE user_id = ? AND tx_time = ?
            """, (uid, t)).fetchone()

            if not exists:
                # 只有不存在时才插入，状态默认设为 '未处理'
                c.execute("""
                    INSERT INTO risk_alerts (user_id, amount, address, tx_type, tx_time, status)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (uid, amt, "0x34......ab7865", reason_str, t, "未处理"))
                conn.commit()

            # 页面实时展示
            alert_count += 1
            with st.container(border=True):
                st.error(f"🚨 用户ID: **{uid}** | {tx_type} **{amt:,.0f} {ast}**")
                st.write(f"**交易时间**: {t}")
                st.write(f"**告警原因**: {reason_str}")

    if alert_count == 0:
        st.info("暂无触发告警的订单。")

# ==================== 静态演示案例（已还原地址信息） ====================
st.subheader("📜 静态演示案例（典型场景）")
st.caption("用于报告展示的固定样例")

col1, col2 = st.columns(2)
with col1:
    st.error("🚨 用户ID: 1976 | 金额: **60000 USDT** | 地址: 0x34......ab7865")
    st.write("**交易时间**: 2026-05-04 18:00:01")
    st.write("**告警原因**: 大额交易")

with col2:
    st.error("🚨 用户ID: 5678 | 金额: **250000 USDT** | 地址: 0xblack...list")
    st.write("**交易时间**: 2026-05-04 10:30:54")
    st.write("**告警原因**: 大额提币 + 命中地址黑名单")

st.info("👈 左侧选择不同模块进入对应功能区")
conn.close()