import streamlit as st
import pandas as pd
import io
import chardet

# 设置页面布局
st.set_page_config(page_title="游戏经济诊断系统", layout="wide")
st.title("🎮 游戏经济系统定性分析流水账")

# --- 自动检测编码与分隔符 ---
def read_csv_smart(file_buffer):
    raw_data = file_buffer.read(10000)
    file_buffer.seek(0)
    encoding = chardet.detect(raw_data)['encoding']
    text_sample = file_buffer.read(1000).decode(encoding, errors='replace')
    file_buffer.seek(0)
    sep = '\t' if '\t' in text_sample.split('\n')[0] else ','
    return pd.read_csv(file_buffer, sep=sep, encoding=encoding)

# --- 映射表加载 ---
@st.cache_data
def load_mappings():
    try:
        # 使用 engine='python' 配合 sep=None 让 pandas 自动探测分隔符
        type_map = pd.read_csv('config/resource_type_mapping.csv', sep=None, engine='python')
        id_map = pd.read_csv('config/resource_id_mapping.csv', sep=None, engine='python')
        type_map.rename(columns={type_map.columns[0]: 'get_type'}, inplace=True)
        id_map.rename(columns={id_map.columns[0]: 'resource_id'}, inplace=True)
        return type_map, id_map
    except Exception as e:
        st.error(f"映射表加载错误: {e}")
        return None, None

# --- 主程序 ---
def main():
    uploaded_file = st.file_uploader("请上传您的 SQL 流水账 (CSV/TSV)", type=["csv", "txt"])
    
    if uploaded_file is not None:
        try:
            df = read_csv_smart(uploaded_file)
        except Exception as e:
            st.error(f"读取文件失败: {e}")
            return
        
        type_col, id_col = 'get_type', 'resource_id'
        
        if type_col not in df.columns or id_col not in df.columns:
            st.error(f"❌ 错误：找不到必要的列 {type_col} 或 {id_col}")
            return

        type_map, id_map = load_mappings()
        if type_map is not None and id_map is not None:
            # 【关键修复】确保 merge 双方的列都是字符串，防止类型不匹配的 ValueError
            df[type_col] = df[type_col].astype(str).str.strip()
            df[id_col] = df[id_col].astype(str).str.strip()
            type_map['get_type'] = type_map['get_type'].astype(str).str.strip()
            id_map['resource_id'] = id_map['resource_id'].astype(str).str.strip()
            
            # 执行合并
            df = df.merge(type_map, on=type_col, how='left')
            df = df.merge(id_map, on=id_col, how='left')
            st.success("✅ 数据映射成功！")
        
        if 'expert_label' not in df.columns:
            df['expert_label'] = ""
        edited_df = st.data_editor(df, num_rows="dynamic", use_container_width=True)
        
        csv_buffer = io.StringIO()
        edited_df.to_csv(csv_buffer, index=False)
        st.download_button("💾 下载标注结果", csv_buffer.getvalue(), "labeled_data.csv", "text/csv")
    else:
        st.info("💡 请上传文件")

if __name__ == "__main__":
    main()
