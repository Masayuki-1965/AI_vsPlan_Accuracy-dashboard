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
    """誤差率帯別マトリクスページを表示"""
    # CSSスタイル（散布図分析と同様）の適用
    st.markdown("""
    <style>
    /* STEP注釈・説明文 */
    .step-annotation {
        color: #666666;
        font-size: 0.95em;
        margin-bottom: 1.2em;
    }

    /* 大項目セクションボックス（STEPスタイル統一） */
    .section-header-box {
        background: #e8f4fd;
        color: #1976d2;
        padding: 0.8rem 1.2rem;
        border-radius: 12px;
        text-align: left;
        margin-bottom: 0.8rem;
        box-shadow: 0 1px 4px rgba(33, 150, 243, 0.1);
    }

    .section-header-box h2 {
        font-size: 1.9rem;
        margin: 0 0 0.1rem 0;
        font-weight: 600;
        color: #1976d2;
    }

    .section-header-box p {
        font-size: 1.05rem;
        margin: 0;
        color: #4a90e2;
        line-height: 1.6;
    }

    /* STEP見出し（青線付きタイトル） */
    .step-title {
        font-size: 1.4em;
        font-weight: bold;
        color: #1976d2;
        border-left: 4px solid #1976d2;
        padding-left: 12px;
        margin-bottom: 1em;
        margin-top: 2em;
    }
    
    /* 誤差率定義の表示スタイル */
    .error-rate-definition {
        background: #f8f9fa;
        border-left: 4px solid #17a2b8;
        padding: 1rem;
        margin: 1rem 0;
        border-radius: 0 8px 8px 0;
    }
    
    .error-rate-definition h4 {
        color: #17a2b8;
        margin-bottom: 0.5rem;
    }
    
    .error-rate-definition ul {
        margin-bottom: 0;
    }
    
    .error-rate-definition li {
        margin-bottom: 0.3rem;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # ① セクション名のデザイン統一
    st.markdown("""
    <div class="section-header-box">
        <h2>■ 誤差率マトリクス分析（誤差率帯×ABC区分）</h2>
        <p>このセクションでは、AI予測値、計画値（複数可）の誤差率を6段階の誤差率帯（0～10%、10～20% … 100%以上）に分類し、誤差率帯 × ABC区分のマトリクス形式で集計・可視化します。誤差率タイプは「絶対誤差率」「正の誤差率」「負の誤差率」から選択可能で、誤差傾向の把握や欠品・過剰在庫リスクの分析に活用できます。</p>
    </div>
    """, unsafe_allow_html=True)
    
    # データ確認
    if st.session_state.data is None:
        st.markdown("""
        <div style="
            background: #e8f4fd;
            color: #1976d2;
            padding: 1rem 1.5rem;
            border-radius: 12px;
            margin-bottom: 1rem;
            font-size: 1.05rem;
            line-height: 1.6;
        ">
            データセットのセクションで、分析用のデータセットを作成してください。
        </div>
        """, unsafe_allow_html=True)
        return
    
    df = st.session_state.data
    
    try:
        # ② フィルター構成の見直し（「分類」と「期間」のみ）
        filtered_df = apply_filters(df)
        
        if filtered_df.empty:
            st.warning("⚠️ フィルター条件に該当するデータがありません。")
            return
        

        
        # ③ グラフタイトルと補足説明の追加
        st.markdown("""
        <div class="step-title">誤差率帯 × ABC区分別マトリクス（AI予測値 vs 計画値）</div>
        """, unsafe_allow_html=True)
        
        st.markdown("""
        <div class="step-annotation">
        誤差率タイプは「絶対誤差率」「正の誤差率」「負の誤差率」から選択してください。
        </div>
        """, unsafe_allow_html=True)
        
        # ④ 誤差率タイプフィルターの配置と定義の表示
        error_type_selection = create_error_type_filter()
        
        # ⑤ 誤差率帯別マトリクス表示（すべての計画値・ABC区分を同時表示）
        display_comprehensive_error_rate_matrix(filtered_df, error_type_selection)
        
    except Exception as e:
        st.error(f"エラーが発生しました: {str(e)}")
        st.write("デバッグ情報:")
        st.write(f"データフレームの形状: {df.shape}")
        st.write(f"列名: {list(df.columns)}")

def apply_filters(df):
    """② フィルター設定UI（分類・期間・評価方法）"""
    from utils.common_helpers import get_enhanced_date_options, parse_date_filter_selection, get_evaluation_method_options, aggregate_data_for_cumulative_evaluation, is_single_month_selection, get_default_date_selection, get_period_filter_help_text, initialize_filter_session_state
    
    # フィルター設定のセッション状態を初期化（保持機能強化）
    initialize_filter_session_state()
    
    # 分類がマッピングされているかどうかを確認
    has_category = 'category_code' in df.columns and not df['category_code'].isna().all()
    
    if has_category:
        # 分類フィルターありの場合
        col1, col2, col3 = st.columns(3)
        
        with col1:
            # 分類フィルター（初期値：全て）
            category_options = ['全て'] + sorted(df['category_code'].dropna().unique().tolist())
            selected_category = st.selectbox(
                "分類",
                category_options,
                key="category_filter"
            )
        
        with col2:
            # 拡張された期間フィルター（デフォルト値・ヘルプテキスト付き）
            if 'Date' in df.columns:
                date_options = get_enhanced_date_options(df)
                default_date = get_default_date_selection(df)
                default_index = date_options.index(default_date) if default_date in date_options else 0
                
                selected_date = st.selectbox(
                    "期間",
                    date_options,
                    index=default_index,
                    key="date_filter",
                    help=get_period_filter_help_text()
                )
            else:
                selected_date = '全期間'
        
        with col3:
            # 単月選択時は評価方法を無効化
            is_single_month = is_single_month_selection(selected_date, df)
            
            if is_single_month:
                st.selectbox(
                    "評価方法",
                    ["単月データ評価"],
                    disabled=True,
                    key="evaluation_method",
                    help="単月選択時は単月データ評価のみ利用可能です"
                )
                selected_evaluation = "単月データ評価"
            else:
                # 評価方法の選択（デフォルト：単月データ評価）
                evaluation_options = get_evaluation_method_options()
                selected_evaluation = st.selectbox(
                    "評価方法",
                    evaluation_options,
                    index=0,  # デフォルト：単月データ評価
                    key="evaluation_method"
                )
    else:
        # 分類フィルターなしの場合
        col1, col2 = st.columns(2)
        
        with col1:
            # 拡張された期間フィルター（デフォルト値・ヘルプテキスト付き）
            if 'Date' in df.columns:
                date_options = get_enhanced_date_options(df)
                default_date = get_default_date_selection(df)
                default_index = date_options.index(default_date) if default_date in date_options else 0
                
                selected_date = st.selectbox(
                    "期間",
                    date_options,
                    index=default_index,
                    key="date_filter",
                    help=get_period_filter_help_text()
                )
            else:
                selected_date = '全期間'
        
        with col2:
            # 単月選択時は評価方法を無効化
            is_single_month = is_single_month_selection(selected_date, df)
            
            if is_single_month:
                st.selectbox(
                    "評価方法",
                    ["単月データ評価"],
                    disabled=True,
                    key="evaluation_method",
                    help="単月選択時は単月データ評価のみ利用可能です"
                )
                selected_evaluation = "単月データ評価"
            else:
                # 評価方法の選択（デフォルト：単月データ評価）
                evaluation_options = get_evaluation_method_options()
                selected_evaluation = st.selectbox(
                    "評価方法",
                    evaluation_options,
                    index=0,  # デフォルト：単月データ評価
                    key="evaluation_method"
                )
        
        selected_category = '全て'
    
    # フィルター適用
    filtered_df = df.copy()
    
    # 分類フィルター適用
    if selected_category != '全て':
        filtered_df = filtered_df[filtered_df['category_code'] == selected_category]
    
    # 評価方法に応じた処理
    if selected_evaluation == "累積データ評価（選択期間で集計）":
        # 累積データ評価の場合
        filtered_df = aggregate_data_for_cumulative_evaluation(filtered_df, selected_date)
    else:
        # 単月データ評価の場合（従来通り）
        filtered_df = parse_date_filter_selection(selected_date, filtered_df)
    
    return filtered_df

def create_error_type_filter():
    """④ 誤差率タイプフィルターの作成（定義付き）"""
    # 誤差率タイプの選択肢と定義
    error_types = {
        '絶対誤差率': {
            'value': 'absolute',
            'definition': '｜計画値 − 実績値｜ ÷ 実績値'
        },
        '正の誤差率': {
            'value': 'positive', 
            'definition': '（計画値 − 実績値）÷ 実績値　※計画値 ＞ 実績値（過剰在庫リスク）'
        },
        '負の誤差率': {
            'value': 'negative',
            'definition': '（計画値 − 実績値）÷ 実績値　※計画値 ＜ 実績値（欠品リスク）'
        }
    }
    
    # B案：フィルターの横幅を縮小し、空いたスペースに定義を表示
    col1, col2 = st.columns([1, 3])
    
    with col1:
        selected_error_type = st.selectbox(
            "誤差率タイプ",
            list(error_types.keys()),
            key="error_type_selector"
        )
    
    with col2:
        # 選択された誤差率タイプの定義をシンプルに表示
        st.markdown(f"""
        <div style="
            padding: 0.8rem 1rem;
            margin-top: 1.7rem;
            font-size: 0.9rem;
        ">
            <strong>{selected_error_type}の定義式：</strong> {error_types[selected_error_type]['definition']}
        </div>
        """, unsafe_allow_html=True)
    
    return error_types[selected_error_type]['value']

def display_comprehensive_error_rate_matrix(df, error_type):
    """⑤ 包括的誤差率帯別マトリクス表示（段階的復元版）"""
    try:
        # 利用可能な計画値を確認
        plan_columns = ['Plan_01']
        if 'Plan_02' in df.columns:
            plan_columns.append('Plan_02')
        
        # 利用可能なABC区分を確認（⑥ ABC区分の拡張表示）
        abc_categories = []
        if 'Class_abc' in df.columns:
            abc_values = sorted(df['Class_abc'].dropna().unique().tolist())
            # A, B, C区分を優先的に表示
            priority_categories = ['A', 'B', 'C']
            abc_categories = [cat for cat in priority_categories if cat in abc_values]
            # D区分、E区分なども全て表示
            other_categories = [cat for cat in abc_values if cat not in priority_categories]
            abc_categories.extend(other_categories)
        

        
        # AI予測と各計画値の誤差率計算
        error_data = {}
        error_data['AI_pred'] = calculate_error_rates(df, 'AI_pred', 'Actual')
        
        for plan_col in plan_columns:
            error_data[plan_col] = calculate_error_rates(df, plan_col, 'Actual')
        
        # マトリクス作成（ABC区分別対応）
        if abc_categories:
            matrix_df = create_advanced_matrix(error_data, error_type, abc_categories, plan_columns)
            display_advanced_matrix(matrix_df, abc_categories, plan_columns)
        else:
            matrix_df = create_basic_matrix(error_data, error_type, abc_categories, plan_columns)
            display_basic_matrix(matrix_df)
        
    except Exception as e:
        st.error(f"マトリクス表示でエラーが発生しました: {str(e)}")
        import traceback
        st.code(traceback.format_exc())

def create_basic_matrix(error_data, error_type, abc_categories, plan_columns):
    """基本的なマトリクス作成（段階的復元）"""
    from utils.error_calculator import categorize_error_rates, calculate_weighted_average_error_rate
    
    # 誤差率カラム選択
    if error_type == 'absolute':
        error_col = 'absolute_error_rate'
    elif error_type == 'positive':
        error_col = 'positive_error_rate'
    else:  # negative
        error_col = 'negative_error_rate'
    
    # 誤差率区分追加
    error_data['AI_pred']['error_category'] = categorize_error_rates(error_data['AI_pred'], error_col, error_type)
    for plan_col in plan_columns:
        error_data[plan_col]['error_category'] = categorize_error_rates(error_data[plan_col], error_col, error_type)
    
    # 誤差率帯の順序定義
    error_bands_original = [cat['label'] for cat in ERROR_RATE_CATEGORIES[error_type]]
    
    # 基本的なマトリクス構造（合計のみ）
    columns = [get_plan_name('AI_pred')] + [get_plan_name(plan_col) for plan_col in plan_columns]
    
    # データフレーム初期化
    matrix_data = []
    
    # 各誤差率帯の集計
    for band_original in error_bands_original:
        row_data = []
        
        # AI予測の件数
        ai_count = len(error_data['AI_pred'][error_data['AI_pred']['error_category'] == band_original])
        row_data.append(ai_count)
        
        # 各計画値の件数
        for plan_col in plan_columns:
            plan_count = len(error_data[plan_col][error_data[plan_col]['error_category'] == band_original])
            row_data.append(plan_count)
        
        matrix_data.append(row_data)
    
    # 合計行の追加（誤差率タイプに応じた実際の対象データ数）
    total_row_data = []
    
    # AI予測の対象データ数（誤差率タイプごとに適切に計算）
    if error_type == 'absolute':
        # 絶対誤差率：全データを対象
        ai_valid_count = len(error_data['AI_pred'])
    else:
        # 正・負の誤差率：該当する誤差率列でNaNでないデータを対象
        ai_valid_count = len(error_data['AI_pred'][error_data['AI_pred'][error_col].notna()])
    total_row_data.append(ai_valid_count)
    
    for plan_col in plan_columns:
        if error_type == 'absolute':
            plan_valid_count = len(error_data[plan_col])
        else:
            plan_valid_count = len(error_data[plan_col][error_data[plan_col][error_col].notna()])
        total_row_data.append(plan_valid_count)
    
    matrix_data.append(total_row_data)
    
    # 加重平均誤差率行の追加
    weighted_avg_row_data = []
    
    # AI予測の加重平均誤差率
    ai_weighted_avg = calculate_weighted_average_error_rate(error_data['AI_pred'], error_col, 'Actual')
    ai_weighted_avg_str = format_weighted_average(ai_weighted_avg, error_type)
    weighted_avg_row_data.append(ai_weighted_avg_str)
    
    # 各計画値の加重平均誤差率
    for plan_col in plan_columns:
        plan_weighted_avg = calculate_weighted_average_error_rate(error_data[plan_col], error_col, 'Actual')
        plan_weighted_avg_str = format_weighted_average(plan_weighted_avg, error_type)
        weighted_avg_row_data.append(plan_weighted_avg_str)
    
    matrix_data.append(weighted_avg_row_data)
    
    # DataFrame作成（最初から文字列で統一）
    index_labels = error_bands_original + ['合計件数', '加重平均誤差率']
    
    # 数値データを文字列に変換してからDataFrame作成
    matrix_data_str = []
    for i, row in enumerate(matrix_data):
        if i < len(matrix_data) - 1:  # 加重平均行以外
            str_row = [str(int(val)) if isinstance(val, (int, float)) and not pd.isna(val) else str(val) for val in row]
        else:  # 加重平均行はそのまま
            str_row = row
        matrix_data_str.append(str_row)
    
    matrix_df = pd.DataFrame(matrix_data_str, index=index_labels, columns=columns, dtype=str)
    matrix_df.index.name = '誤差率帯'
    
    return matrix_df

def display_basic_matrix(matrix_df):
    """基本的なマトリクス表示（比較対象数に応じた動的幅調整）"""
    # 比較対象の数をカラム数から推定
    num_predictions = len(matrix_df.columns)
    
    # 比較対象数に応じた動的CSS設定
    if num_predictions == 2:
        # 2つの比較対象の場合：列幅を広く取る
        prediction_column_width = 45.0  # 各予測列の幅
    else:
        # 3つ以上の比較対象の場合：従来通り
        prediction_column_width = 30.0
    
    # 動的CSS生成（基本マトリクス専用のユニークなクラス名を使用）
    matrix_id = f"basic_matrix_{num_predictions}"
    dynamic_css = f"""
    <style>
    .{matrix_id} .stDataFrame > div {{
        width: 100%;
    }}
    .{matrix_id} .stDataFrame table {{
        width: 100% !important;
        table-layout: fixed !important;
    }}
    .{matrix_id} .stDataFrame th, .{matrix_id} .stDataFrame td {{
        text-align: center !important;
        word-wrap: break-word !important;
        white-space: nowrap !important;
        overflow: hidden !important;
        text-overflow: ellipsis !important;
    }}
         /* 誤差率帯列の幅を確保 */
     .{matrix_id} .stDataFrame th:first-child, .{matrix_id} .stDataFrame td:first-child {{
         width: 140px !important;
         min-width: 140px !important;
         max-width: 140px !important;
     }}
    /* 予測・計画値の列 */
    .{matrix_id} .stDataFrame th:nth-child(n+2), .{matrix_id} .stDataFrame td:nth-child(n+2) {{
        width: {prediction_column_width}% !important;
        min-width: 80px !important;
    }}
    </style>
    """
    st.markdown(dynamic_css, unsafe_allow_html=True)
    
    # ユニークなクラス名を適用したコンテナでテーブルを表示
    with st.container():
        st.markdown(f'<div class="{matrix_id}">', unsafe_allow_html=True)
        
        # Streamlitの列設定を使用してカラム幅を明示的に指定
        column_config = {}
        
        # インデックス列（誤差率帯）の設定
        if matrix_df.index.name:
            column_config[matrix_df.index.name] = st.column_config.TextColumn(
                matrix_df.index.name,
                width=140,
                help="誤差率の帯域"
            )
        
        st.dataframe(
            matrix_df,
            use_container_width=True,
            column_config=column_config
        )
        st.markdown('</div>', unsafe_allow_html=True)
    
    # ③ 注釈の追加
    st.markdown("""
    <div style="margin-top: 1rem; font-size: 0.9rem; color: #666;">
    ※ マトリクス内の数値は、該当する商品コードの件数を表します。<br>
    ※ 誤差率0％（完全一致）の件数は、「絶対誤差率」と「正の誤差率」に含まれます。「負の誤差率」には含まれません。<br>
    ※ 実績値が0の場合、誤差率が計算できないため「計算不能 (実績0)」に分類されます。<br>
    ※ 整合式：絶対誤差率の合計件数 ＝ 正の誤差率の合計件数 ＋ 負の誤差率の合計件数
    ※ 加重平均誤差率は、実績値で重みづけした加重平均値です。
    </div>
    """, unsafe_allow_html=True)

def create_advanced_matrix(error_data, error_type, abc_categories, plan_columns):
    """高度なマトリクス作成（ABC区分別対応、2段ヘッダー）"""
    from utils.error_calculator import categorize_error_rates, calculate_weighted_average_error_rate
    
    # 誤差率カラム選択
    if error_type == 'absolute':
        error_col = 'absolute_error_rate'
    elif error_type == 'positive':
        error_col = 'positive_error_rate'
    else:  # negative
        error_col = 'negative_error_rate'
    
    # 誤差率区分追加
    error_data['AI_pred']['error_category'] = categorize_error_rates(error_data['AI_pred'], error_col, error_type)
    for plan_col in plan_columns:
        error_data[plan_col]['error_category'] = categorize_error_rates(error_data[plan_col], error_col, error_type)
    
    # 誤差率帯の順序定義
    error_bands_original = [cat['label'] for cat in ERROR_RATE_CATEGORIES[error_type]]
    
    # 2段ヘッダーの構造定義
    categories = ['合計'] + [f'{abc}区分' for abc in abc_categories]
    subcategories = [get_plan_name('AI_pred')] + [get_plan_name(plan_col) for plan_col in plan_columns]
    
    # MultiIndex作成
    columns_tuples = []
    for category in categories:
        for subcategory in subcategories:
            columns_tuples.append((category, subcategory))
    
    multi_index = pd.MultiIndex.from_tuples(columns_tuples, names=['区分', '予測タイプ'])
    
    # データフレーム初期化
    matrix_data = []
    
    # 各誤差率帯の集計
    for band_original in error_bands_original:
        row_data = []
        
        # 合計（AI予測／計画）
        ai_count = len(error_data['AI_pred'][error_data['AI_pred']['error_category'] == band_original])
        row_data.append(ai_count)
        
        for plan_col in plan_columns:
            plan_count = len(error_data[plan_col][error_data[plan_col]['error_category'] == band_original])
            row_data.append(plan_count)
        
        # ABC区分別
        for abc in abc_categories:
            # AI予測
            ai_abc_count = len(error_data['AI_pred'][
                (error_data['AI_pred']['error_category'] == band_original) & 
                (error_data['AI_pred']['Class_abc'] == abc)
            ])
            row_data.append(ai_abc_count)
            
            # 各計画値
            for plan_col in plan_columns:
                plan_abc_count = len(error_data[plan_col][
                    (error_data[plan_col]['error_category'] == band_original) & 
                    (error_data[plan_col]['Class_abc'] == abc)
                ])
                row_data.append(plan_abc_count)
        
        matrix_data.append(row_data)
    
    # 合計行の追加（誤差率タイプに応じた実際の対象データ数）
    total_row_data = []
    
    # AI予測の対象データ数（誤差率タイプごとに適切に計算）
    if error_type == 'absolute':
        # 絶対誤差率：全データを対象
        ai_valid_count = len(error_data['AI_pred'])
    else:
        # 正・負の誤差率：該当する誤差率列でNaNでないデータを対象
        ai_valid_count = len(error_data['AI_pred'][error_data['AI_pred'][error_col].notna()])
    total_row_data.append(ai_valid_count)
    
    for plan_col in plan_columns:
        if error_type == 'absolute':
            plan_valid_count = len(error_data[plan_col])
        else:
            plan_valid_count = len(error_data[plan_col][error_data[plan_col][error_col].notna()])
        total_row_data.append(plan_valid_count)
    
    for abc in abc_categories:
        # AI予測のABC区分別対象データ数
        if error_type == 'absolute':
            ai_abc_valid_count = len(error_data['AI_pred'][error_data['AI_pred']['Class_abc'] == abc])
        else:
            ai_abc_valid_count = len(error_data['AI_pred'][
                (error_data['AI_pred'][error_col].notna()) & 
                (error_data['AI_pred']['Class_abc'] == abc)
            ])
        total_row_data.append(ai_abc_valid_count)
        
        for plan_col in plan_columns:
            if error_type == 'absolute':
                plan_abc_valid_count = len(error_data[plan_col][error_data[plan_col]['Class_abc'] == abc])
            else:
                plan_abc_valid_count = len(error_data[plan_col][
                    (error_data[plan_col][error_col].notna()) & 
                    (error_data[plan_col]['Class_abc'] == abc)
                ])
            total_row_data.append(plan_abc_valid_count)
    
    matrix_data.append(total_row_data)
    
    # 加重平均誤差率行の追加
    weighted_avg_row_data = []
    
    # 合計の加重平均誤差率
    ai_weighted_avg = calculate_weighted_average_error_rate(error_data['AI_pred'], error_col, 'Actual')
    ai_weighted_avg_str = format_weighted_average(ai_weighted_avg, error_type)
    weighted_avg_row_data.append(ai_weighted_avg_str)
    
    for plan_col in plan_columns:
        plan_weighted_avg = calculate_weighted_average_error_rate(error_data[plan_col], error_col, 'Actual')
        plan_weighted_avg_str = format_weighted_average(plan_weighted_avg, error_type)
        weighted_avg_row_data.append(plan_weighted_avg_str)
    
    # ABC区分別の加重平均誤差率
    for abc in abc_categories:
        # AI予測のABC区分別加重平均
        ai_abc_data = error_data['AI_pred'][error_data['AI_pred']['Class_abc'] == abc]
        ai_abc_weighted_avg = calculate_weighted_average_error_rate(ai_abc_data, error_col, 'Actual')
        ai_abc_weighted_avg_str = format_weighted_average(ai_abc_weighted_avg, error_type)
        weighted_avg_row_data.append(ai_abc_weighted_avg_str)
        
        # 各計画値のABC区分別加重平均
        for plan_col in plan_columns:
            plan_abc_data = error_data[plan_col][error_data[plan_col]['Class_abc'] == abc]
            plan_abc_weighted_avg = calculate_weighted_average_error_rate(plan_abc_data, error_col, 'Actual')
            plan_abc_weighted_avg_str = format_weighted_average(plan_abc_weighted_avg, error_type)
            weighted_avg_row_data.append(plan_abc_weighted_avg_str)
    
    matrix_data.append(weighted_avg_row_data)
    
    # DataFrame作成（最初から文字列で統一）
    index_labels = error_bands_original + ['合計件数', '加重平均誤差率']
    
    # 数値データを文字列に変換してからDataFrame作成
    matrix_data_str = []
    for i, row in enumerate(matrix_data):
        if i < len(matrix_data) - 1:  # 加重平均行以外
            str_row = [str(int(val)) if isinstance(val, (int, float)) and not pd.isna(val) else str(val) for val in row]
        else:  # 加重平均行はそのまま
            str_row = row
        matrix_data_str.append(str_row)
    
    matrix_df = pd.DataFrame(matrix_data_str, index=index_labels, columns=multi_index, dtype=str)
    matrix_df.index.name = '誤差率帯'
    
    return matrix_df

def display_advanced_matrix(matrix_df, abc_categories, plan_columns):
    """高度なマトリクス表示（2段ヘッダー対応、比較対象数に応じた動的幅調整）"""
    # 比較対象の数（AI予測 + 計画値）
    num_predictions = len(plan_columns) + 1  # +1はAI予測分
    
    # 比較対象数に応じた動的CSS設定
    if num_predictions == 2:
        # 2つの比較対象の場合：列幅を広く取る
        prediction_column_width = 18.0  # 各予測列の幅
        base_column_width = 12.0       # 基本列（区分、件数、実績合計）の幅
    else:
        # 3つ以上の比較対象の場合：従来通り
        prediction_column_width = 12.67
        base_column_width = 8.0
    
    # 動的CSS生成（マトリクス専用のユニークなクラス名を使用）
    matrix_id = f"matrix_{num_predictions}_{len(abc_categories)}"
    dynamic_css = f"""
    <style>
    .{matrix_id} .stDataFrame > div {{
        width: 100%;
    }}
    .{matrix_id} .stDataFrame table {{
        width: 100% !important;
        table-layout: fixed !important;
    }}
    .{matrix_id} .stDataFrame th, .{matrix_id} .stDataFrame td {{
        text-align: center !important;
        word-wrap: break-word !important;
        white-space: nowrap !important;
        overflow: hidden !important;
        text-overflow: ellipsis !important;
    }}
         /* 誤差率帯列の幅を確保 */
     .{matrix_id} .stDataFrame th:first-child, .{matrix_id} .stDataFrame td:first-child {{
         width: 140px !important;
         min-width: 140px !important;
         max-width: 140px !important;
     }}
    /* 区分列 */
    .{matrix_id} .stDataFrame th:nth-child(2), .{matrix_id} .stDataFrame td:nth-child(2) {{
        width: {base_column_width}% !important;
        min-width: 60px !important;
    }}
    /* 件数列 */
    .{matrix_id} .stDataFrame th:nth-child(3), .{matrix_id} .stDataFrame td:nth-child(3) {{
        width: {base_column_width}% !important;
        min-width: 60px !important;
    }}
    /* 実績合計列 */
    .{matrix_id} .stDataFrame th:nth-child(4), .{matrix_id} .stDataFrame td:nth-child(4) {{
        width: {base_column_width}% !important;
        min-width: 60px !important;
    }}
    /* 予測・計画値の列 */
    .{matrix_id} .stDataFrame th:nth-child(n+5), .{matrix_id} .stDataFrame td:nth-child(n+5) {{
        width: {prediction_column_width}% !important;
        min-width: 80px !important;
    }}
    /* 1行目のヘッダー（MultiIndexの最上位レベル）を非表示 */
    .{matrix_id} .stDataFrame thead tr:first-child {{
        display: none;
    }}
    /* 左側3列の1行目ヘッダーの境界線も非表示 */
    .{matrix_id} .stDataFrame thead tr:first-child th:nth-child(1),
    .{matrix_id} .stDataFrame thead tr:first-child th:nth-child(2),
    .{matrix_id} .stDataFrame thead tr:first-child th:nth-child(3) {{
        border-bottom: none !important;
    }}
    </style>
    """
    st.markdown(dynamic_css, unsafe_allow_html=True)
    
    # ユニークなクラス名を適用したコンテナでテーブルを表示
    with st.container():
        st.markdown(f'<div class="{matrix_id}">', unsafe_allow_html=True)
        
        # Streamlitの列設定を使用してカラム幅を明示的に指定
        column_config = {}
        
        # インデックス列（誤差率帯）の設定
        if matrix_df.index.name:
            column_config[matrix_df.index.name] = st.column_config.TextColumn(
                matrix_df.index.name,
                width=140,
                help="誤差率の帯域"
            )
        
        st.dataframe(
            matrix_df,
            use_container_width=True,
            column_config=column_config
        )
        st.markdown('</div>', unsafe_allow_html=True)
    
    # ③ 注釈の追加
    st.markdown("""
    <div style="margin-top: 1rem; font-size: 0.9rem; color: #666;">
    ※ マトリクス内の数値は、該当する商品コードの件数を表します。<br>
    ※ 誤差率0％（完全一致）の件数は、「絶対誤差率」と「正の誤差率」に含まれます。「負の誤差率」には含まれません。<br>
    ※ 実績値が0の場合、誤差率が計算できないため「計算不能 (実績0)」に分類されます。<br>
    ※ 整合式：絶対誤差率の合計件数 ＝ 正の誤差率の合計件数 ＋ 負の誤差率の合計件数
    ※ 加重平均誤差率は、実績値で重みづけした加重平均値です。
    </div>
    """, unsafe_allow_html=True)

def get_plan_name(plan_col):
    """計画カラム名を表示用に変換（カスタム項目名対応・省略表示対応）"""
    # カスタム項目名があるかチェック
    if 'custom_column_names' in st.session_state and plan_col in st.session_state.custom_column_names:
        custom_name = st.session_state.custom_column_names[plan_col].strip()
        if custom_name:
            # 全角6文字を超える場合は省略
            if len(custom_name) > 6:
                return custom_name[:6] + '…'
            else:
                return custom_name
    
    # デフォルト名を設定
    if plan_col == 'Plan_01':
        display_name = '計画01'
    elif plan_col == 'Plan_02':
        display_name = '計画02'
    elif plan_col == 'AI_pred':
        display_name = 'AI予測'
    else:
        display_name = plan_col
    
    # デフォルト名も6文字チェック
    if len(display_name) > 6:
        return display_name[:6] + '…'
    return display_name

def format_weighted_average(weighted_avg, error_type):
    """加重平均誤差率のフォーマット（小数第1位統一・負の誤差率表記統一）"""
    if pd.isna(weighted_avg):
        return '-'
    
    # パーセント表示に変換
    percentage = weighted_avg * 100
    
    # 誤差率タイプに応じた記号付け（小数第1位統一）
    if error_type == 'positive':
        return f"＋{percentage:.1f}%"
    elif error_type == 'negative':
        return f"▲{abs(percentage):.1f}%"  # 負の値を正の値に変換してから▲記号を付ける
    else:  # absolute
        return f"{percentage:.1f}%" 