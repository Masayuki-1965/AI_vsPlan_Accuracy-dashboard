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
        padding: 1rem 1.5rem;
        border-radius: 12px;
        text-align: left;
        margin-bottom: 1rem;
        box-shadow: 0 1px 4px rgba(33, 150, 243, 0.1);
    }

    .section-header-box h2 {
        font-size: 1.9rem;
        margin: 0 0 0.2rem 0;
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
        <h2>■ 誤差率評価マトリクス（誤差率帯 × ABC区分 × 計画種別）</h2>
        <p>このセクションでは、商品コード単位の誤差率を誤差率帯に分類し、ABC区分および計画種別ごとの分布を分類単位でマトリクス形式に可視化します。誤差傾向の把握や、欠品・過剰在庫リスクの分析に活用できます。</p>
    </div>
    """, unsafe_allow_html=True)
    
    # データ確認
    if st.session_state.data is None:
        st.warning("⚠️ データが読み込まれていません。データアップロードページからデータを読み込んでください。")
        return
    
    df = st.session_state.data
    
    try:
        # ② フィルター構成の見直し（「分類」と「期間」のみ）
        filtered_df = apply_filters(df)
        
        if filtered_df.empty:
            st.warning("⚠️ フィルター条件に該当するデータがありません。")
            return
        
        st.info(f"フィルター後データ件数: {len(filtered_df)}件")
        
        # ③ グラフタイトルと補足説明の追加
        st.markdown("""
        <div class="step-title">誤差率評価マトリクス</div>
        """, unsafe_allow_html=True)
        
        st.markdown("""
        <div class="step-annotation">
        マトリクスはすべて商品コード単位で集計されており、誤差率の帯域別に件数を可視化することで、分布傾向と予測精度を把握できます。
        </div>
        """, unsafe_allow_html=True)
        
        # ④ 誤差率タイプフィルターの配置と定義の表示
        error_type_selection = create_error_type_filter()
        
        # ⑤ 誤差率マトリクス表示（すべての計画値・ABC区分を同時表示）
        display_comprehensive_error_rate_matrix(filtered_df, error_type_selection)
        
    except Exception as e:
        st.error(f"エラーが発生しました: {str(e)}")
        st.write("デバッグ情報:")
        st.write(f"データフレームの形状: {df.shape}")
        st.write(f"列名: {list(df.columns)}")

def apply_filters(df):
    """② フィルター設定UI（分類・期間のみ）"""
    # 分類がマッピングされているかどうかを確認
    has_category = 'category_code' in df.columns and not df['category_code'].isna().all()
    
    if has_category:
        # 分類フィルターありの場合
        col1, col2 = st.columns(2)
        
        with col1:
            # 分類フィルター（初期値：全て）
            category_options = ['全て'] + sorted(df['category_code'].dropna().unique().tolist())
            selected_category = st.selectbox(
                "分類",
                category_options,
                key="category_filter"
            )
        
        with col2:
            # 期間フィルター（初期値：全期間）
            if 'Date' in df.columns:
                date_options = ['全期間'] + sorted(df['Date'].dropna().unique().tolist())
                selected_date = st.selectbox(
                    "期間",
                    date_options,
                    key="date_filter"
                )
            else:
                selected_date = '全期間'
        
        # フィルター適用
        filtered_df = df.copy()
        
        if selected_category != '全て':
            filtered_df = filtered_df[filtered_df['category_code'] == selected_category]
        
        if selected_date != '全期間' and 'Date' in df.columns:
            filtered_df = filtered_df[filtered_df['Date'] == selected_date]
    
    else:
        # 分類フィルターなしの場合
        # 期間フィルターのみ
        if 'Date' in df.columns:
            date_options = ['全期間'] + sorted(df['Date'].dropna().unique().tolist())
            selected_date = st.selectbox(
                "期間",
                date_options,
                key="date_filter"
            )
            
            filtered_df = df.copy()
            if selected_date != '全期間':
                filtered_df = filtered_df[filtered_df['Date'] == selected_date]
        else:
            filtered_df = df.copy()
    
    return filtered_df

def create_error_type_filter():
    """④ 誤差率タイプフィルターの作成（定義付き）"""
    # 誤差率タイプの選択肢と定義
    error_types = {
        '絶対誤差率': {
            'value': 'absolute',
            'definition': '|計画値 − 実績値| ÷ 実績値'
        },
        '正の誤差率': {
            'value': 'positive', 
            'definition': '(計画値 − 実績値) ÷ 実績値 ※計画値 ＞ 実績値（過剰在庫リスク）'
        },
        '負の誤差率': {
            'value': 'negative',
            'definition': '(計画値 − 実績値) ÷ 実績値 ※計画値 ＜ 実績値（欠品リスク）'
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
        # 選択された誤差率タイプの定義を横に表示
        st.markdown(f"""
        <div style="
            background: #f8f9fa;
            border-left: 4px solid #17a2b8;
            padding: 0.8rem 1rem;
            margin-top: 1.7rem;
            border-radius: 0 8px 8px 0;
            font-size: 0.9rem;
        ">
            <strong>{selected_error_type}：</strong> {error_types[selected_error_type]['definition']}
        </div>
        """, unsafe_allow_html=True)
    
    return error_types[selected_error_type]['value']

def display_comprehensive_error_rate_matrix(df, error_type):
    """⑤ 包括的誤差率マトリクス表示（段階的復元版）"""
    try:
        # 利用可能な計画値を確認
        plan_columns = ['Plan_01']
        if 'Plan_02' in df.columns:
            plan_columns.append('Plan_02')
        
        # 利用可能なABC区分を確認
        abc_categories = []
        if 'Class_abc' in df.columns:
            abc_values = sorted(df['Class_abc'].dropna().unique().tolist())
            # A, B, C区分を優先的に表示
            priority_categories = ['A', 'B', 'C']
            abc_categories = [cat for cat in priority_categories if cat in abc_values]
            # 他の区分も追加（最大3つまで）
            other_categories = [cat for cat in abc_values if cat not in priority_categories]
            abc_categories.extend(other_categories[:3-len(abc_categories)])
        
        st.write(f"📊 選択された誤差率タイプ: {error_type}")
        st.write(f"📊 データ件数: {len(df)}件")
        st.write(f"📊 計画値: {', '.join(plan_columns)}")
        st.write(f"📊 ABC区分: {', '.join(abc_categories) if abc_categories else 'なし'}")
        
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
    # 誤差率カラム選択
    if error_type == 'absolute':
        error_col = 'absolute_error_rate'
    elif error_type == 'positive':
        error_col = 'positive_error_rate'
    else:  # negative
        error_col = 'negative_error_rate'
    
    # 誤差率区分追加
    error_data['AI_pred']['error_category'] = categorize_error_rates(error_data['AI_pred'], error_col)
    for plan_col in plan_columns:
        error_data[plan_col]['error_category'] = categorize_error_rates(error_data[plan_col], error_col)
    
    # 誤差率帯の順序定義
    error_bands_original = [cat['label'] for cat in ERROR_RATE_CATEGORIES]
    
    # 基本的なマトリクス構造（合計のみ）
    columns = ['AI予測'] + [get_plan_name(plan_col) for plan_col in plan_columns]
    
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
    
    # 合計行の追加
    total_row_data = []
    total_row_data.append(len(error_data['AI_pred']))
    for plan_col in plan_columns:
        total_row_data.append(len(error_data[plan_col]))
    matrix_data.append(total_row_data)
    
    # DataFrame作成（最初から文字列で統一）
    index_labels = error_bands_original + ['合計（件数）']
    
    # 数値データを文字列に変換してからDataFrame作成
    matrix_data_str = []
    for row in matrix_data:
        str_row = [str(int(val)) if isinstance(val, (int, float)) and not pd.isna(val) else str(val) for val in row]
        matrix_data_str.append(str_row)
    
    matrix_df = pd.DataFrame(matrix_data_str, index=index_labels, columns=columns, dtype=str)
    matrix_df.index.name = '誤差率帯'
    
    return matrix_df

def display_basic_matrix(matrix_df):
    """基本的なマトリクス表示"""
    st.write("### 誤差率分布マトリクス（基本版）")
    st.dataframe(
        matrix_df,
        use_container_width=True
    )

def create_advanced_matrix(error_data, error_type, abc_categories, plan_columns):
    """高度なマトリクス作成（ABC区分別対応、2段ヘッダー）"""
    # 誤差率カラム選択
    if error_type == 'absolute':
        error_col = 'absolute_error_rate'
    elif error_type == 'positive':
        error_col = 'positive_error_rate'
    else:  # negative
        error_col = 'negative_error_rate'
    
    # 誤差率区分追加
    error_data['AI_pred']['error_category'] = categorize_error_rates(error_data['AI_pred'], error_col)
    for plan_col in plan_columns:
        error_data[plan_col]['error_category'] = categorize_error_rates(error_data[plan_col], error_col)
    
    # 誤差率帯の順序定義
    error_bands_original = [cat['label'] for cat in ERROR_RATE_CATEGORIES]
    
    # 2段ヘッダーの構造定義
    categories = ['合計'] + [f'{abc}区分' for abc in abc_categories]
    subcategories = ['AI予測'] + [get_plan_name(plan_col) for plan_col in plan_columns]
    
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
    
    # 合計行の追加
    total_row_data = []
    total_row_data.append(len(error_data['AI_pred']))
    
    for plan_col in plan_columns:
        total_row_data.append(len(error_data[plan_col]))
    
    for abc in abc_categories:
        ai_abc_total = len(error_data['AI_pred'][error_data['AI_pred']['Class_abc'] == abc])
        total_row_data.append(ai_abc_total)
        
        for plan_col in plan_columns:
            plan_abc_total = len(error_data[plan_col][error_data[plan_col]['Class_abc'] == abc])
            total_row_data.append(plan_abc_total)
    
    matrix_data.append(total_row_data)
    
    # DataFrame作成（最初から文字列で統一）
    index_labels = error_bands_original + ['合計（件数）']
    
    # 数値データを文字列に変換してからDataFrame作成
    matrix_data_str = []
    for row in matrix_data:
        str_row = [str(int(val)) if isinstance(val, (int, float)) and not pd.isna(val) else str(val) for val in row]
        matrix_data_str.append(str_row)
    
    matrix_df = pd.DataFrame(matrix_data_str, index=index_labels, columns=multi_index, dtype=str)
    matrix_df.index.name = '誤差率帯'
    
    return matrix_df

def display_advanced_matrix(matrix_df, abc_categories, plan_columns):
    """高度なマトリクス表示（2段ヘッダー対応）"""
    st.write("### 誤差率分布マトリクス（ABC区分別）")
    
    # データは既に文字列形式なので、そのまま表示
    st.dataframe(
        matrix_df,
        use_container_width=True
    )

def get_plan_name(plan_col):
    """計画カラム名を表示用に変換"""
    if plan_col == 'Plan_01':
        return '計画01'
    elif plan_col == 'Plan_02':
        return '計画02'
    else:
        return plan_col 