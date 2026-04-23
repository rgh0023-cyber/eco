import streamlit as st
import pandas as pd
import io

st.set_page_config(page_title="游戏经济诊断系统", layout="wide")

st.title("🎮 经济系统定性分析流水账")

# 1. 文件上传
uploaded_file = st.file_uploader("请上传您的 SQL 流水账 (CSV)", type=["csv"])

if uploaded_file:
    # 自动处理编码问题的读取逻辑
    try:
        df = pd.read_csv(uploaded_file, encoding='utf-8')
    except UnicodeDecodeError:
        uploaded_file.seek(0)
        df = pd.read_csv(uploaded_file, encoding='gbk')

    st.success(f"成功读取数据，共 {len(df)} 条记录")

    # 2. 交互式定性标注区
    st.subheader("📝 专家定性标注")
    st.markdown("请在下方为每一行或选定的行添加您的业务经验标注：")
    
    # 增加一列 'expert_label' 用于标注
    if 'expert_label' not in df.columns:
        df['expert_label'] = ""

    # 使用 data_editor 实现交互式编辑
    edited_df = st.data_editor(
        df, 
        column_config={
            "expert_label": st.column_config.SelectboxColumn(
                "定性标签",
                help="选择该行为的经济逻辑",
                options=["正常循环", "外部注水", "硬核收缩", "策略性存量", "难度失效"],
                required=False,
            )
        },
        num_rows="dynamic"
    )

    # 3. 数据导出
    st.subheader("💾 导出标注结果")
    csv_buffer = io.StringIO()
    edited_df.to_csv(csv_buffer, index=False)
    
    st.download_button(
        label="下载标注后的流水账",
        data=csv_buffer.getvalue(),
        file_name="labeled_economy_data.csv",
        mime="text/csv",
    )

    # 4. 可视化观察
    st.subheader("📊 经济动态预览")
    chart_data = edited_df[['event_time', 'user_coin_remain', 'current_level']].dropna()
    st.line_chart(chart_data.set_index('event_time')['user_coin_remain'])

else:
    st.info("💡 请上传您的 CSV 文件以开始定性标注流程。")
    st.markdown("""
    ### 使用说明：
    1. 上传您从数数导出的 CSV 文件。
    2. 在表格的 **'expert_label'** 列中，选择符合您经验的定性分类。
    3. 点击底部的 **'下载标注后的流水账'**，将结果发回给我，我将开始学习您的标注逻辑。
    """)
