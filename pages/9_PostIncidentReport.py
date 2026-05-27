import streamlit as st
import sqlite3
from datetime import datetime

st.set_page_config(page_title="事后报告", layout="wide")
st.title("📋 事后报告")
st.caption("重大事件复盘")

# ==================== 创建数据库表 ====================
conn = sqlite3.connect("risk_control.db")
c = conn.cursor()
c.execute("""
    CREATE TABLE IF NOT EXISTS post_incident_reports (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        event_title TEXT,
        event_time TEXT,
        severity TEXT,
        status TEXT,
        description TEXT,
        impact TEXT,
        root_cause TEXT,
        measures TEXT,
        created_at TEXT
    )
""")
conn.commit()
conn.close()

# ==================== 测试数据管理 ====================
with st.expander("🧹 测试数据管理", expanded=False):
    st.warning("⚠️ 此操作将清除所有事后报告历史记录")
    if st.button("🗑️ 一键清除测试记录", type="secondary"):
        conn = sqlite3.connect("risk_control.db")
        conn.execute("DELETE FROM post_incident_reports")
        conn.commit()
        conn.close()
        st.success("✅ 已清除所有事后报告记录！")
        st.rerun()

st.markdown("---")

# ==================== 标准化事后报告模板 ====================
st.subheader("标准化事后报告模板")

with st.expander("📝 填写并生成新报告", expanded=True):
    col1, col2 = st.columns(2)
    with col1:
        event_title = st.text_input("事件标题", value="大规模异常提现事件")
        event_time = st.text_input("事件发生时间", value="2026-05-25 18:48:02")   # ← 支持你手动填写
    with col2:
        severity = st.selectbox("事件严重程度", ["低", "中", "高", "极高"], index=2)
        status = st.selectbox("当前状态", ["已暂停", "已解除", "处理中"], index=0)

    description = st.text_area("1. 事件描述", height=100, 
        value="用户2008、2012等多个高风险账号在短时间内进行大额提现，金额超过阈值且命中部分黑名单特征。")
    
    impact = st.text_area("2. 影响评估", height=80,
        value="涉及资金约 450,000 USDT，触发紧急暂停，全站交易暂停约 45 分钟。")
    
    root_cause = st.text_area("3. 根因分析", height=100,
        value="• AML 短时频率阈值设置偏松\n• 高风险用户标签未及时联动提现限额\n• 跨设备行为识别缺失")
    
    measures = st.text_area("4. 改进措施", height=120,
        value="• 将短时频繁交易阈值从5次/小时调整为3次/小时\n• 加强高风险用户与提现审核联动\n• 增加事后复盘模板自动化生成\n• 下次进行应急演练")

    if st.button("💾 生成并保存事后报告", type="primary"):
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        conn = sqlite3.connect("risk_control.db")
        conn.execute("""
            INSERT INTO post_incident_reports 
            (event_title, event_time, severity, status, description, impact, root_cause, measures, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (event_title, event_time, severity, status, description, impact, root_cause, measures, now))
        conn.commit()
        conn.close()
        st.success("✅ 事后报告已成功保存！")
        st.balloons()
        st.rerun()

st.markdown("---")

# ==================== 历史报告模块 ====================
st.subheader("📜 历史事后报告（按时间倒序）")

conn = sqlite3.connect("risk_control.db")
reports = conn.execute("""
    SELECT id, event_title, event_time, severity, created_at 
    FROM post_incident_reports 
    ORDER BY created_at DESC
""").fetchall()
conn.close()

for rid, title, etime, sev, ctime in reports:
    with st.container(border=True):
        st.write(f"**{title}** | 严重程度：**{sev}** | 发生时间：{etime}")
        st.write(f"生成时间：{ctime}")
        if st.button("📋 查看完整报告", key=f"view_{rid}"):
            st.session_state.selected_report = rid
            st.session_state.show_report = True

# ==================== 查看完整报告弹窗 ====================
@st.dialog("完整事后报告")
def show_full_report():
    rid = st.session_state.selected_report
    conn = sqlite3.connect("risk_control.db")
    report = conn.execute("""
        SELECT event_title, event_time, severity, status, description, 
               impact, root_cause, measures, created_at 
        FROM post_incident_reports WHERE id = ?
    """, (rid,)).fetchone()
    conn.close()
    
    if report:
        title, etime, sev, status, desc, imp, cause, meas, ctime = report
        st.write(f"**事件标题**：{title}")
        st.write(f"**发生时间**：{etime}　**严重程度**：{sev}　**状态**：{status}")
        st.write(f"**生成时间**：{ctime}")
        st.markdown("---")
        st.write("**1. 事件描述**")
        st.write(desc)
        st.write("**2. 影响评估**")
        st.write(imp)
        st.write("**3. 根因分析**")
        st.write(cause)
        st.write("**4. 改进措施**")
        st.write(meas)

    if st.button("关闭"):
        st.rerun()

if st.session_state.get("show_report", False):
    show_full_report()
    st.session_state.show_report = False

st.info("此模板可作为真实风控工作中的标准化文档使用")