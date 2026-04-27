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
        type_map, id_map = load_mappings()
        
        if type_map is not None and id_map is not None:
            # 清洗并合并
            df[type_col] = df[type_col].astype(str).str.strip()
            df[id_col] = df[id_col].astype(str).str.strip()
            
            # 为了明确区分映射表的 description，我们在合并前重命名
            type_map_renamed = type_map.rename(columns={'description': 'type_desc'})
            id_map_renamed = id_map.rename(columns={'description': 'res_desc'})
            
            df = df.merge(type_map_renamed, on=type_col, how='left')
            df = df.merge(id_map_renamed, on=id_col, how='left')
            
            # 【核心逻辑】：构建结构化业务叙述
            # 格式：通过 [category] 的 [type_desc] 来获取 [res_desc]
            mask = df['event_name'] == 'resource_get'
            df.loc[mask, 'tag'] = (
                "通过 " + df['category'].fillna('未知类别') + 
                " 的 " + df['type_desc'].fillna('未知类型') + 
                " 来获取 " + df['res_desc'].fillna('未知资源')
            )
            
            st.success("✅ 业务叙述已生成")
        
        # 专家标注区
        st.subheader("📝 专家定性标注")
        edited_df = st.data_editor(df, num_rows="dynamic", use_container_width=True)
        
        # 导出
        csv_buffer = io.StringIO()
        edited_df.to_csv(csv_buffer, index=False)
        st.download_button("💾 下载标注结果", csv_buffer.getvalue(), "labeled_data.csv", "text/csv")
    else:
        st.info("💡 请上传数据文件")

if __name__ == "__main__":
    main()
