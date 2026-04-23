import streamlit as st
import pandas as pd
import io

# 设置页面布局
st.set_page_config(page_title="游戏经济诊断系统", layout="wide")

st.title("🎮 游戏经济系统定性分析流水账")

# --- 1. 核心映射表加载函数 ---
@st.cache_data
def load_mappings():
    """读取并处理映射表，自动兼容 UTF-8 和 GBK"""
    def safe_read(file_path):
        try:
            return pd.read_csv(file_path, encoding='utf-8')
        except UnicodeDecodeError:
            return pd.read_csv(file_path, encoding='gbk')
    
    try:
        type_map = safe_read('config/resource_type_mapping.csv')
        id_map = safe_read('config/resource_id_mapping.csv')
        return type_map, id_map
    except Exception as e:
        return None, None

# --- 2. 主程序逻辑 ---
def main():
    uploaded_file = st.file_uploader("请上传您的 SQL 流水账 (CSV)", type=["csv"])
    
    if uploaded_file is not None:
        # A. 读取流水账
        try:
            df = pd.read_csv(uploaded_file, encoding='utf-8')
        except UnicodeDecodeError:
            uploaded_file.seek(0)
            df = pd.read_csv(uploaded_file, encoding='gbk')
        
        # B. 执行映射逻辑
        type_map, id_map = load_mappings()
        if type_map is not None and id_map is not None:
            # 确保关键列为字符串，防止 merge 失败
            df['resource_type'] = df['resource_type'].astype(str)
            df['resource_id'] = df['resource_id'].astype(str)
            
            # 进行左连接
            df = df.merge(type_map, on='resource_type', how='left')
            df = df.merge(id_map, on='resource_id', how='left')
            st.success("✅ 数据已加载并自动完成业务映射")
        else:
            st.warning("⚠️ 未找到或加载映射表 (config/), 数据将以原始 ID 显示")

        # C. 增加专家标注列
        if 'expert_label' not in df.columns:
            df['expert_label'] = ""

        # D. 交互式编辑器
        st.subheader("📝 专家定性标注")
        edited_df = st.data_editor(
            df, 
            column_config={
                "expert_label": st.column_config.SelectboxColumn(
                    "定性标签",
                    help="请为该行流水选择经济逻辑属性",
                    options=["正常循环", "外部注水", "硬核收缩", "策略性存量", "难度失效"],
                    required=False,
                )
            },
            num_rows="dynamic",
            use_container_width=True
        )

        # E. 导出标注结果
        csv_buffer = io.StringIO()
        edited_df.to_csv(csv_buffer, index=False)
        st.download_button(
            label="💾 下载标注后的流水账",
            data=csv_buffer.getvalue(),
            file_name="labeled_economy_data.csv",
            mime="text/csv"
        )
    else:
        st.info("💡 请上传数据文件以开始分析。")

if __name__ == "__main__":
    main()
