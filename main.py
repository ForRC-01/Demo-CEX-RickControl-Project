import streamlit as st
from datetime import datetime

st.set_page_config(page_title="CEX 风险控制仪表盘", layout="wide")
st.title("🔥 CEX 风险控制仪表盘")
st.caption(f"基于 SlowMist 安全实践要求 | 当前时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

st.success("✅ 项目框架初始化成功！")

col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("总资产 (USDT)", "248,392", "+2.4%")
with col2:
    st.metric("风险总分", "23", "-4")
with col3:
    st.metric("今日告警", "7", "🔴")
with col4:
    st.metric("提币通过率", "96.8%", "+0.8%")

st.markdown("---")
st.info("👈 左侧选择不同模块进入对应功能区")

st.subheader("近期风险趋势")
st.caption("（后续接入真实数据后这里会显示图表）")