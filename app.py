import streamlit as st
import pandas as pd
import io
import chardet  # 新增库用于自动检测编码

# 设置页面布局
st.set_page_config(page_title="游戏经济诊断系统", layout="wide")
st.title("🎮 游戏经济系统定性分析流水账")

# --- 1. 自动检测编码函数 ---
def detect_encoding(file_buffer):
    """自动检测上传文件的编码格式"""
    raw_data = file_buffer.read(10000) # 读取部分数据来检测
    file_buffer.seek(0) # 重置指针
    result = chardet.detect(raw_data)
    return result['encoding']

# --- 2. 映射表加载函数 ---
@st.cache_data
def load_mappings():
    """自动检测映射表编码并读取"""
    def read_csv_auto(file_path):
        with open(file_path, 'rb') as f:
            encoding = chardet.detect(f.read())['encoding']
        return pd.read_csv(file_path, encoding=encoding)
    
    try:
        type_map = read_csv_auto('config/resource_type_mapping.csv')
        id_map = read_csv_auto('config/resource_id_mapping.csv')
        type_map.rename(columns={type_map.columns[0]: 'get_type'}, inplace=True)
        id_map.rename(columns={id_map.columns[0]: 'resource_id'}, inplace=True)
        return type_map, id_map
    except Exception as e:
        st.error(f"映射表加载失败: {e}")
        return None, None

# --- 3. 主程序 ---
def main():
    uploaded_file = st.file_uploader("请上传您的 SQL 流水账 (CSV)", type=["csv"])
    
    if uploaded_file is not None:
        # A. 自动检测上传文件的编码
        encoding = detect_encoding(uploaded_file)
        st.write(f"🔍 检测到上传文件编码为: {encoding}")
        
        try:
            df = pd.read_csv(uploaded_file, encoding=encoding)
        except Exception as e:
            st.error(f"读取文件失败: {e}")
            return
        
        type_col, id_col = 'get_type', 'resource_id'
        
        if type_col not in df.columns or id_col not in df.columns:
            st.error(f"❌ 错误：CSV 缺少必要的列。现有列: {df.columns.tolist()}")
            return

        # B. 合并映射
        type_map, id_map = load_mappings()
        if type_map is not None and id_map is not None:
            df[type_col] = df[type_col].astype(str)
            df[id_col] = df[id_col].astype(str)
            df = df.merge(type_map, on=type_col, how='left')
            df = df.merge(id_map, on=id_col, how='left')
            st.success("✅ 数据映射已完成")
        
        # C. 标注与导出
        if 'expert_label' not in df.columns:
            df['expert_label'] = ""
        edited_df = st.data_editor(df, num_rows="dynamic", use_container_width=True)
        
        csv_buffer = io.StringIO()
        edited_df.to_csv(csv_buffer, index=False)
        st.download_button("💾 下载标注结果", csv_buffer.getvalue(), "labeled_data.csv", "text/csv")
    else:
        st.info("💡 请上传标准 CSV 流水账文件以开始分析。")

if __name__ == "__main__":
    main()
