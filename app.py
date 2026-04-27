import streamlit as st
import pandas as pd
import io
import chardet

# --- 1. 编组校验逻辑 (纯净版) ---
def validate_lifecycle(df):
    """只判定 level 事件的闭环，返回 True/False 的序列"""
    group_cols = ['account_id', 'current_level', 'challenge_times']
    starts = df['event_name'] == 'level_start'
    ends = df['event_name'] == 'level_end'
    
    valid_groups = df[starts].groupby(group_cols).size().index.intersection(
                   df[ends].groupby(group_cols).size().index)
    
    # 判定规则：
    # 1. 如果是 level 事件，必须在 valid_groups 中
    # 2. 如果非 level 事件，自动为 True
    is_level_event = df['event_name'].str.startswith('level_')
    in_valid_group = pd.MultiIndex.from_frame(df[group_cols]).isin(valid_groups)
    
    # 逻辑：(是level事件 且 在有效组中) OR (不是level事件)
    return (is_level_event & in_valid_group) | (~is_level_event)

# --- 2. 主程序片段 ---
def main():
    # ... (读取与映射代码保持不变) ...
    
    # 1. 计算可用性
    df['is_usable'] = validate_lifecycle(df)
    
    # 2. 定量描述逻辑 (仅处理有效的且对应的事件)
    # 确保 tag 为空字符串初始化
    if 'tag' not in df.columns: df['tag'] = ""
    
    get_mask = (df['event_name'] == 'resource_get')
    df.loc[get_mask, 'tag'] = (
        "通过 " + df['category'].fillna('未知') + " 的 " + df['description_x'].fillna('未知') + 
        " 获取 " + df['description_y'].fillna('未知') + " x" + df['get_count'].fillna(0).astype(int).astype(str)
    )
    
    cost_mask = (df['event_name'] == 'resource_cost')
    df.loc[cost_mask, 'tag'] = (
        "通过 " + df['category'].fillna('未知') + " 的 " + df['description_x'].fillna('未知') + 
        " 消耗 " + df['description_y'].fillna('未知') + " x" + df['cost_count'].fillna(0).astype(int).astype(str)
    )
    
    # --- 界面展示 ---
    # 我们可以把 is_usable 放在第一列，方便你一眼识别
    cols = ['is_usable'] + [c for c in df.columns if c != 'is_usable']
    df = df[cols]
    
    st.data_editor(df, num_rows="dynamic", use_container_width=True)
