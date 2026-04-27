import streamlit as st
import pandas as pd
import io
import chardet

st.set_page_config(page_title="游戏经济诊断系统", layout="wide")
st.title("🎮 游戏经济系统定性分析流水账 (编组清洗版)")

# --- 1. 基础工具函数 ---
def read_csv_smart(file_buffer):
    raw_data = file_buffer.read(10000)
    file_buffer.seek(0)
    encoding = chardet.detect(raw_data)['encoding']
    text_sample = file_buffer.read(1000).decode(encoding, errors='replace')
    file_buffer.seek(0)
    sep = '\t' if '\t' in text_sample.split('\n')[0] else ','
    df = pd.read_csv(file_buffer, sep=sep, encoding=encoding)
    df.columns = df.columns.str.strip()
    return df

def clean_id(val):
    try:
        return str(int(float(val)))
    except:
        return str(val).strip()

# --- 2. 编组清洗核心逻辑 ---
def validate_lifecycle(df):
    """
    原则：同一 account_id + current_level + challenge_times 必须同时包含 start 和 end
    """
    # 定义闭环的关键动作
    starts = df['event_name'] == 'level_start'
    ends = df['event_name'] == 'level_end'
    
    # 按编组分组统计是否有 start 和 end
    group_cols = ['account_id', 'current_level', 'challenge_times']
    
    # 找出包含 start 的组和包含 end 的组
    has_start = df[starts].groupby(group_cols).size().index
    has_end = df[ends].groupby(group_cols).size().index
    
    # 逻辑：必须同时存在 (Intersection)
    valid_groups = has_start.intersection(has_end)
    
    # 创建有效标记列 (默认为作废)
    df['is_valid'] = False
    
    # 将符合条件的编组标记为有效
    # 使用 MultiIndex 进行快速匹配
    df_idx = pd.MultiIndex.from_frame(df[group_cols])
    df.loc[df_idx.isin(valid_groups), 'is_valid'] = True
    
    # 对作废的数据打上标记
    df.loc[~df['is_valid'], 'tag'] = "[作废] 进出关记录不闭环"
    
    return df

# --- 3. 映射逻辑 ---
@st.cache_data
def load_mappings():
    # (保持原有映射逻辑不变)
    type_map = pd.read_csv('config/resource_type_mapping.csv', sep=None, engine='python')
    id_map = pd.read_csv('config/resource_id_mapping.csv', sep=None, engine='python')
    type_map.columns = type_map.columns.str.strip()
    id_map.columns = id_map.columns.str.strip()
    type_map.rename(columns={type_map.columns[0]: 'resource_type'}, inplace=True)
    id_map.rename(columns={id_map.columns[0]: 'resource_id'}, inplace=True)
    return type_map, id_map

def main():
    uploaded_file = st.file_uploader("请上传 SQL 流水账", type=["csv", "txt"])
    
    if uploaded_file is not None:
        df = read_csv_smart(uploaded_file)
        
        # 【执行清洗】
        df = validate_lifecycle(df)
        
        # 【执行业务映射】
        type_map, id_map = load_mappings()
        type_col = 'resource_type'
        id_col = 'resource_id'
        
        df[type_col] = df[type_col].apply(clean_id)
        df[id_col] = df[id_col].apply(clean_id)
        
        df = df.merge(type_map, on=type_col, how='left')
        df = df.merge(id_map, on=id_col, how='left')
        
        # 仅对有效数据生成业务标签
        valid_mask = df['is_valid']
        
        # 填充 Get/Cost 标签 (仅对有效行)
        get_mask = (df['event_name'] == 'resource_get') & valid_mask
        df.loc[get_mask, 'tag'] = "通过 " + df['category'] + " 的 " + df['description_x'] + " 获取 " + df['description_y'] + " x" + df['get_count'].astype(str)
        
        cost_mask = (df['event_name'] == 'resource_cost') & valid_mask
        df.loc[cost_mask, 'tag'] = "通过 " + df['category'] + " 的 " + df['description_x'] + " 消耗 " + df['description_y'] + " x" + df['cost_count'].astype(str)
        
        st.success(f"✅ 处理完毕，共 {len(df[df['is_valid']])} 条有效记录，{len(df[~df['is_valid']])} 条作废记录。")
        
        edited_df = st.data_editor(df, num_rows="dynamic", use_container_width=True)
        # ... (下载逻辑保持不变)
        
if __name__ == "__main__":
    main()
