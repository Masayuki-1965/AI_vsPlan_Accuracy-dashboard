import streamlit as st
import pandas as pd
import numpy as np
from utils.error_calculator import (
    calculate_error_rates, 
    create_error_matrix, 
    compare_prediction_accuracy,
    calculate_weighted_average_error_rate,
    categorize_error_rates
)
from config.settings import COLOR_PALETTE, ERROR_RATE_CATEGORIES, MATRIX_DISPLAY_SETTINGS
from config.ui_styles import HELP_TEXTS, MATRIX_EXPLANATION, ERROR_RATE_DEFINITIONS
from config.constants import PREDICTION_TYPE_NAMES

def show():
    """誤差率評価マトリクスページを表示"""
    st.header("📊 誤差率評価マトリクス")
    
    # データ確認
    if st.session_state.data is None:
        st.warning("⚠️ データが読み込まれていません。データアップロードページからデータを読み込んでください。")
        return
    
    df = st.session_state.data
    
    # フィルター設定
    st.subheader("🔍 フィルター設定")
    filter_settings = create_filter_ui(df)
    
    # フィルター適用
    filtered_df = apply_advanced_filters(df, filter_settings)
    
    if filtered_df.empty:
        st.warning("⚠️ フィルター条件に該当するデータがありません。")
        return
    
    st.info(f"📊 フィルター後データ件数: {len(filtered_df)}件")
    
    # 誤差率マトリクス表示
    display_new_error_rate_matrix(filtered_df, filter_settings)

def create_filter_ui(df):
    """改善されたフィルターUIを作成"""
    filter_settings = {}
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        # 誤差率タイプフィルター
        error_types = {
            '絶対誤差率': 'absolute',
            '正の誤差率': 'positive', 
            '負の誤差率': 'negative'
        }
        selected_error_type = st.selectbox(
            "誤差率タイプ",
            list(error_types.keys()),
            help=HELP_TEXTS['error_type_help']
        )
        filter_settings['error_type'] = error_types[selected_error_type]
        
    with col2:
        # 計画値フィルター
        plan_options = ['計画01']
        if 'Plan_02' in df.columns:
            plan_options.append('計画02')
        
        selected_plan = st.selectbox("計画値", plan_options)
        filter_settings['plan_column'] = 'Plan_01' if selected_plan == '計画01' else 'Plan_02'
        
    with col3:
        # ABC区分フィルター
        if 'Class_abc' in df.columns:
            abc_values = sorted(df['Class_abc'].dropna().unique().tolist())
            default_abc = ['A', 'B', 'C'] if all(x in abc_values for x in ['A', 'B', 'C']) else abc_values[:3]
            
            selected_abc = st.multiselect(
                "ABC区分表示",
                abc_values,
                default=default_abc,
                help="最大3つまで選択可能"
            )
            filter_settings['abc_categories'] = selected_abc[:3]  # 最大3つまで
        else:
            filter_settings['abc_categories'] = []
    
    with col4:
        # 期間フィルター
        if 'Date' in df.columns:
            date_options = ['全期間'] + sorted(df['Date'].dropna().unique().tolist())
            selected_date = st.selectbox("期間", date_options)
            filter_settings['date'] = None if selected_date == '全期間' else selected_date
        else:
            filter_settings['date'] = None
    
    return filter_settings

def apply_advanced_filters(df, filter_settings):
    """改良されたフィルター適用"""
    filtered_df = df.copy()
    
    # 期間フィルター
    if filter_settings['date'] and 'Date' in df.columns:
        filtered_df = filtered_df[filtered_df['Date'] == filter_settings['date']]
    
    return filtered_df

def display_new_error_rate_matrix(df, filter_settings):
    """新仕様に基づく誤差率マトリクス表示"""
    plan_col = filter_settings['plan_column']
    error_type = filter_settings['error_type']
    abc_categories = filter_settings['abc_categories']
    
    # 説明文追加（誤差率タイプに応じて動的変更）
    error_definition = get_error_rate_definition(error_type)
    st.markdown(f"""
    {MATRIX_EXPLANATION['matrix_note']}  
    {MATRIX_EXPLANATION['error_definition_prefix']}  {error_definition} {MATRIX_EXPLANATION['error_definition_suffix']}
    """)
    
    # AI予測と計画値の誤差率計算
    ai_errors = calculate_error_rates(df, 'AI_pred', 'Actual')
    plan_errors = calculate_error_rates(df, plan_col, 'Actual')
    
    # 新仕様マトリクス作成
    matrix_df = create_comprehensive_matrix(ai_errors, plan_errors, error_type, abc_categories, plan_col)
    
    # マトリクス表示
    display_styled_matrix(matrix_df, abc_categories)

def create_comprehensive_matrix(ai_errors, plan_errors, error_type, abc_categories, plan_col):
    """新仕様に基づく包括的マトリクス作成（2段ヘッダー対応）"""
    # 誤差率カラム選択
    if error_type == 'absolute':
        error_col = 'absolute_error_rate'
    elif error_type == 'positive':
        error_col = 'positive_error_rate'
    else:  # negative
        error_col = 'negative_error_rate'
    
    # 誤差率区分追加
    ai_errors['error_category'] = categorize_error_rates(ai_errors, error_col)
    plan_errors['error_category'] = categorize_error_rates(plan_errors, error_col)
    
    # 誤差率帯の順序定義（誤差率タイプに応じて符号付き）
    error_bands_original = [cat['label'] for cat in ERROR_RATE_CATEGORIES]
    error_bands_display = get_error_rate_bands_with_signs(error_type)
    
    # 2段ヘッダーの構造定義
    categories = ['合計'] + [f'{abc}区分' for abc in abc_categories]
    subcategories = ['AI予測', get_plan_name(plan_col)]
    
    # MultiIndex作成
    columns_tuples = []
    for category in categories:
        for subcategory in subcategories:
            columns_tuples.append((category, subcategory))
    
    multi_index = pd.MultiIndex.from_tuples(columns_tuples, names=['区分', '予測タイプ'])
    
    # データフレーム初期化
    matrix_data = []
    
    # 各誤差率帯の集計
    for i, band_original in enumerate(error_bands_original):
        band_display = error_bands_display[i]
        row_data = []
        
        # 合計（AI予測／計画）
        ai_count = len(ai_errors[ai_errors['error_category'] == band_original])
        plan_count = len(plan_errors[plan_errors['error_category'] == band_original])
        row_data.extend([ai_count, plan_count])
        
        # ABC区分別
        for abc in abc_categories:
            if 'Class_abc' in ai_errors.columns:
                ai_abc_count = len(ai_errors[(ai_errors['error_category'] == band_original) & (ai_errors['Class_abc'] == abc)])
                plan_abc_count = len(plan_errors[(plan_errors['error_category'] == band_original) & (plan_errors['Class_abc'] == abc)])
                row_data.extend([ai_abc_count, plan_abc_count])
            else:
                row_data.extend([0, 0])
        
        matrix_data.append(row_data)
    
    # 合計行の追加
    total_row_data = []
    total_row_data.extend([len(ai_errors), len(plan_errors)])
    
    for abc in abc_categories:
        if 'Class_abc' in ai_errors.columns:
            ai_abc_total = len(ai_errors[ai_errors['Class_abc'] == abc])
            plan_abc_total = len(plan_errors[plan_errors['Class_abc'] == abc])
            total_row_data.extend([ai_abc_total, plan_abc_total])
        else:
            total_row_data.extend([0, 0])
    
    matrix_data.append(total_row_data)
    
    # 加重平均誤差率行の追加
    avg_row_data = []
    
    # 全体の加重平均誤差率を計算（正負分けて計算）
    if error_type == 'positive':
        # 正の誤差率のみでフィルタリングしてから計算
        ai_positive = ai_errors[ai_errors['error_rate'] > 0]
        plan_positive = plan_errors[plan_errors['error_rate'] > 0]
        
        if len(ai_positive) > 0:
            ai_weighted_avg = calculate_weighted_average_error_rate(ai_positive, 'error_rate', 'Actual') * 100
            ai_formatted = f"+{ai_weighted_avg:.1f}%"
        else:
            ai_formatted = "+0.0%"
            
        if len(plan_positive) > 0:
            plan_weighted_avg = calculate_weighted_average_error_rate(plan_positive, 'error_rate', 'Actual') * 100
            plan_formatted = f"+{plan_weighted_avg:.1f}%"
        else:
            plan_formatted = "+0.0%"
            
        avg_row_data.extend([ai_formatted, plan_formatted])
        
    elif error_type == 'negative':
        # 負の誤差率のみでフィルタリングしてから計算
        ai_negative = ai_errors[ai_errors['error_rate'] < 0]
        plan_negative = plan_errors[plan_errors['error_rate'] < 0]
        
        if len(ai_negative) > 0:
            ai_weighted_avg = calculate_weighted_average_error_rate(ai_negative, 'error_rate', 'Actual') * 100
            ai_formatted = f"{ai_weighted_avg:.1f}%"
        else:
            ai_formatted = "0.0%"
            
        if len(plan_negative) > 0:
            plan_weighted_avg = calculate_weighted_average_error_rate(plan_negative, 'error_rate', 'Actual') * 100
            plan_formatted = f"{plan_weighted_avg:.1f}%"
        else:
            plan_formatted = "0.0%"
            
        avg_row_data.extend([ai_formatted, plan_formatted])
        
    else:  # absolute
        # 絶対誤差率は従来通り
        ai_weighted_avg = calculate_weighted_average_error_rate(ai_errors, error_col, 'Actual') * 100
        plan_weighted_avg = calculate_weighted_average_error_rate(plan_errors, error_col, 'Actual') * 100
        avg_row_data.extend([f"{ai_weighted_avg:.1f}%", f"{plan_weighted_avg:.1f}%"])
    
    # ABC区分別の加重平均誤差率を計算
    for abc in abc_categories:
        if 'Class_abc' in ai_errors.columns:
            ai_abc_data = ai_errors[ai_errors['Class_abc'] == abc]
            plan_abc_data = plan_errors[plan_errors['Class_abc'] == abc]
            
            # 正の誤差率の場合は正の値のみでフィルタリング
            if error_type == 'positive':
                ai_abc_positive = ai_abc_data[ai_abc_data['error_rate'] > 0]
                plan_abc_positive = plan_abc_data[plan_abc_data['error_rate'] > 0]
                
                if len(ai_abc_positive) > 0:
                    ai_abc_weighted_avg = calculate_weighted_average_error_rate(ai_abc_positive, 'error_rate', 'Actual') * 100
                    avg_row_data.append(f"+{ai_abc_weighted_avg:.1f}%")
                else:
                    avg_row_data.append("+0.0%")
                    
                if len(plan_abc_positive) > 0:
                    plan_abc_weighted_avg = calculate_weighted_average_error_rate(plan_abc_positive, 'error_rate', 'Actual') * 100
                    avg_row_data.append(f"+{plan_abc_weighted_avg:.1f}%")
                else:
                    avg_row_data.append("+0.0%")
                    
            elif error_type == 'negative':
                ai_abc_negative = ai_abc_data[ai_abc_data['error_rate'] < 0]
                plan_abc_negative = plan_abc_data[plan_abc_data['error_rate'] < 0]
                
                if len(ai_abc_negative) > 0:
                    ai_abc_weighted_avg = calculate_weighted_average_error_rate(ai_abc_negative, 'error_rate', 'Actual') * 100
                    avg_row_data.append(f"{ai_abc_weighted_avg:.1f}%")
                else:
                    avg_row_data.append("0.0%")
                    
                if len(plan_abc_negative) > 0:
                    plan_abc_weighted_avg = calculate_weighted_average_error_rate(plan_abc_negative, 'error_rate', 'Actual') * 100
                    avg_row_data.append(f"{plan_abc_weighted_avg:.1f}%")
                else:
                    avg_row_data.append("0.0%")
                    
            else:  # absolute
                if len(ai_abc_data) > 0:
                    ai_abc_weighted_avg = calculate_weighted_average_error_rate(ai_abc_data, error_col, 'Actual') * 100
                    avg_row_data.append(f"{ai_abc_weighted_avg:.1f}%")
                else:
                    avg_row_data.append("0.0%")
                    
                if len(plan_abc_data) > 0:
                    plan_abc_weighted_avg = calculate_weighted_average_error_rate(plan_abc_data, error_col, 'Actual') * 100
                    avg_row_data.append(f"{plan_abc_weighted_avg:.1f}%")
                else:
                    avg_row_data.append("0.0%")
        else:
            if error_type == 'positive':
                avg_row_data.extend(["+0.0%", "+0.0%"])
            else:
                avg_row_data.extend(["0.0%", "0.0%"])
    
    matrix_data.append(avg_row_data)
    
    # インデックス作成
    index_labels = error_bands_display + ['合計（件数）', '加重平均誤差率（%）']
    
    # DataFrame作成
    matrix_df = pd.DataFrame(matrix_data, index=index_labels, columns=multi_index)
    
    # インデックス名を設定
    matrix_df.index.name = '誤差率帯'
    
    return matrix_df

def get_plan_name(plan_col):
    """計画カラム名を表示用に変換"""
    from config.constants import PLAN_TYPE_NAMES
    return PLAN_TYPE_NAMES.get(plan_col, plan_col)

def get_error_rate_definition(error_type):
    """誤差率タイプに応じた定義文を取得"""
    return ERROR_RATE_DEFINITIONS.get(error_type, ERROR_RATE_DEFINITIONS['absolute'])

def get_error_rate_bands_with_signs(error_type):
    """誤差率タイプに応じた符号付き誤差率帯ラベル生成"""
    bands = []
    for cat in ERROR_RATE_CATEGORIES:
        label = cat['label']
        
        # 新しい表記形式に変更（「～」を使用）
        if error_type in ['positive', 'negative']:
            if error_type == 'positive':
                # 正の誤差率の場合は「+」を付ける
                if label == '0 - 10%':
                    label = '+0％ ～ +10％'
                elif label == '10 - 20%':
                    label = '+10％ ～ +20％'
                elif label == '20 - 30%':
                    label = '+20％ ～ +30％'
                elif label == '30 - 50%':
                    label = '+30％ ～ +50％'
                elif label == '50 - 100%':
                    label = '+50％ ～ +100％'
                elif label == '100%以上':
                    label = '+100％以上'
                elif label == '計算不能（実績ゼロ）':
                    label = '計算不能（実績ゼロ）'
            else:  # negative
                # 負の誤差率の場合は「-」を付ける
                if label == '0 - 10%':
                    label = '-0％ ～ -10％'
                elif label == '10 - 20%':
                    label = '-10％ ～ -20％'
                elif label == '20 - 30%':
                    label = '-20％ ～ -30％'
                elif label == '30 - 50%':
                    label = '-30％ ～ -50％'
                elif label == '50 - 100%':
                    label = '-50％ ～ -100％'
                elif label == '100%以上':
                    label = '-100％以上'
                elif label == '計算不能（実績ゼロ）':
                    label = '計算不能（実績ゼロ）'
        else:
            # 絶対誤差率の場合は符号なしで「～」表記
            if label == '0 - 10%':
                label = '0％ ～ 10％'
            elif label == '10 - 20%':
                label = '10％ ～ 20％'
            elif label == '20 - 30%':
                label = '20％ ～ 30％'
            elif label == '30 - 50%':
                label = '30％ ～ 50％'
            elif label == '50 - 100%':
                label = '50％ ～ 100％'
            elif label == '100%以上':
                label = '100％以上'
            elif label == '計算不能（実績ゼロ）':
                label = '計算不能（実績ゼロ）'
        
        bands.append(label)
    
    return bands

def display_styled_matrix(matrix_df, abc_categories):
    """2段ヘッダー維持＋誤差率帯列幅制御版マトリクス表示"""
    # データ型の統一処理（Arrow互換性確保）
    matrix_formatted = matrix_df.copy()
    
    # 全てのデータを文字列に統一してArrow互換性を確保
    for idx in matrix_formatted.index:
        for col in matrix_formatted.columns:
            val = matrix_formatted.loc[idx, col]
            if pd.isna(val):
                matrix_formatted.loc[idx, col] = ""
            elif idx == '加重平均誤差率（%）':
                # 加重平均行はパーセント表記のまま
                matrix_formatted.loc[idx, col] = str(val)
            else:
                # 件数行は整数として表示してから文字列に変換
                try:
                    if isinstance(val, (int, float)) and not pd.isna(val):
                        matrix_formatted.loc[idx, col] = str(int(val))
                    else:
                        matrix_formatted.loc[idx, col] = str(val)
                except:
                    matrix_formatted.loc[idx, col] = str(val)
    
    # MultiIndex構造を維持（平坦化しない）
    # 2段ヘッダー構造を保持したまま処理
    
    # インデックをリセットして誤差率帯を通常の列として扱う
    matrix_display = matrix_formatted.reset_index()
    
    # 列幅設定：誤差率帯列のみを対象とする
    column_config = {
        "誤差率帯": st.column_config.TextColumn(
            "誤差率帯",
            width="medium",  # 適切な幅に設定
            help="誤差率の区分範囲"
        )
    }
    
    # DataFrame表示（2段ヘッダー維持＋誤差率帯列幅制御）
    st.dataframe(
        matrix_display,
        use_container_width=True,
        column_config=column_config,
        hide_index=True
    ) 