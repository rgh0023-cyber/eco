import streamlit as st
import pandas as pd
import io

st.set_page_config(page_title="游戏经济诊断系统", layout="wide")
st.title("🎮 游戏经济系统定性分析流水账")

# --- 1. 映射表加载 ---
@st.cache_data
def load_mappings():
    def safe_read(file_path):
        try:
            return pd.read_csv(file_path, encoding='utf-8')
        except:
            return pd.read_csv(file_path, encoding='gbk')
    try:
        return safe_read('config/resource_type_mapping.csv'), safe_read('config/resource_id_mapping.csv')
    except:
        return None, None

# --- 2. 主程序 ---
def main():
    uploaded_file = st.file_uploader("请上传您的 CSV 流水账", type=["csv"])
    if uploaded_file:
        try:
            df = pd.read_csv(uploaded_file, encoding='utf-8')
        except:
            uploaded_file.seek(0)
            df = pd.read_csv(uploaded_file, encoding='gbk')

        # [关键改动] 自动匹配逻辑
        # 这里列出您CSV中实际的列名，程序会自动找匹配项
        type_col = next((c for c in df.columns if 'type' in c.lower()), None)
        id_col = next((c for c in df.columns if 'id' in c.lower()), None)
        
        st.write(f"🔍 自动识别列名 -> 类型列: **{type_col}**, ID列: **{id_col}**")

        if type_col and id_col:
            type_map, id_map = load_mappings()
            if type_map is not None and id_map is not None:
                # 转换并合并
                df[type_col] = df[type_col].astype(str)
                df[id_col] = df[id_col].astype(str)
                # 假设映射表里也有对应的列，此处做合并
                df = df.merge(type_map, on=type_col, how='left')
                df = df.merge(id_map, on=id_col, how='left')
                st.success("✅ 映射成功")
        
        # 标注与导出
        if 'expert_label' not in df.columns:
            df['expert_label'] = ""
        
        edited_df = st.data_editor(df, num_rows="dynamic", use_container_width=True)
        
        csv_buffer = io.StringIO()
        edited_df.to_csv(csv_buffer, index=False)
        st.download_button("💾 下载标注结果", csv_buffer.getvalue(), "labeled_data.csv")
    else:
        st.info("💡 请上传文件")

if __name__ == "__main__":
    main()
