import streamlit as st
import pandas as pd
import io
import chardet

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
    df = pd.read_csv(file_buffer, sep=sep, encoding=encoding)
    # 清理所有列名的前后空格
    df.columns = df.columns.str.strip()
    return df

# --- 映射表加载 ---
@st.cache_data
def load_mappings():
    try:
        # 这里同样使用自动检测读取
        type_map = pd.read_csv('config/resource_type_mapping.csv', sep=None, engine='python')
        id_map = pd.read_csv('config/resource_id_mapping.csv', sep=None, engine='python')
        # 统一清理映射表的列名
        type_map.columns = type_map.columns.str.strip()
        id_map.columns = id_map.columns.str.strip()
        # 强制将第一列重命名为标准 KEY
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
        
        # 【关键改动】：自动从现有的列中匹配最接近的列名
        all_cols = df.columns.tolist()
        type_col = next((c for c in all_cols if 'get_type' in c.lower()), None)
        id_col = next((c for c in all_cols if 'resource_id' in c.lower()), None)
        
        if not type_col or not id_col:
            st.error(f"❌ 错误：在 CSV 中找不到 get_type 或 resource_id。现有列: {all_cols}")
            return

        type_map, id_map = load_mappings()
        if type_map is not None and id_map is not None:
            # 清洗键值并进行合并
            df[type_col] = df[type_col].astype(str).str.strip()
            df[id_col] = df[id_col].astype(str).str.strip()
            type_map['get_type'] = type_map['get_type'].astype(str).str.strip()
            id_map['resource_id'] = id_map['resource_id'].astype(str).str.strip()
            
            df = df.merge(type_map, left_on=type_col, right_on='get_type', how='left')
            df = df.merge(id_map, left_on=id_col, right_on='resource_id', how='left')
            
            # 【逻辑】：构建结构化业务叙述
            mask = df['event_name'] == 'resource_get'
            df.loc[mask, 'tag'] = (
                "通过 " + df['category'].fillna('未知类别') + 
                " 的 " + df['description_x'].fillna('未知类型') + 
                " 来获取 " + df['description_y'].fillna('未知资源')
            )
            
            st.success("✅ 数据映射及叙述生成成功")
        
        # 标注与导出
        edited_df = st.data_editor(df, num_rows="dynamic", use_container_width=True)
        csv_buffer = io.StringIO()
        edited_df.to_csv(csv_buffer, index=False)
        st.download_button("💾 下载结果", csv_buffer.getvalue(), "labeled_data.csv", "text/csv")

if __name__ == "__main__":
    main()
