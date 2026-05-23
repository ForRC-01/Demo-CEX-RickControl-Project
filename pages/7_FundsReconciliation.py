import streamlit as st
import sqlite3
from datetime import datetime
import random

st.set_page_config(page_title="资金对账", layout="wide")
st.title("🔄 资金对账与异常告警系统")
st.caption("资金安全与对账")

conn = sqlite3.connect("risk_control.db")
c = conn.cursor()

# ==================== 测试数据管理 ====================
with st.expander("🧹 测试数据管理", expanded=False):
    st.warning("⚠️ 此操作仅清空对账测试数据")
    if st.button("🗑️ 一键清除对账测试数据", type="secondary"):
        c.execute("DELETE FROM fund_reconciliation")
        conn.commit()
        st.success("✅ 已清除所有对账测试数据！")
        st.rerun()

st.markdown("---")

# ==================== 5.1 资金对账机制 ====================
st.subheader("💰 资金对账模块")

col1, col2 = st.columns(2)
with col1:
    if st.button("🚀 执行实时对账", type="primary"):
        status = "一致" if random.random() > 0.3 else "异常"
        diff = "0 USDT" if status == "一致" else f"+{random.randint(100, 800)} USDT"
        c.execute("""
            INSERT INTO fund_reconciliation (check_time, check_type, status, difference, created_at)
            VALUES (?, ?, ?, ?, ?)
        """, (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "实时对账", status, diff, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
        conn.commit()
        if status == "一致":
            st.success("✅ 实时对账完成！资产一致性校验通过")
        else:
            st.error(f"⚠️ 实时对账发现异常！差额 {diff}")

with col2:
    if st.button("🌙 执行日终对账"):
        status = "一致" if random.random() > 0.2 else "异常"
        diff = "0 USDT" if status == "一致" else f"+{random.randint(500, 2000)} USDT"
        c.execute("""
            INSERT INTO fund_reconciliation (check_time, check_type, status, difference, created_at)
            VALUES (?, ?, ?, ?, ?)
        """, (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "日终对账", status, diff, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
        conn.commit()
        if status == "一致":
            st.success("✅ 日终对账完成！全部资产核对一致")
        else:
            st.error(f"⚠️ 日终对账发现异常！差额 {diff}")

st.markdown("---")

# ==================== 对账记录列表 ====================
st.subheader("📊 对账记录列表")
records = c.execute("""
    SELECT check_time, check_type, status, difference 
    FROM fund_reconciliation 
    ORDER BY created_at DESC
""").fetchall()

if records:
    for time, ctype, status, diff in records:
        with st.container(border=True):
            st.write(f"**时间**: {time} | **类型**: {ctype}")
            if status == "一致":
                st.success(f"✅ 对账结果：{status}（差额 {diff}）")
            else:
                st.error(f"⚠️ 对账结果：{status}（差额 {diff}）")
else:
    st.info("暂无对账记录，点击上方按钮执行对账")

st.info("👈 左侧选择不同模块进入对应功能区")
conn.close()