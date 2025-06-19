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
    
    # 新仕様の誤差率マトリクス表示
    display_new_error_rate_matrix(filtered_df, filter_settings)
    
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
            help="絶対: |計画-実績|÷実績, 正: 計画>実績(滞留), 負: 計画<実績(欠品)"
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
    st.subheader("📊 誤差率評価マトリクス")
    
    plan_col = filter_settings['plan_column']
    error_type = filter_settings['error_type']
    abc_categories = filter_settings['abc_categories']
    
    # 説明文追加（誤差率タイプに応じて動的変更）
    error_definition = get_error_rate_definition(error_type)
    st.markdown(f"""
    **※マトリクス内はすべて商品コードの件数です**  
    **誤差率定義**: {error_definition}（分母：実績値）
    """)
    
    # AI予測と計画値の誤差率計算
    ai_errors = calculate_error_rates(df, 'AI_pred', 'Actual')
    plan_errors = calculate_error_rates(df, plan_col, 'Actual')
    
    # 新仕様マトリクス作成
    matrix_df = create_comprehensive_matrix(ai_errors, plan_errors, error_type, abc_categories, plan_col)
    
    # マトリクス表示
    display_styled_matrix(matrix_df, abc_categories)

def create_comprehensive_matrix(ai_errors, plan_errors, error_type, abc_categories, plan_col):
    """新仕様に基づく包括的マトリクス作成"""
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
    
    # カラム定義
    columns = ['誤差率帯']
    columns.extend(['合計_AI予測', f'合計_{get_plan_name(plan_col)}'])
    
    for abc in abc_categories:
        columns.extend([f'{abc}区分_AI予測', f'{abc}区分_{get_plan_name(plan_col)}'])
    
    # データフレーム初期化
    matrix_data = []
    
    # 各誤差率帯の集計
    for i, band_original in enumerate(error_bands_original):
        band_display = error_bands_display[i]
        row = {'誤差率帯': band_display}
        
        # 合計（AI予測／計画）
        ai_count = len(ai_errors[ai_errors['error_category'] == band_original])
        plan_count = len(plan_errors[plan_errors['error_category'] == band_original])
        row['合計_AI予測'] = ai_count
        row[f'合計_{get_plan_name(plan_col)}'] = plan_count
        
        # ABC区分別
        for abc in abc_categories:
            if 'Class_abc' in ai_errors.columns:
                ai_abc_count = len(ai_errors[(ai_errors['error_category'] == band_original) & (ai_errors['Class_abc'] == abc)])
                plan_abc_count = len(plan_errors[(plan_errors['error_category'] == band_original) & (plan_errors['Class_abc'] == abc)])
                row[f'{abc}区分_AI予測'] = ai_abc_count
                row[f'{abc}区分_{get_plan_name(plan_col)}'] = plan_abc_count
            else:
                row[f'{abc}区分_AI予測'] = 0
                row[f'{abc}区分_{get_plan_name(plan_col)}'] = 0
        
        matrix_data.append(row)
    
    # 合計行の追加
    total_row = {'誤差率帯': '合計（件数）'}
    total_row['合計_AI予測'] = len(ai_errors)
    total_row[f'合計_{get_plan_name(plan_col)}'] = len(plan_errors)
    
    for abc in abc_categories:
        if 'Class_abc' in ai_errors.columns:
            ai_abc_total = len(ai_errors[ai_errors['Class_abc'] == abc])
            plan_abc_total = len(plan_errors[plan_errors['Class_abc'] == abc])
            total_row[f'{abc}区分_AI予測'] = ai_abc_total
            total_row[f'{abc}区分_{get_plan_name(plan_col)}'] = plan_abc_total
        else:
            total_row[f'{abc}区分_AI予測'] = 0
            total_row[f'{abc}区分_{get_plan_name(plan_col)}'] = 0
    
    matrix_data.append(total_row)
    
    # 加重平均誤差率行の追加（文字列として直接保存）
    weighted_avg_row = {'誤差率帯': '加重平均誤差率（%）'}
    
    # 全体の加重平均（直接%文字列として保存）
    ai_weighted_avg = calculate_weighted_average_error_rate(ai_errors, error_col, 'Actual') * 100
    plan_weighted_avg = calculate_weighted_average_error_rate(plan_errors, error_col, 'Actual') * 100
    weighted_avg_row['合計_AI予測'] = f"{ai_weighted_avg:.1f}%" if not pd.isna(ai_weighted_avg) else "N/A"
    weighted_avg_row[f'合計_{get_plan_name(plan_col)}'] = f"{plan_weighted_avg:.1f}%" if not pd.isna(plan_weighted_avg) else "N/A"
    
    # ABC区分別の加重平均（直接%文字列として保存）
    for abc in abc_categories:
        if 'Class_abc' in ai_errors.columns:
            ai_abc_data = ai_errors[ai_errors['Class_abc'] == abc]
            plan_abc_data = plan_errors[plan_errors['Class_abc'] == abc]
            
            ai_abc_weighted = calculate_weighted_average_error_rate(ai_abc_data, error_col, 'Actual') * 100
            plan_abc_weighted = calculate_weighted_average_error_rate(plan_abc_data, error_col, 'Actual') * 100
            
            weighted_avg_row[f'{abc}区分_AI予測'] = f"{ai_abc_weighted:.1f}%" if not pd.isna(ai_abc_weighted) else "N/A"
            weighted_avg_row[f'{abc}区分_{get_plan_name(plan_col)}'] = f"{plan_abc_weighted:.1f}%" if not pd.isna(plan_abc_weighted) else "N/A"
        else:
            weighted_avg_row[f'{abc}区分_AI予測'] = "N/A"
            weighted_avg_row[f'{abc}区分_{get_plan_name(plan_col)}'] = "N/A"
    
    matrix_data.append(weighted_avg_row)
    
    # データフレーム作成
    matrix_df = pd.DataFrame(matrix_data, columns=columns)
    
    return matrix_df

def get_plan_name(plan_col):
    """計画カラム名を表示用に変換"""
    return '計画01' if plan_col == 'Plan_01' else '計画02'

def get_error_rate_definition(error_type):
    """誤差率タイプに応じた定義文を取得"""
    definitions = {
        'absolute': '|計画値 - 実績値| ÷ 実績値',
        'positive': '(計画値 - 実績値) ÷ 実績値（計画 > 実績時のみ）',
        'negative': '(計画値 - 実績値) ÷ 実績値（計画 < 実績時のみ）'
    }
    return definitions.get(error_type, '|計画値 - 実績値| ÷ 実績値')

def get_error_rate_bands_with_signs(error_type):
    """誤差率タイプに応じた誤差率帯ラベルを取得"""
    from config.settings import ERROR_RATE_CATEGORIES
    
    bands = []
    for category in ERROR_RATE_CATEGORIES:
        if 'special' in category:
            bands.append(category['label'])
        else:
            label = category['label']
            if error_type == 'positive':
                # 正の誤差率の場合は「+」を付ける
                label = '+' + label
            elif error_type == 'negative':
                # 負の誤差率の場合は「-」を付ける
                label = '-' + label
            # 絶対誤差率の場合は符号なし
            bands.append(label)
    
    return bands

def display_styled_matrix(matrix_df, abc_categories):
    """スタイル付きマトリクス表示（HTML方式）"""
    # インデックスを非表示にする
    matrix_display = matrix_df.set_index('誤差率帯')
    
    # 件数を整数表示に変換
    def format_integer_values(df):
        """件数を整数形式でフォーマット"""
        df_formatted = df.copy()
        for idx in df_formatted.index:
            if idx not in ['加重平均誤差率（%）']:  # 加重平均行以外
                for col in df_formatted.columns:
                    val = df_formatted.loc[idx, col]
                    if pd.notna(val) and isinstance(val, (int, float)):
                        df_formatted.loc[idx, col] = int(val)
        return df_formatted
    
    matrix_formatted = format_integer_values(matrix_display)
    
    # 簡素化された凡例表示
    st.markdown("### 📋 カラム凡例")
    st.markdown("🔴 AI予測　🔵 計画01")
    
    # HTMLテーブルを直接生成
    def create_html_table(df):
        """カスタムHTMLテーブル生成"""
        
        # グループ色定義
        group_colors = {
            '合計': '#f8f9fa',
            'A': '#fff3cd', 
            'B': '#d1ecf1',
            'C': '#d4edda'
        }
        
        # HTML開始
        html = """
        <style>
        .custom-matrix-table {
            font-family: Arial, sans-serif;
            border-collapse: collapse;
            width: 100%;
            margin: 20px 0;
        }
        .custom-matrix-table th {
            border: 2px solid #dee2e6;
            padding: 12px;
            text-align: center;
            font-weight: bold;
        }
        .custom-matrix-table td {
            border: 1px solid #dee2e6;
            padding: 10px;
            text-align: center;
        }
        .header-ai { background-color: #FF6B6B; color: white; }
        .header-plan01 { background-color: #4ECDC4; color: white; }
        .header-plan02 { background-color: #45B7D1; color: white; }
        .header-row { background-color: #f8f9fa; }
        .group-total { background-color: #f8f9fa; }
        .group-a { background-color: #fff3cd; }
        .group-b { background-color: #d1ecf1; }
        .group-c { background-color: #d4edda; }
        .border-left { border-left: 4px solid #495057 !important; }
        .bold-row { font-weight: bold; background-color: #e9ecef; }
        .hatching-row { 
            font-weight: bold; 
            background: repeating-linear-gradient(
                45deg,
                #f8f9fa,
                #f8f9fa 10px,
                #e9ecef 10px,
                #e9ecef 20px
            );
        }
        </style>
        <table class="custom-matrix-table">
        """
        
        # ヘッダー行
        html += "<thead><tr><th class='header-row'>誤差率帯</th>"
        
        for col in df.columns:
            css_class = ""
            border_class = ""
            
            # カラムヘッダーの色分け
            if 'AI予測' in col:
                css_class = "header-ai"
            elif '計画01' in col:
                css_class = "header-plan01"
            elif '計画02' in col:
                css_class = "header-plan02"
            
            # グループ境界線
            if 'A区分' in col and col.endswith('_AI予測'):
                border_class = "border-left"
            elif 'B区分' in col and col.endswith('_AI予測'):
                border_class = "border-left"
            elif 'C区分' in col and col.endswith('_AI予測'):
                border_class = "border-left"
            
            html += f"<th class='{css_class} {border_class}'>{col}</th>"
        
        html += "</tr></thead><tbody>"
        
        # データ行
        for idx, row in df.iterrows():
            row_class = ""
            
            # 特別な行のスタイル
            if idx == '合計（件数）':
                row_class = "bold-row"
            elif idx == '加重平均誤差率（%）':
                row_class = "hatching-row"
            
            html += f"<tr class='{row_class}'>"
            html += f"<th class='header-row'>{idx}</th>"
            
            for col_idx, (col, val) in enumerate(row.items()):
                cell_class = ""
                border_class = ""
                
                # グループ背景色
                if '合計' in col:
                    cell_class = "group-total"
                elif 'A区分' in col:
                    cell_class = "group-a"
                elif 'B区分' in col:
                    cell_class = "group-b"
                elif 'C区分' in col:
                    cell_class = "group-c"
                
                # グループ境界線
                if 'A区分' in col and col.endswith('_AI予測'):
                    border_class = "border-left"
                elif 'B区分' in col and col.endswith('_AI予測'):
                    border_class = "border-left"
                elif 'C区分' in col and col.endswith('_AI予測'):
                    border_class = "border-left"
                
                html += f"<td class='{cell_class} {border_class}'>{val}</td>"
            
            html += "</tr>"
        
        html += "</tbody></table>"
        return html
    
    # HTMLテーブル表示
    html_table = create_html_table(matrix_formatted)
    st.markdown(html_table, unsafe_allow_html=True)
    
    # 参考用に通常のDataFrameも表示（デバッグ用）
    with st.expander("📊 データ確認用（通常表示）"):
        st.dataframe(matrix_formatted, use_container_width=True)

def display_basic_statistics(df, filter_settings):
    """基本統計情報表示"""
    st.subheader("📈 基本統計情報")
    
    plan_col = filter_settings['plan_column']
    
    # AI予測と計画値の誤差率計算
    ai_errors = calculate_error_rates(df, 'AI_pred', 'Actual')
    plan_errors = calculate_error_rates(df, plan_col, 'Actual')
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**AI予測の統計**")
        ai_stats = {
            '平均絶対誤差率': f"{ai_errors['absolute_error_rate'].mean()*100:.2f}%",
            '加重平均誤差率': f"{calculate_weighted_average_error_rate(ai_errors, 'absolute_error_rate', 'Actual')*100:.2f}%",
            '対象件数': len(ai_errors),
            '計算不能件数': len(ai_errors[ai_errors['is_actual_zero']])
        }
        for key, value in ai_stats.items():
            st.metric(key, value)
    
    with col2:
        st.markdown(f"**{get_plan_name(plan_col)}の統計**")
        plan_stats = {
            '平均絶対誤差率': f"{plan_errors['absolute_error_rate'].mean()*100:.2f}%",
            '加重平均誤差率': f"{calculate_weighted_average_error_rate(plan_errors, 'absolute_error_rate', 'Actual')*100:.2f}%",
            '対象件数': len(plan_errors),
            '計算不能件数': len(plan_errors[plan_errors['is_actual_zero']])
        }
        for key, value in plan_stats.items():
            st.metric(key, value) 