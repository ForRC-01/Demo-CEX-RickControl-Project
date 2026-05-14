import streamlit as st
import sqlite3
from datetime import datetime

st.set_page_config(page_title="提现风控", layout="wide")
st.title("💰 提现风控模块")
st.caption("提现限额分层 + 黑名单审核 | 对应报告 4.1 ~ 4.4")

conn = sqlite3.connect("risk_control.db")
c = conn.cursor()

# ==================== 测试数据管理 ====================
with st.expander("🧹 测试数据管理", expanded=False):
    st.warning("⚠️ 此操作仅清空提现记录，不会影响其他模块")
    if st.button("🗑️ 一键清除所有提现测试数据", type="secondary"):
        c.execute("DELETE FROM withdrawals")
        conn.commit()
        st.success("✅ 已清除所有提现测试数据！")
        st.rerun()

st.markdown("---")

# ==================== 4.1 提现限额分层规则 ====================
st.subheader("📏 提现限额分层规则（KYC 3 层）")

limit_data = {
    0: {"name": "未认证（游客）", "base": 0},
    1: {"name": "KYC 1 - 手机/邮箱认证", "base": 10000},
    2: {"name": "KYC 2 - 身份证+人脸认证", "base": 50000},
    3: {"name": "KYC 3 - 机构/高级认证", "base": 200000}
}

col1, col2 = st.columns(2)
with col1:
    kyc_level = st.selectbox(
        "KYC 等级", 
        [0, 1, 2, 3], 
        format_func=lambda x: f"KYC {x} - {limit_data[x]['name']}"
    )

with col2:
    risk_level = st.selectbox("风险等级", ["低风险", "中风险", "高风险"])

base_limit = limit_data[kyc_level]["base"]
risk_factor = {"低风险": 1.0, "中风险": 0.7, "高风险": 0.3}[risk_level]
final_limit = int(base_limit * risk_factor)

if final_limit == 0:
    st.error("❌ 未认证用户（KYC 0）禁止提现")
else:
    st.success(f"**最终每日提现限额：{final_limit:,} USDT**")
    st.caption(f"计算过程：基础限额 {base_limit:,} USDT × 风险系数 {risk_factor} = {final_limit:,} USDT")

st.markdown("---")

# ==================== 4.2 黑名单管理 ====================
st.subheader("⛔ 地址黑名单管理")
blacklist_input = st.text_area("黑名单地址（每行一个）", 
                              value="0xdeadbeef1234567890abcdef\n0xblacklist111222333\n0x suspicious888999", 
                              height=100)

if st.button("💾 保存黑名单"):
    st.success("✅ 黑名单已更新")

st.markdown("---")

# ==================== 模拟提现申请 + 黑名单拦截 ====================
st.subheader("🧾 模拟提现申请")

with st.form("withdraw_form"):
    user_id = st.number_input("提现用户 ID", min_value=1000, value=1900)
    amount = st.number_input("提现金额 (USDT)", min_value=5.0, value=15000.0, step=100.0)
    address = st.text_input("提现地址", value="0x1234567890abcdef1234567890abcdef12345678")
    
    submitted = st.form_submit_button("提交提现申请", type="primary")

    if submitted:
        if final_limit == 0:
            st.error("❌ 未认证用户禁止提现！请先完成 KYC 认证。")
        elif amount > final_limit:
            st.error(f"❌ 超出当日限额！当前限额 {final_limit:,} USDT")
        elif address.strip() in blacklist_input:
            st.error("❌ 提现地址命中黑名单！已自动拦截")
        else:
            st.success(f"✅ 提现申请已提交（{amount:,.0f} USDT）")
            st.info("→ 已进入多重审核流程（4.3 将进一步实现）")

st.info("👈 左侧选择不同模块进入对应功能区")
conn.close()