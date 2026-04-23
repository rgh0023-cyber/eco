import streamlit as st
import pandas as pd
import io

st.set_page_config(page_title="游戏经济诊断系统", layout="wide")

st.title("🎮 游戏经济系统定性分析流水账")

# 1. 映射表加载函数
@st.cache_data
def load_mappings():
    try:
        # 从 GitHub 仓库读取您的配置表
        # 请确保路径和文件名与您在 config/ 下的一致
        type_map = pd.read_csv('config/resource_type_mapping.csv')
        id_map = pd.read_csv('config/resource_id_mapping.csv')
        return type_map, id_map
    except Exception as e:
        st.warning(f"映射表加载失败，请检查 config/ 路径: {e}")
        return None, None

# 2. 文件上传与数据预处理
uploaded_file = st.file_uploader("请上传您的 SQL 流水账 (CSV)", type=["csv"])

if uploaded_file:
    # 编码兼容处理
    try:
        df = pd.read_csv(uploaded_file, encoding='utf-8')
    except UnicodeDecodeError:
        uploaded_file.seek(0)
        df = pd.read_csv(uploaded_file, encoding='gbk')

    # 数据映射逻辑
    type_map, id_map = load_mappings()
    if type_map is not None and id_map is not None:
        # 确保类型一致性以便合并
        df['resource_type'] = df['resource_type'].astype(str)
        df['resource_id'] = df['resource_id'].astype(str)
        
        # 执行左连接映射
        df = df.merge(type_map, on='resource_type', how='left')
        df = df.merge(id_map, on='resource_id', how='left')

    st.success(f"数据加载完成，共 {len(df)} 条记录")

    # 3. 交互式定性标注区
    st.subheader("📝 专家定性标注")
    if 'expert_label' not in df.columns:
        df['expert_label'] = ""

    # 使用 data_editor 进行标注
    edited_df = st.data_editor(
        df, 
        column_config={
            "expert_label": st.column_config.SelectboxColumn(
                "定性标签",
                options=["正常循环", "外部注水", "硬核收缩", "策略性存量", "难度失效"],
                required=False,
            )
        },
        num_rows="dynamic"
    )

    # 4. 导出结果
    csv_buffer = io.StringIO()
    edited_df.to_csv(csv_buffer, index=False)
    st.download_button("下载标注后的流水账", csv_buffer.getvalue(), "labeled_economy_data.csv", "text/csv")

else:
    st.info("💡 请上传 CSV 文件开始标注。")
    st.markdown("""
    ### 映射说明：
    系统已自动加载 `config/` 下的映射表，流水账中的 `resource_id` 和 `resource_type` 将自动转化为业务定义。
    """)
