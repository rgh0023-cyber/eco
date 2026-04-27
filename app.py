import streamlit as st
import pandas as pd
import io
import chardet

st.set_page_config(page_title="游戏经济诊断系统", layout="wide")
st.title("🎮 游戏经济系统定性分析流水账 (编组清洗版)")

# --- 1. 数据读取与清理 ---
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
    try: return str(int(float(val)))
    except: return str(val).strip()

# --- 2. 编组校验逻辑 ---
def validate_lifecycle(df):
    """只对 level_start 和 level_end 进行配对检查"""
    group_cols = ['account_id', 'current_level', 'challenge_times']
    
    # 提取所有 Level 相关事件的闭环
    starts = df['event_name'] == 'level_start'
    ends = df['event_name'] == 'level_end'
    
    # 获取有效组
    valid_groups = df[starts].groupby(group_cols).size().index.intersection(
                   df[ends].groupby(group_cols).size().index)
    
    # 所有行根据归属的组判断是否有效
    df['is_valid'] = pd.MultiIndex.from_frame(df[group_cols]).isin(valid_groups)
    
    # 对所有无效行打上标签
    df.loc[~df['is_valid'], 'tag'] = "[作废] 进出关记录不闭环"
    return df

# --- 3. 映射逻辑 ---
@st.cache_data
def load_mappings():
    type_map = pd.read_csv('config/resource_type_mapping.csv', sep=None, engine='python')
    id_map = pd.read_csv('config/resource_id_mapping.csv', sep=None, engine='python')
    type_map.rename(columns={type_map.columns[0]: 'resource_type'}, inplace=True)
    id_map.rename(columns={id_map.columns[0]: 'resource_id'}, inplace=True)
    return type_map, id_map

# --- 4. 主程序 ---
def main():
    uploaded_file = st.file_uploader("请上传最新的流水账", type=["csv", "txt"])
    if uploaded_file:
        df = read_csv_smart(uploaded_file)
        # 先进行编组清洗
        df = validate_lifecycle(df)
        
        type_map, id_map = load_mappings()
        
        # 规整化合并键
        df['resource_type'] = df['resource_type'].fillna('0').apply(clean_id)
        df['resource_id'] = df['resource_id'].fillna('0').apply(clean_id)
        type_map['resource_type'] = type_map['resource_type'].fillna('0').apply(clean_id)
        id_map['resource_id'] = id_map['resource_id'].fillna('0').apply(clean_id)
        
        df = df.merge(type_map, on='resource_type', how='left')
        df = df.merge(id_map, on='resource_id', how='left')
        
        # --- 业务标注逻辑 ---
        valid = df['is_valid']
        
        # 处理 Get (仅对有效编组内)
        get_mask = (df['event_name'] == 'resource_get') & valid
        df.loc[get_mask, 'tag'] = (
            "通过 " + df['category'].fillna('未知') + " 的 " + df['description_x'].fillna('未知') + 
            " 获取 " + df['description_y'].fillna('未知') + " x" + df['get_count'].fillna(0).astype(int).astype(str)
        )
        
        # 处理 Cost (仅对有效编组内)
        cost_mask = (df['event_name'] == 'resource_cost') & valid
        df.loc[cost_mask, 'tag'] = (
            "通过 " + df['category'].fillna('未知') + " 的 " + df['description_x'].fillna('未知') + 
            " 消耗 " + df['description_y'].fillna('未知') + " x" + df['cost_count'].fillna(0).astype(int).astype(str)
        )

        st.success(f"✅ 处理完毕：{len(df[df['is_valid']])} 条记录属于有效闭环，{len(df[~df['is_valid']])} 条记录被标记为作废。")
        st.data_editor(df, num_rows="dynamic", use_container_width=True)
        
if __name__ == "__main__":
    main()
