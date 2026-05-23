import streamlit as st
import sqlite3
from datetime import datetime
import random

st.set_page_config(page_title="资金对账", layout="wide")
st.title("🔄 资金对账与异常告警系统")
st.caption("资金安全与对账 | 对应报告 第5章")

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

# ==================== 5.1 资金对账模块 ====================
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
st.subheader("📊 对账记录列表（全部历史）")
records = c.execute("""
    SELECT id, check_time, check_type, status, difference 
    FROM fund_reconciliation 
    ORDER BY created_at DESC
""").fetchall()

for rid, time, ctype, status, diff in records:
    with st.container(border=True):
        col_a, col_b = st.columns([6, 3])
        with col_a:
            st.write(f"**时间**: {time} | **类型**: {ctype}")
            if status == "一致":
                st.success(f"✅ 对账结果：{status}（差额 {diff}）")
            elif "已处理" in status:
                st.success(f"✅ 对账结果：{status}（差额 {diff}）")
            else:
                st.error(f"⚠️ 对账结果：{status}（差额 {diff}）")
        with col_b:
            if "已处理" in status:
                if st.button("📋 查看处理报告", key=f"report_{rid}"):
                    st.session_state.selected_record = (rid, time, ctype, diff)
                    st.session_state.show_report = True

# ==================== 5.2 异常资金处理中心 ====================
st.subheader("⚠️ 异常资金处理中心")

abnormal_records = c.execute("""
    SELECT id, check_time, check_type, difference 
    FROM fund_reconciliation 
    WHERE status = '异常' 
    ORDER BY created_at DESC
""").fetchall()

if abnormal_records:
    for rid, time, ctype, diff in abnormal_records:
        with st.container(border=True):
            st.error(f"**时间**: {time} | **类型**: {ctype} | **差额**: {diff}")
            if st.button("🔍 查看详情 & 标记已处理", key=f"handle_{rid}"):
                st.session_state.selected_record = (rid, time, ctype, diff)
                st.session_state.show_dialog = True
else:
    st.success("🎉 当前暂无异常资金记录")

# ==================== 5.3 对账报告生成 ====================
st.subheader("📄 5.3 对账报告生成示例")

if st.button("📊 生成今日对账报告", type="primary"):
    total_checks = len(records)
    abnormal_count = len(abnormal_records)
    st.success(f"✅ 对账报告生成成功！")
    st.write(f"**报告时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    st.write(f"**总对账次数**: {total_checks} 次")
    st.write(f"**异常次数**: {abnormal_count} 次")
    st.write(f"**总体状态**: {'正常' if abnormal_count == 0 else '存在异常'}")

st.info("👈 左侧选择不同模块进入对应功能区")
conn.close()

# ==================== 弹窗部分（保持不变） ====================
@st.dialog("异常处理")
def show_processing_dialog():
    rid, time, ctype, diff = st.session_state.selected_record
    st.write(f"**时间**: {time}")
    st.write(f"**类型**: {ctype}")
    st.write(f"**差额**: {diff}")
    note = st.text_area("处理意见", "经人工核实，差额为系统延迟导致，已调整。")
    if st.button("✅ 标记已处理", type="primary"):
        conn = sqlite3.connect("risk_control.db")
        conn.execute("UPDATE fund_reconciliation SET status = '已处理' WHERE id=?", (rid,))
        conn.commit()
        conn.close()
        st.success("✅ 已标记为已处理")
        st.rerun()

@st.dialog("处理报告")
def show_report_dialog():
    rid, time, ctype, diff = st.session_state.selected_record
    st.write(f"**时间**: {time}")
    st.write(f"**类型**: {ctype}")
    st.write(f"**差额**: {diff}")
    st.write("**处理意见**: 经人工核实，差额为系统延迟导致，已调整。")
    if st.button("关闭"):
        st.rerun()

if st.session_state.get("show_dialog", False):
    show_processing_dialog()
    st.session_state.show_dialog = False

if st.session_state.get("show_report", False):
    show_report_dialog()
    st.session_state.show_report = False