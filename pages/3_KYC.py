import streamlit as st
import sqlite3

st.title("🛡️ KYC 审核流程")
st.caption("待审核列表 + KYC审核记录（自动+人工混合审核模式）")

conn = sqlite3.connect("risk_control.db")
c = conn.cursor()

# 安全添加字段
try:
    c.execute("ALTER TABLE kyc_records ADD COLUMN review_type TEXT")
    c.execute("ALTER TABLE kyc_records ADD COLUMN reason TEXT")
except:
    pass

# ==================== 初始化指定演示数据 ====================
c.execute("DELETE FROM kyc_records")

demo_data = [
    # 待审核（2条）
    (1, 1234, '待审核', '人工', None),
    (2, 5678, '待审核', '人工', None),
    
    # 已通过（3条）
    (3, 3367, '通过', '自动通过', None),
    (4, 4877, '通过', '人工通过', '人工审核为低风险'),
    (5, 8743, '通过', '自动通过', None),
    
    # 已拒绝（3条）
    (6, 1234, '拒绝', '自动拒绝', 'IP地址可疑'),
    (7, 6646, '拒绝', '人工拒绝', '证件活体匹配不通过'),
    (8, 5678, '拒绝', '自动拒绝', '黑名单记录'),
]

c.executemany("""
    INSERT INTO kyc_records (id, user_id, status, review_type, reason, created_at)
    VALUES (?, ?, ?, ?, ?, datetime('now'))
""", demo_data)
conn.commit()

# ==================== 待审核列表 ====================
st.subheader("⏳ 待审核列表（高风险用户）")
pending = c.execute("SELECT id, user_id FROM kyc_records WHERE status = '待审核'").fetchall()

for pid, uid in pending:
    risk_score = 18 if uid == 1234 else 10
    with st.expander(f"👤 用户 ID: {uid} （自动风险分: **{risk_score}** 🔴 高风险）", expanded=False):
        st.write("**详细注册信息**")
        st.image("https://via.placeholder.com/300x180/FF0000/FFFFFF?text=证件照", caption="身份证/护照")
        st.write("✅ 人脸活体匹配: 通过")
        st.write(f"📍 设备: iPhone 15 Pro | IP: 香港 (高风险地区)")
        
        reason = st.text_input("审核原因（必填）", key=f"reason_{pid}")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("✅ 通过", key=f"pass_{pid}", type="primary"):
                c.execute("UPDATE kyc_records SET status='通过', review_type='人工通过', reason=? WHERE id=?", 
                         (reason or "人工审核通过", pid))
                conn.commit()
                st.success("已人工通过！")
                st.rerun()
        with col2:
            if st.button("❌ 拒绝", key=f"reject_{pid}"):
                c.execute("UPDATE kyc_records SET status='拒绝', review_type='人工拒绝', reason=? WHERE id=?", 
                         (reason or "人工审核拒绝", pid))
                conn.commit()
                st.error("已人工拒绝！")
                st.rerun()

# ==================== 已审核记录 ====================
st.subheader("📊 KYC 审核记录")
col_pass, col_reject = st.columns(2)

with col_pass:
    st.write("**✅ 已通过**")
    passed = c.execute("SELECT user_id, review_type, reason FROM kyc_records WHERE status = '通过'").fetchall()
    for u, rtype, r in passed:
        st.success(f"用户ID：{u} | {rtype} | {r or 'None'}")

with col_reject:
    st.write("**❌ 已拒绝**")
    rejected = c.execute("SELECT user_id, review_type, reason FROM kyc_records WHERE status = '拒绝'").fetchall()
    for u, rtype, r in rejected:
        st.error(f"用户ID：{u} | {rtype} | {r or 'None'}")

conn.close()