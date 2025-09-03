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

def is_consecutive_dates(dates):
    """年月のリストが連続しているかを判定する"""
    if len(dates) <= 1:
        return True
    
    # 年月を数値に変換して連続性をチェック
    numeric_dates = []
    for date_str in dates:
        try:
            year = int(str(date_str)[:4])
            month = int(str(date_str)[4:6])
            numeric_dates.append(year * 12 + month)
        except:
            return False
    
    # 連続性をチェック
    for i in range(1, len(numeric_dates)):
        if numeric_dates[i] != numeric_dates[i-1] + 1:
            return False
    
    return True

def get_enhanced_date_options(df, date_column='Date'):
    """詳細仕様に従った期間選択肢を生成"""
    if date_column not in df.columns:
        return ['全期間']
    
    # 利用可能な年月を取得（昇順ソート）
    available_dates = sorted(df[date_column].dropna().unique().tolist())
    
    if len(available_dates) == 0:
        return ['全期間']
    
    # 基本選択肢
    date_options = ['全期間']
    
    # 連続性を判定
    is_consecutive = is_consecutive_dates(available_dates)
    date_count = len(available_dates)
    
    if is_consecutive:
        # 連続データの場合
        if date_count >= 6:
            # ケース①：連続6か月以上
            first_half = available_dates[:3]
            last_half = available_dates[-3:]
            first_half_label = f"前半3か月間（{first_half[0]}～{first_half[-1]}）"
            last_half_label = f"後半3か月間（{last_half[0]}～{last_half[-1]}）"
            date_options.extend([first_half_label, last_half_label])
            
        elif date_count == 5:
            # ケース②：連続5か月
            first_half = available_dates[:3]
            last_half = available_dates[2:5]  # 3か月間（重複あり）
            first_half_label = f"前半3か月間（{first_half[0]}～{first_half[-1]}）"
            last_half_label = f"後半3か月間（{last_half[0]}～{last_half[-1]}）"
            date_options.extend([first_half_label, last_half_label])
            
        elif date_count == 4:
            # ケース③：連続4か月
            first_half = available_dates[:3]
            last_half = available_dates[1:4]  # 3か月間（重複あり）
            first_half_label = f"前半3か月間（{first_half[0]}～{first_half[-1]}）"
            last_half_label = f"後半3か月間（{last_half[0]}～{last_half[-1]}）"
            date_options.extend([first_half_label, last_half_label])
            
        elif date_count == 3:
            # ケース④：連続3か月
            first_half = available_dates[:2]
            last_half = available_dates[1:3]  # 2か月間（重複あり）
            first_half_label = f"前半2か月間（{first_half[0]}～{first_half[-1]}）"
            last_half_label = f"後半2か月間（{last_half[0]}～{last_half[-1]}）"
            date_options.extend([first_half_label, last_half_label])
        
        # ケース⑤（2か月）、ケース⑥（1か月）は前半・後半なし
    
    # ケース⑦：不連続の場合も前半・後半なし
    
    # 個別月を追加
    date_options.extend(available_dates)
    
    return date_options

def parse_date_filter_selection(selected_date, df, date_column='Date'):
    """期間フィルター選択を解析してフィルタリング条件を返す"""
    if selected_date == '全期間':
        return df.copy()
    
    # 利用可能な年月を取得（昇順ソート）
    available_dates = sorted(df[date_column].dropna().unique().tolist())
    
    if len(available_dates) == 0:
        return df.copy()
    
    # selected_dateを文字列に変換（整数の場合に対応）
    selected_date_str = str(selected_date)
    
    # 連続性を判定
    is_consecutive = is_consecutive_dates(available_dates)
    date_count = len(available_dates)
    
    # 前半期間の判定
    if selected_date_str.startswith('前半') and 'か月間' in selected_date_str:
        if is_consecutive:
            if date_count >= 6:
                # ケース①：連続6か月以上
                target_dates = available_dates[:3]
            elif date_count == 5:
                # ケース②：連続5か月
                target_dates = available_dates[:3]
            elif date_count == 4:
                # ケース③：連続4か月
                target_dates = available_dates[:3]
            elif date_count == 3:
                # ケース④：連続3か月
                target_dates = available_dates[:2]
            else:
                target_dates = available_dates
        else:
            target_dates = available_dates
        return df[df[date_column].isin(target_dates)]
    
    # 後半期間の判定
    if selected_date_str.startswith('後半') and 'か月間' in selected_date_str:
        if is_consecutive:
            if date_count >= 6:
                # ケース①：連続6か月以上
                target_dates = available_dates[-3:]
            elif date_count == 5:
                # ケース②：連続5か月
                target_dates = available_dates[2:5]
            elif date_count == 4:
                # ケース③：連続4か月
                target_dates = available_dates[1:4]
            elif date_count == 3:
                # ケース④：連続3か月
                target_dates = available_dates[1:3]
            else:
                target_dates = available_dates
        else:
            target_dates = available_dates
        return df[df[date_column].isin(target_dates)]
    
    # 個別月の場合（文字列と整数両方に対応）
    if selected_date in available_dates or selected_date_str in [str(d) for d in available_dates]:
        return df[df[date_column] == selected_date] if selected_date in available_dates else df[df[date_column] == selected_date_str]
    
    # 該当しない場合は全データを返す
    return df.copy()

def get_evaluation_method_options():
    """評価方法の選択肢を返す"""
    return [
        "単月データ評価",
        "累積データ評価（選択期間で集計）"
    ]

def get_default_date_selection(df, date_column='Date'):
    """デフォルトの期間選択を取得する（すべてのケースで全期間）"""
    return '全期間'

def get_period_filter_help_text():
    """期間フィルターのヘルプテキストを返す"""
    return ('「前半／後半」の分割は3か月単位を基本とし、対象期間が不足する場合は2か月単位に調整する。'
            'なお、対象期間が2か月以下の場合は、前半／後半の設定は行わない。')

def is_single_month_selection(selected_date, df, date_column='Date'):
    """選択された期間が単月かどうかを判定する"""
    if selected_date == '全期間':
        return False
    
    # 利用可能な年月を取得
    available_dates = sorted(df[date_column].dropna().unique().tolist()) if date_column in df.columns else []
    
    # selected_dateを文字列に変換
    selected_date_str = str(selected_date)
    
    # 前半・後半の判定
    if selected_date_str.startswith('前半') or selected_date_str.startswith('後半'):
        return False
    
    # 個別月の判定
    return selected_date in available_dates or selected_date_str in [str(d) for d in available_dates]

def aggregate_data_for_cumulative_evaluation(df, selected_date, date_column='Date'):
    """累積データ評価用にデータを集計する"""
    # まず期間フィルターを適用
    filtered_df = parse_date_filter_selection(selected_date, df, date_column)
    
    if filtered_df.empty:
        return filtered_df
    
    # 商品コード単位で集計
    numeric_columns = ['Actual', 'AI_pred', 'Plan_01']
    if 'Plan_02' in filtered_df.columns:
        numeric_columns.append('Plan_02')
    
    # 集計対象列を特定
    group_columns = ['P_code']
    if 'category_code' in filtered_df.columns:
        group_columns.append('category_code')
    if 'Class_abc' in filtered_df.columns:
        group_columns.append('Class_abc')
    
    # 数値列のみを集計
    agg_dict = {col: 'sum' for col in numeric_columns if col in filtered_df.columns}
    
    try:
        cumulative_df = filtered_df.groupby(group_columns).agg(agg_dict).reset_index()
        
        # 期間情報を追加（集計期間を示すために）
        selected_date_str = str(selected_date)
        if selected_date == '全期間':
            cumulative_df['Date'] = '全期間'
        elif selected_date_str.startswith('前半') or selected_date_str.startswith('後半'):
            cumulative_df['Date'] = selected_date_str
        else:
            cumulative_df['Date'] = selected_date_str
        
        return cumulative_df
    
    except Exception as e:
        st.error(f"累積データの集計でエラーが発生しました: {str(e)}")
        return filtered_df