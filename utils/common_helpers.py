# 共通ヘルパー関数
# 各ページで使用される共通処理を統合管理

import streamlit as st
import pandas as pd
import numpy as np

def safe_get_session_state(key, default_value=None):
    """セッション状態を安全に取得"""
    return st.session_state.get(key, default_value)

def initialize_session_state(key, default_value):
    """セッション状態を初期化（存在しない場合のみ）"""
    if key not in st.session_state:
        st.session_state[key] = default_value

def validate_required_columns(df, required_columns):
    """必須カラムの存在チェック"""
    if df is None or df.empty:
        return False, "データが空です"
    
    missing_columns = [col for col in required_columns if col not in df.columns]
    if missing_columns:
        return False, f"必要な列が不足しています: {missing_columns}"
    
    return True, "OK"

def filter_dataframe_by_category(df, category_column='category_code', selected_category='全て'):
    """分類による DataFrame フィルタリング"""
    if selected_category == '全て' or category_column not in df.columns:
        return df
    return df[df[category_column] == selected_category]

def filter_dataframe_by_abc(df, abc_column='Class_abc', selected_abc_list=None):
    """ABC区分による DataFrame フィルタリング"""
    if not selected_abc_list or abc_column not in df.columns:
        return df
    return df[df[abc_column].isin(selected_abc_list)]

def get_unique_categories(df, category_column='category_code', include_all=True):
    """分類の一意値を取得（「全て」オプション付き）"""
    if category_column not in df.columns:
        return ['全て'] if include_all else []
    
    categories = sorted(df[category_column].dropna().unique().tolist())
    if include_all:
        return ['全て'] + categories
    return categories

def get_unique_abc_categories(df, abc_column='Class_abc'):
    """ABC区分の一意値を取得"""
    if abc_column not in df.columns:
        return []
    return sorted(df[abc_column].dropna().unique().tolist())

def safe_numeric_conversion(series, fill_value=0):
    """安全な数値変換（エラー値は指定値で置換）"""
    return pd.to_numeric(series, errors='coerce').fillna(fill_value)

def calculate_percentage(numerator, denominator, decimal_places=2):
    """安全な割合計算"""
    if denominator == 0:
        return 0.0
    return round((numerator / denominator) * 100, decimal_places)

def format_number_display(value, decimal_places=0):
    """数値の表示形式を統一"""
    if pd.isna(value) or value == float('inf') or value == float('-inf'):
        return "N/A"
    
    if decimal_places == 0:
        return f"{int(value):,}"
    else:
        return f"{value:,.{decimal_places}f}"

def show_processing_status(message="処理中..."):
    """処理中ステータスの表示"""
    return st.status(message, expanded=False)

def show_success_message(message):
    """成功メッセージの表示"""
    st.success(message)

def show_error_message(message):
    """エラーメッセージの表示"""
    st.error(message)

def show_warning_message(message):
    """警告メッセージの表示"""
    st.warning(message)

def show_info_message(message):
    """情報メッセージの表示"""
    st.info(message)

def get_selectbox_index(options, value, default_index=0):
    """selectboxのindex値を安全に取得"""
    try:
        return options.index(value) if value in options else default_index
    except (ValueError, TypeError):
        return default_index

def safe_dataframe_groupby_sum(df, group_column, sum_column):
    """安全なDataFrameのgroupby sum操作"""
    try:
        if group_column not in df.columns or sum_column not in df.columns:
            return pd.Series(dtype=float)
        
        return df.groupby(group_column)[sum_column].sum()
    except Exception:
        return pd.Series(dtype=float)

def validate_data_completeness(df, required_columns=None):
    """データの完全性チェック"""
    if df is None or df.empty:
        return False, "データが存在しません"
    
    if required_columns:
        missing_cols = [col for col in required_columns if col not in df.columns]
        if missing_cols:
            return False, f"必須列が不足しています: {missing_cols}"
    
    # 基本的なデータ品質チェック
    if len(df) == 0:
        return False, "データが空です"
    
    return True, "データは有効です"

def create_download_data(df, filename_prefix="data"):
    """ダウンロード用データの作成"""
    try:
        csv = df.to_csv(index=False, encoding='utf-8-sig')
        return csv.encode('utf-8-sig')
    except Exception as e:
        st.error(f"ダウンロードデータの作成に失敗しました: {str(e)}")
        return None

def display_dataframe_with_pagination(df, page_size=100):
    """ページネーション付きDataFrame表示"""
    if df is None or df.empty:
        st.info("表示するデータがありません")
        return
    
    total_rows = len(df)
    if total_rows <= page_size:
        st.dataframe(df, use_container_width=True)
        return
    
    # ページネーション
    total_pages = (total_rows + page_size - 1) // page_size
    page = st.number_input(
        f"ページ (1-{total_pages})", 
        min_value=1, 
        max_value=total_pages, 
        value=1
    )
    
    start_idx = (page - 1) * page_size
    end_idx = min(start_idx + page_size, total_rows)
    
    st.dataframe(df.iloc[start_idx:end_idx], use_container_width=True)
    st.caption(f"表示: {start_idx + 1}-{end_idx} / {total_rows} 件")
