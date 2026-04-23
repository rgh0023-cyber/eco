import streamlit as st
import pandas as pd
import io

# 设置页面布局
st.set_page_config(page_title="游戏经济诊断系统", layout="wide")
st.title("🎮 游戏经济系统定性分析流水账")

# --- 1. 映射表加载函数 ---
@st.cache_data
def load_mappings():
    """读取映射表，使用 errors='replace' 防止编码报错"""
    def safe_read(file_path):
        # 尝试使用 utf-8 读取，如果失败则使用 gbk，并设置 errors='replace' 忽略无法解码的字符
        try:
            return pd.read_csv(file_path, sep='\t', encoding='utf-8', errors='replace')
        except:
            return pd.read_csv(file_path, sep='\t', encoding='gbk', errors='replace')
    
    try:
        type_map = safe_read('config/resource_type_mapping.csv')
        id_map = safe_read('config/resource_id_mapping.csv')
        
        # 强制将映射表第一列重命名为对应的键值，确保 merge 对齐
        type_map.rename(columns={type_map.columns[0]: 'get_type'}, inplace=True)
        id_map.rename(columns={id_map.columns[0]: 'resource_id'}, inplace=True)
        
        return type_map, id_map
    except Exception as e:
        st.error(f"映射表加载失败，请检查 config/ 文件夹及文件格式: {e}")
        return None, None

# --- 2. 主程序 ---
def main():
    uploaded_file = st.file_uploader("请上传您的 SQL 流水账 (CSV/TSV)", type=["csv", "txt"])
    
    if uploaded_file is not None:
        # A. 读取流水账 (使用 errors='replace' 确保容错)
        try:
            df = pd.read_csv(uploaded_file, sep='\t', encoding='utf-8', errors='replace')
        except:
            uploaded_file.seek(0)
            df = pd.read_csv(uploaded_file, sep='\t', encoding='gbk', errors='replace')
        
        # B. 精确指定列名
        type_col = 'get_type'
        id_col = 'resource_id'
        
        if type_col not in df.columns or id_col not in df.columns:
            st.error(f"❌ 错误：CSV 中缺少必要的列！期望: {type_col}, {id_col}。现有: {df.columns.tolist()}")
            return

        # C. 执行映射合并
        type_map, id_map = load_mappings()
        if type_map is not None and id_map is not None:
            df[type_col] = df[type_col].astype(str)
            df[id_col] = df[id_col].astype(str)
            
            # 使用 left merge
            df = df.merge(type_map, on=type_col, how='left')
            df = df.merge(id_map, on=id_col, how='left')
            st.success("✅ 数据映射已完成，业务描述已合并")
        
        # D. 专家标注
        if 'expert_label' not in df.columns:
            df['expert_label'] = ""

        st.subheader("📝 专家定性标注")
        edited_df = st.data_editor(
            df, 
            column_config={
                "expert_label": st.column_config.SelectboxColumn(
                    "定性标签",
                    options=["正常循环", "外部注水", "硬核收缩", "策略性存量", "难度失效"],
                    required=False,
                )
            },
            num_rows="dynamic",
            use_container_width=True
        )

        # E. 导出
        csv_buffer = io.StringIO()
        edited_df.to_csv(csv_buffer, index=False)
        st.download_button("💾 下载标注结果", csv_buffer.getvalue(), "labeled_data.csv", "text/csv")
    else:
        st.info("💡 请上传 CSV/TSV 文件")

if __name__ == "__main__":
    main()
