import streamlit as st
import sqlite3
import random

st.title("👤 用户管理")
st.caption("用户注册与信息管理")

conn = sqlite3.connect("risk_control.db")
c = conn.cursor()

# 清空数据
if st.button("🗑️ 清空所有用户数据（测试用）"):
    c.execute("DELETE FROM users")
    conn.commit()
    st.success("✅ 数据已清空！")
    st.rerun()

# ==================== 成功提示区 ====================
if "register_success" in st.session_state:
    st.success(st.session_state.register_success)
    del st.session_state.register_success

# ==================== 新用户注册 ====================
st.subheader("📝 新用户注册")

# 人脸扫描（必须先完成）
if "face_verify_state" not in st.session_state:
    st.session_state.face_verify_state = False

if st.button("🪪 人脸扫描模拟"):
    st.session_state.face_verify_state = not st.session_state.face_verify_state
    if st.session_state.face_verify_state:
        st.success("✅ 人脸扫描完成！")
    else:
        st.error("❌ 人脸扫描失败！")

with st.form("user_register", clear_on_submit=True):
    account = st.text_input("账号（邮箱/手机号）")
    username = st.text_input("👤 用户名")
    password = st.text_input("🔑 密码", type="password")
    
    st.write("**身份验证**")
    id_card = st.file_uploader("📄 上传证件照", type=["jpg", "png", "jpeg"])
    
    submitted = st.form_submit_button("🚀 注册")

# 注册逻辑（加强校验）
if submitted:
    if not account:
        st.error("❌ 账号（邮箱/手机号）不能为空")
    elif not username:
        st.error("❌ 用户名不能为空")
    elif not password:
        st.error("❌ 密码不能为空")
    elif not st.session_state.face_verify_state:
        st.error("❌ 请先完成人脸扫描验证！")
    else:
        try:
            new_id = random.randint(1000, 9999)
            
            if c.execute("SELECT 1 FROM users WHERE username = ?", (username,)).fetchone():
                st.error("❌ 用户名已存在，请更换用户名")
            elif c.execute("SELECT 1 FROM users WHERE email = ? OR phone = ?", (account, account)).fetchone():
                st.error("❌ 该账号（邮箱/手机号）已存在，请使用其他账号")
            else:
                c.execute("""
                    INSERT INTO users (id, username, email, phone, created_at)
                    VALUES (?, ?, ?, ?, datetime('now'))
                """, (new_id, username, account, account))
                
                conn.commit()
                
                st.session_state.register_success = f"""
                    ✅ **注册成功！请等待 KYC 通过！**

                    用户ID: **{new_id}**  
                    用户名: **{username}**  
                    账号: **{account}**
                """
                # 注册成功后重置人脸验证状态
                st.session_state.face_verify_state = False
                st.rerun()
                
        except Exception as e:
            st.error(f"❌ 注册失败: {str(e)}")

# ==================== 现有用户 ====================
st.subheader("📋 现有用户")
users = c.execute("SELECT id, username, email, created_at FROM users ORDER BY id DESC").fetchall()

for uid, uname, acc, reg_time in users:
    with st.container(border=True):
        st.write(f"**用户ID**: `{uid}` | **用户名**: `{uname}` | **账号**: `{acc}`")
        st.caption(f"注册时间: {reg_time}")

conn.close()