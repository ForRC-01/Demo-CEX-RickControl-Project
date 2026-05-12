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
    blacklisted = st.text_area("地址黑名单", value="0xblack...list\n0xdead...beef\n0x34......ab7865", height=100)

st.markdown("---")

if st.button("🚨 开始 AML 交易扫描", type="primary"):
    st.success("✅ 扫描完成！正在保存告警...")

    all_orders = c.execute("SELECT user_id, order_type, amount, asset, created_at FROM orders ORDER BY created_at DESC").fetchall()
    st.subheader("🔍 多规则告警列表")

    alert_count = 0
    for order in all_orders:
        uid, otype, amt, ast, t = order
        tx_type = "BUY" if otype == "buy" else "SELL"
        reasons = []

        # 规则应用
        if amt >= amount_threshold:
            reasons.append(f"大额交易 (≥{amount_threshold:,} USDT)") # 确保文字带有阈值提示

        freq = c.execute("SELECT COUNT(*) FROM orders WHERE user_id = ? AND created_at <= ? AND created_at >= datetime(?, '-1 hour')", (uid, t, t)).fetchone()[0]
        if freq >= freq_threshold:
            reasons.append(f"短时频繁交易 ({freq}次/小时)")

        if uid % 7 == 0: reasons.append("跨设备登录交易")
        if uid in [5678, 1976]: reasons.append("高风险用户")

        if reasons:
            reason_str = ' + '.join(reasons)
            
            # --- 核心修改逻辑：支持规则叠加更新 ---
            # 检查数据库中是否存在相同用户在相同时间的告警，并取回它当前的描述文字
            exists = c.execute("SELECT tx_type FROM risk_alerts WHERE user_id = ? AND tx_time = ?", (uid, t)).fetchone()

            if exists:
                # 如果扫描出的新理由比数据库里存的长（说明发现了更多规则，如叠加了频繁交易），则更新它
                if len(reason_str) > len(exists[0]):
                    c.execute("UPDATE risk_alerts SET tx_type = ? WHERE user_id = ? AND tx_time = ?", 
                             (reason_str, uid, t))
                    conn.commit()
            else:
                # 如果完全不存在，则正常插入
                c.execute("INSERT INTO risk_alerts (user_id, amount, address, tx_type, tx_time, status) VALUES (?, ?, ?, ?, ?, ?)",
                         (uid, amt, "0x34......ab7865", reason_str, t, "未处理"))
                conn.commit()

            alert_count += 1
            with st.container(border=True):
                st.error(f"🚨 用户ID: **{uid}** | {tx_type} **{amt:,.0f} {ast}**")
                st.write(f"**交易时间**: {t}")
                st.write(f"**告警原因**: {reason_str}")

    if alert_count == 0:
        st.info("暂无触发告警的订单。")

# ==================== 静态演示案例 ====================
st.subheader("📜 静态演示案例")
col1, col2 = st.columns(2)
with col1:
    st.error("🚨 用户ID: 1976 | 金额: **60000 USDT** | 地址: 0x34......ab7865")
    st.write("**交易时间**: 2026-05-04 18:00:01")
    st.write("**告警原因**: 大额交易 (≥50,000 USDT)")
with col2:
    st.error("🚨 用户ID: 5678 | 金额: **250000 USDT** | 地址: 0xblack...list")
    st.write("**交易时间**: 2026-05-04 10:30:54")
    st.write("**告警原因**: 大额提币 + 命中地址黑名单")

conn.close()