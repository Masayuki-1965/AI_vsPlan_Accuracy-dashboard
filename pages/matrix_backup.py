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
        <h2>📊 誤差率評価マトリクス</h2>
        <p>このセクションでは、分類単位で誤差率の分布をマトリクス形式で可視化し、傾向の把握やリスク分析を行います。</p>
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
        
        st.info(f"📊 フィルター後データ件数: {len(filtered_df)}件")
        
        # ③ グラフタイトルと補足説明の追加
        st.markdown("""
        <div class="step-title">📊 誤差率評価マトリクス</div>
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
                "🏷️ 分類",
                category_options,
                key="category_filter"
            )
        
        with col2:
            # 期間フィルター（初期値：全期間）
            if 'Date' in df.columns:
                date_options = ['全期間'] + sorted(df['Date'].dropna().unique().tolist())
                selected_date = st.selectbox(
                    "📅 期間",
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
                "📅 期間",
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
    
    selected_error_type = st.selectbox(
        "📊 誤差率タイプ",
        list(error_types.keys()),
        key="error_type_selector"
    )
    
    # 選択された誤差率タイプの定義を表示
    st.markdown(f"""
    <div class="error-rate-definition">
        <h4>選択中の誤差率定義</h4>
        <ul>
            <li><strong>{selected_error_type}：</strong> {error_types[selected_error_type]['definition']}</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)
    
    return error_types[selected_error_type]['value']

def display_comprehensive_error_rate_matrix(df, error_type):
    """⑤ 包括的誤差率マトリクス表示（簡略版）"""
    try:
        st.write("マトリクス機能は現在開発中です。")
        st.write(f"選択された誤差率タイプ: {error_type}")
        st.write(f"データ件数: {len(df)}")
        
        # 基本的な統計情報を表示
        if 'AI_pred' in df.columns and 'Actual' in df.columns:
            ai_errors = calculate_error_rates(df, 'AI_pred', 'Actual')
            st.write("AI予測の誤差率計算が完了しました")
            st.write(f"AI予測データ件数: {len(ai_errors)}")
        
        if 'Plan_01' in df.columns and 'Actual' in df.columns:
            plan_errors = calculate_error_rates(df, 'Plan_01', 'Actual')
            st.write("計画01の誤差率計算が完了しました")
            st.write(f"計画01データ件数: {len(plan_errors)}")
            
    except Exception as e:
        st.error(f"マトリクス表示でエラーが発生しました: {str(e)}")
        import traceback
        st.code(traceback.format_exc()) 