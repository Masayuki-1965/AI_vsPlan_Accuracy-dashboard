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
    display_error_rate_matrix(filtered_df, filter_settings)
    
    # 基本統計情報表示
    display_basic_statistics(filtered_df, filter_settings)

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
            help="絶対: |計画-実績|÷計画, 正: 計画>実績(滞留), 負: 計画<実績(欠品)"
        )
        filter_settings['error_type'] = error_types[selected_error_type]
        
    with col2:
        # 計画値フィルター
        plan_options = ['AI予測 vs 計画01']
        if 'Plan_02' in df.columns:
            plan_options.append('AI予測 vs 計画02')
        
        selected_comparison = st.selectbox("比較対象", plan_options)
        filter_settings['plan_column'] = 'Plan_01' if '計画01' in selected_comparison else 'Plan_02'
        
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

def get_prediction_name(pred_type):
    """予測タイプの表示名を取得"""
    name_mapping = {
        'AI_pred': 'AI予測',
        'Plan_01': '計画01',
        'Plan_02': '計画02'
    }
    return name_mapping.get(pred_type, pred_type)

def display_error_rate_matrix(df, filter_settings):
    """要求仕様に基づく誤差率マトリクス表示"""
    st.subheader("📊 誤差率評価マトリクス")
    
    # 計画値とAI予測の誤差率計算
    plan_col = filter_settings['plan_column']
    error_type = filter_settings['error_type']
    abc_categories = filter_settings['abc_categories']
    
    # AI予測と計画値の誤差率計算
    ai_errors = calculate_error_rates(df, 'AI_pred', 'Actual')
    plan_errors = calculate_error_rates(df, plan_col, 'Actual')
    
    # マトリクス作成
    ai_matrix = create_advanced_matrix(ai_errors, 'AI_pred', error_type, abc_categories)
    plan_matrix = create_advanced_matrix(plan_errors, plan_col, error_type, abc_categories)
    
    # マトリクス表示
    display_combined_matrix(ai_matrix, plan_matrix, error_type, abc_categories)

def create_advanced_matrix(df, pred_col, error_type, abc_categories):
    """高度なマトリクス作成"""
    # 誤差率カラム選択
    if error_type == 'absolute':
        error_col = 'absolute_error_rate'
        error_name = '絶対誤差率'
    elif error_type == 'positive':
        error_col = 'positive_error_rate'
        error_name = '正の誤差率'
    else:  # negative
        error_col = 'negative_error_rate'
        error_name = '負の誤差率'
    
    # 誤差率区分追加
    df_with_category = df.copy()
    df_with_category['error_category'] = categorize_error_rates(df, error_col)
    
    # 合計マトリクス
    total_matrix = df_with_category.groupby('error_category').agg({
        'P_code': 'count',
        error_col: lambda x: calculate_weighted_average_error_rate(
            df_with_category.loc[x.index], error_col, 'Actual'
        )
    }).rename(columns={'P_code': 'count', error_col: 'weighted_avg_error'})
    
    # ABC区分別マトリクス
    abc_matrices = {}
    if 'Class_abc' in df.columns and abc_categories:
        for abc in abc_categories:
            abc_data = df_with_category[df_with_category['Class_abc'] == abc]
            if not abc_data.empty:
                abc_matrix = abc_data.groupby('error_category').agg({
                    'P_code': 'count',
                    error_col: lambda x: calculate_weighted_average_error_rate(
                        abc_data.loc[x.index], error_col, 'Actual'
                    ) if len(x) > 0 else np.nan
                }).rename(columns={'P_code': 'count', error_col: 'weighted_avg_error'})
                abc_matrices[abc] = abc_matrix
    
    return {
        'total': total_matrix,
        'abc': abc_matrices,
        'error_type': error_name
    }

def display_combined_matrix(ai_matrix, plan_matrix, error_type, abc_categories):
    """結合マトリクス表示"""
    # 誤差率カテゴリー
    error_categories = ['0-10%', '10-20%', '20-30%', '30-50%', '50-100%', '100%超']
    
    # 表示用データフレーム作成
    matrix_data = []
    
    for category in error_categories:
        row = {'誤差率帯': category}
        
        # 合計（AI予測／計画）
        ai_count = ai_matrix['total'].loc[category, 'count'] if category in ai_matrix['total'].index else 0
        plan_count = plan_matrix['total'].loc[category, 'count'] if category in plan_matrix['total'].index else 0
        row['合計_AI予測'] = ai_count
        row['合計_計画'] = plan_count
        
        # ABC区分別
        for abc in abc_categories:
            if abc in ai_matrix['abc']:
                ai_abc_count = ai_matrix['abc'][abc].loc[category, 'count'] if category in ai_matrix['abc'][abc].index else 0
            else:
                ai_abc_count = 0
                
            if abc in plan_matrix['abc']:
                plan_abc_count = plan_matrix['abc'][abc].loc[category, 'count'] if category in plan_matrix['abc'][abc].index else 0
            else:
                plan_abc_count = 0
                
            row[f'{abc}区分_AI予測'] = ai_abc_count
            row[f'{abc}区分_計画'] = plan_abc_count
        
        matrix_data.append(row)
    
    # 加重平均誤差率行を追加
    weighted_avg_row = {'誤差率帯': '加重平均'}
    
    # 合計の加重平均
    ai_total_avg = calculate_overall_weighted_average(ai_matrix['total'])
    plan_total_avg = calculate_overall_weighted_average(plan_matrix['total'])
    weighted_avg_row['合計_AI予測'] = f"{ai_total_avg:.0%}" if not np.isnan(ai_total_avg) else "N/A"
    weighted_avg_row['合計_計画'] = f"{plan_total_avg:.0%}" if not np.isnan(plan_total_avg) else "N/A"
    
    # ABC区分別の加重平均
    for abc in abc_categories:
        if abc in ai_matrix['abc']:
            ai_abc_avg = calculate_overall_weighted_average(ai_matrix['abc'][abc])
            weighted_avg_row[f'{abc}区分_AI予測'] = f"{ai_abc_avg:.0%}" if not np.isnan(ai_abc_avg) else "N/A"
        else:
            weighted_avg_row[f'{abc}区分_AI予測'] = "N/A"
            
        if abc in plan_matrix['abc']:
            plan_abc_avg = calculate_overall_weighted_average(plan_matrix['abc'][abc])
            weighted_avg_row[f'{abc}区分_計画'] = f"{plan_abc_avg:.0%}" if not np.isnan(plan_abc_avg) else "N/A"
        else:
            weighted_avg_row[f'{abc}区分_計画'] = "N/A"
    
    matrix_data.append(weighted_avg_row)
    
    # データフレーム作成・表示
    matrix_df = pd.DataFrame(matrix_data)
    
    # スタイル適用
    def highlight_weighted_avg(row):
        return ['background-color: #f0f0f0' if row.name == len(matrix_df) - 1 else '' for _ in row]
    
    styled_df = matrix_df.style.apply(highlight_weighted_avg, axis=1)
    
    st.dataframe(styled_df, use_container_width=True)
    
def calculate_overall_weighted_average(matrix):
    """全体加重平均誤差率計算"""
    if matrix.empty:
        return np.nan
    
    # 各カテゴリーの加重平均誤差率と件数を用いて全体平均を計算
    total_weighted_sum = 0
    total_count = 0
    
    for _, row in matrix.iterrows():
        if not np.isnan(row['weighted_avg_error']) and row['count'] > 0:
            total_weighted_sum += row['weighted_avg_error'] * row['count']
            total_count += row['count']
    
    return total_weighted_sum / total_count if total_count > 0 else np.nan

def display_basic_statistics(df, filter_settings):
    """基本統計情報を統一形式で表示"""
    st.subheader("📈 基本統計情報")
    
    plan_col = filter_settings['plan_column']
    
    # 統計データ作成
    stats_data = {}
    
    # AI予測値統計
    ai_stats = df['AI_pred'].describe()
    stats_data['AI予測値'] = ai_stats
    
    # 計画値統計
    plan_name = '計画01' if plan_col == 'Plan_01' else '計画02'
    plan_stats = df[plan_col].describe()
    stats_data[plan_name] = plan_stats
    
    # 実績値統計
    actual_stats = df['Actual'].describe()
    stats_data['実績値'] = actual_stats
    
    # 統計表作成
    stats_df = pd.DataFrame(stats_data)
    
    # インデックス名を日本語に変更
    index_mapping = {
        'count': '件数',
        'mean': '平均',
        'std': '標準偏差',
        'min': '最小値',
        '25%': '25%点',
        '50%': '中央値',
        '75%': '75%点',
        'max': '最大値'
    }
    
    stats_df.index = [index_mapping.get(idx, idx) for idx in stats_df.index]
    
    # 数値フォーマット適用
    formatted_df = stats_df.style.format({
        'AI予測値': '{:.1f}',
        plan_name: '{:.1f}',
        '実績値': '{:.1f}'
    })
    
    st.dataframe(formatted_df, use_container_width=True)
    
    # 相関分析
    st.subheader("🔗 相関分析")
    col1, col2 = st.columns(2)
    
    with col1:
        ai_actual_corr = df['AI_pred'].corr(df['Actual'])
        st.metric(
            f"AI予測 vs 実績 相関係数",
            f"{ai_actual_corr:.3f}",
            help="1に近いほど正の相関が強い"
        )
    
    with col2:
        plan_actual_corr = df[plan_col].corr(df['Actual'])
        st.metric(
            f"{plan_name} vs 実績 相関係数",
            f"{plan_actual_corr:.3f}",
            help="1に近いほど正の相関が強い"
        ) 