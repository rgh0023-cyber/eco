import streamlit as st
import pandas as pd

st.set_page_config(page_title="经济系统诊断工具", layout="wide")

st.title("🎮 游戏经济系统定性分析流水账")

# 1. 数据上传组件
uploaded_file = st.file_uploader("上传您的 SQL 导出流水账 (CSV/Excel)", type=["csv", "xlsx"])

if uploaded_file:
    df = pd.read_csv(uploaded_file)
    
    # 2. 数据预览与筛选
    st.subheader("流水账预览")
    st.dataframe(df.head(10))
    
    # 3. 定性标注区 (后续我们会在这里加入您的标注交互)
    st.subheader("定性标注与诊断")
    # 这里将集成一个可编辑的 Dataframe 或输入框，方便您进行标注
    
    # 4. 可视化观察区
    st.subheader("经济趋势观察")
    # 这里将放置余额变化曲线与关卡事件的联动图表
    
else:
    st.info("请先上传数据以开始分析。")
