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
    try: 
        # 将 float/double 转为 int，再转为字符串，确保 '1001.0' 和 '1001' 对齐
        return str(int(float(val)))
    except: 
        return str(val).strip()

# --- 2. 编组校验逻辑 ---
def validate_lifecycle(df):
    group_cols = ['account_id', 'current_level', 'challenge_times']
    # 查找闭环动作 (start 和 end)
    starts = df['event_name'] == 'level_start'
    ends = df['event_name'] == 'level_end'
    
    # 找到同时拥有 start 和 end 的组
    valid_groups = df[starts].groupby(group_cols).size().index.intersection(
                   df[ends].groupby(group_cols).size().index)
    
    # 标记有效行
    df['is_valid'] = pd.MultiIndex.from_frame(df[group_cols]).isin(valid_groups)
    df.loc[~df['is_valid'], 'tag'] = "[作废] 进出关记录不闭环"
    return df

# --- 3. 映射表加载 ---
@st.cache_data
def load_mappings():
    type_map = pd.read_csv('config/resource_type_mapping.csv', sep=None, engine='python')
    id_map = pd.read_csv('config/resource_id_mapping.csv', sep=None, engine='python')
    type_map.columns = type_map.columns.str.strip()
    id_map.columns = id_map.columns.str.strip()
    
    # 强制重命名映射表的关联键
    type_map.rename(columns={type_map.columns[0]: 'resource_type'}, inplace=True)
    id_map.rename(columns={id_map.columns[0]: 'resource_id'}, inplace=True)
    return type_map, id_map

# --- 4. 主程序 ---
def main():
    uploaded_file = st.file_uploader("请上传最新的流水账", type=["csv", "txt"])
    if uploaded_file:
        df = read_csv_smart(uploaded_file)
        df = validate_lifecycle(df) # 执行原则一：编组清洗
        type_map, id_map = load_mappings()
        
        # 规整化合并键，防止类型不一致导致的 ValueError
        df['resource_type'] = df['resource_type'].fillna('0').apply(clean_id)
        df['resource_id'] = df['resource_id'].fillna('0').apply(clean_id)
        type_map['resource_type'] = type_map['resource_type'].fillna('0').apply(clean_id)
        id_map['resource_id'] = id_map['resource_id'].fillna('0').apply(clean_id)
        
        # 执行合并
        df = df.merge(type_map, on='resource_type', how='left')
        df = df.merge(id_map, on='resource_id', how='left')
        
        # 【业务叙述逻辑】：基于事件名分流
        valid = df['is_valid']
        
        # 处理获取逻辑
        get_mask = (df['event_name'] == 'resource_get') & valid
        df.loc[get_mask, 'tag'] = (
            "通过 " + df['category'].fillna('未知') + " 的 " + df['description_x'].fillna('未知') + 
            " 获取 " + df['description_y'].fillna('未知') + " x" + df['get_count'].fillna(0).astype(int).astype(str)
        )
        
        # 处理消耗逻辑
        cost_mask = (df['event_name'] == 'resource_cost') & valid
        df.loc[cost_mask, 'tag'] = (
            "通过 " + df['category'].fillna('未知') + " 的 " + df['description_x'].fillna('未知') + 
            " 消耗 " + df['description_y'].fillna('未知') + " x" + df['cost_count'].fillna(0).astype(int).astype(str)
        )
        
        st.success(f"✅ 处理完毕：有效数据 {len(df[df['is_valid']])} 条，作废数据 {len(df[~df['is_valid']])} 条。")
        st.data_editor(df, num_rows="dynamic", use_container_width=True)
        
        # 下载
        csv_buffer = io.StringIO()
        df.to_csv(csv_buffer, index=False)
        st.download_button("💾 下载清洗标注结果", csv_buffer.getvalue(), "labeled_data.csv", "text/csv")
        
if __name__ == "__main__":
    main()
