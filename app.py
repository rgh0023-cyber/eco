import streamlit as st
import pandas as pd
import io

# 设置页面布局
st.set_page_config(page_title="游戏经济诊断系统", layout="wide")
st.title("🎮 游戏经济系统定性分析流水账")

# --- 1. 映射表加载函数 ---
@st.cache_data
def load_mappings():
    """读取 config/ 下的 CSV，自动处理编码，返回 DataFrame"""
    def safe_read(file_path):
        try:
            return pd.read_csv(file_path, encoding='utf-8')
        except:
            return pd.read_csv(file_path, encoding='gbk')
    
    try:
        type_map = safe_read('config/resource_type_mapping.csv')
        id_map = safe_read('config/resource_id_mapping.csv')
        return type_map, id_map
    except:
        return None, None

# --- 2. 主程序 ---
def main():
    uploaded_file = st.file_uploader("请上传您的 SQL 流水账 (CSV)", type=["csv"])
    
    if uploaded_file is not None:
        # A. 读取流水账
        try:
            df = pd.read_csv(uploaded_file, encoding='utf-8')
        except:
            uploaded_file.seek(0)
            df = pd.read_csv(uploaded_file, encoding='gbk')
        
        # B. 自动识别匹配列
        type_col = next((c for c in df.columns if 'type' in c.lower()), None)
        id_col = next((c for c in df.columns if 'id' in c.lower()), None)
        
        st.write(f"🔍 已识别: 类型列=**{type_col}**, ID列=**{id_col}**")

        # C. 执行合并逻辑
        type_map, id_map = load_mappings()
        if type_map is not None and id_map is not None and type_col and id_col:
            # 关键修复：强制将映射表的第一列重命名为流水账对应的列名，确保 merge 不报错
            type_map.rename(columns={type_map.columns[0]: type_col}, inplace=True)
            id_map.rename(columns={id_map.columns[0]: id_col}, inplace=True)
            
            df[type_col] = df[type_col].astype(str)
            df[id_col] = df[id_col].astype(str)
            
            df = df.merge(type_map, on=type_col, how='left')
            df = df.merge(id_map, on=id_col, how='left')
            st.success("✅ 数据映射已完成")
        else:
            st.warning("⚠️ 映射表加载失败或列名识别异常，请检查 config/ 下的文件格式")

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
        st.info("💡 请上传 CSV 文件")

if __name__ == "__main__":
    main()
