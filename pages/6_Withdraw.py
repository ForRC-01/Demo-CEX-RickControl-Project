import streamlit as st
import sqlite3
from datetime import datetime

st.set_page_config(page_title="提现风控", layout="wide")
st.title("💰 提现风控模块")
st.caption("提现限额分层 + 黑名单管理 + 多重审核流程")

conn = sqlite3.connect("risk_control.db")
c = conn.cursor()

# ==================== 测试数据管理 ====================
with st.expander("🧹 测试数据管理", expanded=False):
    st.warning("⚠️ 此操作仅清空提现记录")
    if st.button("🗑️ 一键清除所有提现测试数据", type="secondary"):
        c.execute("DELETE FROM withdrawals")
        conn.commit()
        st.success("✅ 已清除所有提现测试数据！")
        st.rerun()

st.markdown("---")

# ==================== 4.1 提现限额分层规则 ====================
st.subheader("📏 提现限额分层规则")

limit_data = {
    0: {"name": "未认证（游客）", "base": 0},
    1: {"name": "KYC 1 - 手机/邮箱认证", "base": 100},
    2: {"name": "KYC 2 - 身份证+人脸认证", "base": 5000},
    3: {"name": "KYC 3 - 机构/高级认证", "base": 20000}
}

col1, col2 = st.columns(2)
with col1:
    kyc_level = st.selectbox("KYC 等级", [0,1,2,3], 
                            format_func=lambda x: f"KYC {x} - {limit_data[x]['name']}")
with col2:
    risk_level = st.selectbox("风险等级", ["低风险", "中风险", "高风险"])

base_limit = limit_data[kyc_level]["base"]
risk_factor = {"低风险":1.0, "中风险":0.7, "高风险":0.3}[risk_level]
final_limit = int(base_limit * risk_factor)

if final_limit == 0:
    st.error("❌ 未认证用户禁止提现")
else:
    st.success(f"**最终每日提现限额：{final_limit:,} USDT**")
    st.caption(f"计算过程：基础限额 {base_limit:,} USDT × {risk_level}系数 {risk_factor} = {final_limit:,} USDT")

st.markdown("---")

# ==================== 4.2 黑名单管理 ====================
st.subheader("⛔ 地址黑名单管理")
blacklist_text = st.text_area("黑名单地址（每行一个）", 
                             value="0xdeadbeef1234567890abcdef\n0xblacklist111222333", 
                             height=100)

if st.button("💾 保存黑名单"):
    st.success("✅ 黑名单已更新")

st.markdown("---")

# ==================== 模拟提现申请 ====================
st.subheader("🧾 模拟提现申请")
with st.form("withdraw_form"):
    user_id = st.number_input("提现用户 ID", min_value=1000, value=1900)
    amount = st.number_input("提现金额 (USDT)", min_value=5.0, value=15000.0, step=100.0)
    address = st.text_input("提现地址", value="0x1234567890abcdef1234567890abcdef12345678")
    
    submitted = st.form_submit_button("提交提现申请", type="primary")

    if submitted:
        blacklist_list = [line.strip() for line in blacklist_text.splitlines() if line.strip()]

        if final_limit == 0:
            st.error("❌ 未认证用户禁止提现！")
        elif amount > final_limit:
            st.error(f"❌ 超出当日限额！当前限额 {final_limit:,} USDT")
        else:
            is_blacklisted = address.strip() in blacklist_list
            if is_blacklisted:
                status = "已拦截 - 命中黑名单"
            elif risk_level == "低风险":
                status = "已通过"   # 低风险 + 非黑名单 自动通过
            else:
                status = "待初审"
            
            c.execute("""
                INSERT INTO withdrawals (user_id, amount, address, status, kyc_level, risk_level, created_at) 
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (user_id, amount, address, status, kyc_level, risk_level, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
            conn.commit()
            
            if is_blacklisted:
                st.error("❌ 地址命中黑名单！已自动拦截")
            elif status == "已通过":
                st.success(f"✅ 低风险用户，提现申请自动通过！（{amount:,.0f} USDT）")
            else:
                st.success(f"✅ 提现申请已提交（{amount:,.0f} USDT）")
                st.info("→ 已进入多重审核流程")

st.markdown("---")

# ==================== 待审核提现记录 ====================
st.subheader("🔍 提现记录（多重审核）")
records = c.execute("""
    SELECT id, user_id, amount, address, status, kyc_level, risk_level, created_at 
    FROM withdrawals 
    ORDER BY created_at DESC
""").fetchall()

for rid, uid, amt, addr, status, kyc, risk, t in records:
    with st.container(border=True):
        col_a, col_b = st.columns([6, 3])
        with col_a:
            st.write(f"**用户ID**: {uid} | **金额**: {amt:,.0f} USDT | **KYC**: {kyc} | **风险**: {risk}")
            st.write(f"**地址**: `{addr}` | **时间**: {t}")
        with col_b:
            st.write(f"**状态**: **{status}**")
            
            if status == "待初审" or "拦截" in status:
                if st.button("✅ 初审通过", key=f"first_{rid}"):
                    c.execute("UPDATE withdrawals SET status='待复审' WHERE id=?", (rid,))
                    conn.commit()
                    st.rerun()
                if st.button("❌ 初审拒绝", key=f"reject1_{rid}"):
                    c.execute("UPDATE withdrawals SET status='已拒绝' WHERE id=?", (rid,))
                    conn.commit()
                    st.rerun()
            elif status == "待复审":
                if st.button("✅ 复审通过", key=f"final_{rid}"):
                    c.execute("UPDATE withdrawals SET status='已通过' WHERE id=?", (rid,))
                    conn.commit()
                    st.rerun()
                if st.button("❌ 复审拒绝", key=f"reject2_{rid}"):
                    c.execute("UPDATE withdrawals SET status='已拒绝' WHERE id=?", (rid,))
                    conn.commit()
                    st.rerun()

conn.close()