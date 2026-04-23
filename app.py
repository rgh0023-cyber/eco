import streamlit as st
import pandas as pd
import io

# 设置页面布局
st.set_page_config(page_title="游戏经济诊断系统", layout="wide")
st.title("🎮 游戏经济系统定性分析流水账")

# --- 1. 映射表加载函数 ---
@st.cache_data
def load_mappings():
    """读取标准 UTF-8 逗号分隔的 CSV 映射表"""
    try:
        # 此时文件已规范化，直接读取即可
        type_map = pd.read_csv('config/resource_type_mapping.csv')
        id_map = pd.read_csv('config/resource_id_mapping.csv')
        
        # 强制重命名映射表的第一列作为主键，确保 merge 一致性
        type_map.rename(columns={type_map.columns[0]: 'get_type'}, inplace=True)
        id_map.rename(columns={id_map.columns[0]: 'resource_id'}, inplace=True)
        
        return type_map, id_map
    except Exception as e:
        st.error(f"映射表加载失败: {e}")
        return None, None

# --- 2. 主程序 ---
def main():
    uploaded_file = st.file_uploader("请上传您的 SQL 流水账 (CSV)", type=["csv"])
    
    if uploaded_file is not None:
        # 读取上传的 CSV
        try:
            df = pd.read_csv(uploaded_file)
        except Exception as e:
            st.error(f"读取文件失败: {e}")
            return
        
        # 验证必要列是否存在
        type_col = 'get_type'
        id_col = 'resource_id'
        
        if type_col not in df.columns or id_col not in df.columns:
            st.error(f"❌ 错误：CSV 缺少必要的列。现有列: {df.columns.tolist()}")
            return

        # 执行映射合并
        type_map, id_map = load_mappings()
        if type_map is not None and id_map is not None:
            # 确保连接键为字符串类型，防止匹配失败
            df[type_col] = df[type_col].astype(str)
            df[id_col] = df[id_col].astype(str)
            
            # 使用 left merge 合并映射信息
            df = df.merge(type_map, on=type_col, how='left')
            df = df.merge(id_map, on=id_col, how='left')
            st.success("✅ 数据映射已完成，业务描述已合并")
        
        # 专家标注区
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

        # 导出标注结果
        csv_buffer = io.StringIO()
        edited_df.to_csv(csv_buffer, index=False)
        st.download_button(
            label="💾 下载标注结果", 
            data=csv_buffer.getvalue(), 
            file_name="labeled_economy_data.csv", 
            mime="text/csv"
        )
    else:
        st.info("💡 请上传标准 CSV 流水账文件以开始分析。")

if __name__ == "__main__":
    main()
