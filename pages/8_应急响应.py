import streamlit as st
import sqlite3
from datetime import datetime

st.set_page_config(page_title="应急响应", layout="wide")
st.title("🚨 应急响应与紧急暂停")
st.caption("重大风险事件处置")

# ==================== 创建历史记录表 ====================
conn = sqlite3.connect("risk_control.db")
c = conn.cursor()
c.execute("""
    CREATE TABLE IF NOT EXISTS emergency_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        action TEXT,
        reason TEXT,
        time TEXT
    )
""")
conn.commit()
conn.close()

# ==================== 测试数据管理 ====================
with st.expander("🧹 测试数据管理", expanded=False):
    st.warning("⚠️ 此操作仅清空紧急暂停历史记录")
    if st.button("🗑️ 一键清除紧急暂停历史记录", type="secondary"):
        conn = sqlite3.connect("risk_control.db")
        conn.execute("DELETE FROM emergency_history")
        conn.commit()
        conn.close()
        st.success("✅ 已清除所有紧急暂停历史记录！")
        st.rerun()

st.markdown("---")

st.subheader("紧急暂停开关（一键停止全站）")

col1, col2 = st.columns(2)
with col1:
    if st.button("⛔ 立即启动紧急暂停", type="primary"):
        st.session_state.show_pause_dialog = True

with col2:
    if st.button("✅ 解除紧急暂停"):
        if st.session_state.get('emergency_stop', False):
            st.session_state.show_resume_dialog = True
        else:
            st.warning("当前并未处于暂停状态")

# 当前状态显示
if st.session_state.get('emergency_stop', False):
    st.error(f"🚨 **系统处于紧急暂停状态**！\n\n**原因**：{st.session_state.get('stop_reason', '')}\n**暂停时间**：{st.session_state.get('stop_time', '')}")
else:
    st.success("✅ 系统当前运行正常")

st.markdown("---")

# ==================== 紧急暂停历史记录 ====================
st.subheader("📜 紧急暂停历史记录（永久保存）")
conn = sqlite3.connect("risk_control.db")
history = conn.execute("""
    SELECT id, action, reason, time 
    FROM emergency_history 
    ORDER BY time DESC
""").fetchall()
conn.close()

for hid, action, reason, time in history:
    with st.container(border=True):
        icon = "🚨" if "启动" in action else "✅"
        st.write(f"{icon} **{action}** | **时间**: {time}")
        st.write(f"**原因**: {reason}")
        if st.button("📋 查看详细报告", key=f"hist_{hid}"):
            st.session_state.selected_history = (action, reason, time)
            st.session_state.show_history = True

# ==================== 弹窗 ====================
@st.dialog("启动紧急暂停")
def pause_dialog():
    reason = st.text_area("请输入暂停原因（必填）", "检测到重大安全事件")
    if st.button("确认启动", type="primary"):
        if reason.strip():
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            conn = sqlite3.connect("risk_control.db")
            conn.execute("INSERT INTO emergency_history (action, reason, time) VALUES (?, ?, ?)",
                        ("🚨 启动紧急暂停", reason.strip(), now))
            conn.commit()
            conn.close()
            
            st.session_state.emergency_stop = True
            st.session_state.stop_reason = reason.strip()
            st.session_state.stop_time = now
            st.rerun()

@st.dialog("解除紧急暂停")
def resume_dialog():
    reason = st.text_area("请输入解除原因（必填）", "风险已排除，系统恢复正常")
    if st.button("确认解除", type="primary"):
        if reason.strip():
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            conn = sqlite3.connect("risk_control.db")
            conn.execute("INSERT INTO emergency_history (action, reason, time) VALUES (?, ?, ?)",
                        ("✅ 解除紧急暂停", reason.strip(), now))
            conn.commit()
            conn.close()
            
            st.session_state.emergency_stop = False
            st.session_state.stop_reason = ""
            st.session_state.stop_time = ""
            st.rerun()

@st.dialog("操作详细报告")
def history_dialog():
    action, reason, time = st.session_state.selected_history
    st.write(f"**操作**: {action}")
    st.write(f"**时间**: {time}")
    st.write(f"**原因**: {reason}")
    if st.button("关闭"):
        st.rerun()

if st.session_state.get("show_pause_dialog", False):
    pause_dialog()
    st.session_state.show_pause_dialog = False

if st.session_state.get("show_resume_dialog", False):
    resume_dialog()
    st.session_state.show_resume_dialog = False

if st.session_state.get("show_history", False):
    history_dialog()
    st.session_state.show_history = False

st.info("👈 左侧选择不同模块进入对应功能区")