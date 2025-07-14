import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from utils.error_calculator import calculate_error_rates, calculate_weighted_average_error_rate
from config.settings import COLOR_PALETTE, COLUMN_MAPPING
from config.ui_styles import HELP_TEXTS

def show():
    """月次推移折れ線グラフ一覧ページを表示"""
    
    # CSSスタイル
    st.markdown("""
    <style>
    /* セクションヘッダー */
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

    /* フィルターエリア */
    .filter-container {
        background: #f8f9fa;
        border-radius: 8px;
        padding: 1.5rem;
        margin-bottom: 2rem;
        border: 1px solid #e9ecef;
    }

    .filter-title {
        font-size: 1.2rem;
        font-weight: 600;
        color: #495057;
        margin-bottom: 1rem;
    }

    /* グラフエリア */
    .graph-container {
        background: white;
        padding: 0.5rem;
        margin-bottom: 1rem;
    }

    .product-code-title {
        font-size: 1.1rem;
        font-weight: 600;
        color: #495057;
        margin-bottom: 0.5rem;
        padding: 0.5rem;
        background: #f8f9fa;
        text-align: center;
    }

    .graph-layout {
        display: flex;
        align-items: flex-start;
        gap: 1rem;
    }

    .graph-section {
        flex: 2;
        min-width: 0;
    }

    .error-info-section {
        flex: 1;
        min-width: 200px;
        background: #f8f9fa;
        border-radius: 8px;
        padding: 0.8rem;
        border: 1px solid #e9ecef;
        height: fit-content;
    }

    .error-info-title {
        font-size: 1rem;
        font-weight: 600;
        color: #495057;
        margin-bottom: 0.8rem;
        text-align: center;
    }

    .error-info-item {
        margin-bottom: 0.5rem;
        font-size: 0.9rem;
    }

    .error-info-label {
        font-weight: 500;
        color: #495057;
    }

    .error-info-value {
        font-weight: 600;
        color: #007bff;
    }

    .error-info-diff {
        font-weight: 600;
        color: #28a745;
    }

    .compact-divider {
        margin: 0.5rem 0;
        border: 0;
        border-top: 1px solid #dee2e6;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # セクションヘッダー
    st.markdown("""
    <div class="section-header-box">
        <h2>■ 月次推移折れ線グラフ一覧</h2>
        <p>商品コード単位で AI予測値・計画値・実績値の月次推移を重ねた折れ線グラフを表示します。平均絶対誤差率の差に基づくフィルターで、AI予測の優位性を可視化します。</p>
    </div>
    """, unsafe_allow_html=True)
    
    # データ確認
    if st.session_state.data is None:
        st.warning("⚠️ データが読み込まれていません。データアップロードページからデータを読み込んでください。")
        return
    
    df = st.session_state.data
    
    try:
        # フィルター設定
        filter_config = create_filter_ui(df)
        
        # データフィルタリング
        filtered_products = apply_filters(df, filter_config)
        
        if not filtered_products:
            st.warning("⚠️ フィルター条件に該当する商品コードがありません。")
            return
        
        # グラフ表示
        display_monthly_trend_graphs(df, filtered_products, filter_config)
        
    except Exception as e:
        st.error(f"エラーが発生しました: {str(e)}")
        st.write("デバッグ情報:")
        st.write(f"データフレームの形状: {df.shape}")
        st.write(f"列名: {list(df.columns)}")

def create_filter_ui(df):
    """フィルター設定UIを作成"""
    
    st.markdown("""
    <div class="filter-container">
        <div class="filter-title">🔍 フィルター設定</div>
    </div>
    """, unsafe_allow_html=True)
    
    # フィルター設定のコンテナ
    with st.container():
        # 分類・ABC区分フィルター
        st.subheader("基本フィルター")
        col1, col2 = st.columns(2)
        
        with col1:
            # 分類フィルター
            if 'category_code' in df.columns and not df['category_code'].isna().all():
                category_options = ['全て'] + sorted(df['category_code'].dropna().unique().tolist())
                selected_category = st.selectbox(
                    "分類",
                    category_options,
                    index=0,
                    key="category_filter"
                )
            else:
                selected_category = '全て'
                st.info("分類情報がありません")
        
        with col2:
            # ABC区分フィルター
            if 'Class_abc' in df.columns and not df['Class_abc'].isna().all():
                abc_options = sorted(df['Class_abc'].dropna().unique().tolist())
                selected_abc = st.multiselect(
                    "ABC区分（複数選択可）",
                    abc_options,
                    default=abc_options,
                    key="abc_filter"
                )
            else:
                selected_abc = []
                st.info("ABC区分情報がありません")
        
        # 比較対象の選択
        st.subheader("比較対象")
        col3, col4 = st.columns(2)
        
        with col3:
            ai_vs_plan01 = st.checkbox("AI予測値 vs 計画値01", value=True, key="ai_vs_plan01")
            ai_vs_plan02 = st.checkbox("AI予測値 vs 計画値02", value=False, key="ai_vs_plan02")
        
        with col4:
            plan01_vs_plan02 = st.checkbox("計画値01 vs 計画値02", value=False, key="plan01_vs_plan02")
        
        # 比較方向の選択
        st.subheader("比較方向")
        comparison_direction = st.selectbox(
            "フィルター条件",
            [
                "AI予測値の誤差率 ＜ 計画値01の誤差率",
                "AI予測値の誤差率 ＞ 計画値01の誤差率",
                "AI予測値の誤差率 ＜ 計画値02の誤差率",
                "AI予測値の誤差率 ＞ 計画値02の誤差率"
            ],
            key="comparison_direction"
        )
        
        # 差分ポイント設定
        st.subheader("差分ポイント設定")
        col5, col6 = st.columns(2)
        
        with col5:
            diff_threshold = st.slider(
                "差分閾値（0.1 = 10ポイント差）",
                min_value=0.0,
                max_value=1.0,
                value=0.1,
                step=0.01,
                format="%.2f",
                key="diff_threshold",
                help="例：0.1 = 10ポイント差（30%と20%の差）"
            )
        
        with col6:
            diff_input = st.number_input(
                "数値入力（0.1 = 10ポイント差）",
                min_value=0.0,
                max_value=1.0,
                value=0.1,
                step=0.01,
                format="%.2f",
                key="diff_input",
                help="例：0.1 = 10ポイント差（30%と20%の差）"
            )
        
        # 実際の差分値を決定（スライダーと数値入力の同期）
        actual_diff = diff_input if diff_input != 0.1 else diff_threshold
        
        # 表示順選択
        st.subheader("表示順")
        col7, col8 = st.columns(2)
        
        with col7:
            sort_order = st.selectbox(
                "並び順",
                ["降順（差分の大きい順）", "昇順（差分の小さい順）"],
                key="sort_order"
            )
        
        with col8:
            # 表示件数制限
            max_display = st.slider(
                "最大表示件数",
                min_value=5,
                max_value=100,
                value=20,
                step=5,
                key="max_display"
            )
    
    return {
        'selected_category': selected_category,
        'selected_abc': selected_abc,
        'ai_vs_plan01': ai_vs_plan01,
        'ai_vs_plan02': ai_vs_plan02,
        'plan01_vs_plan02': plan01_vs_plan02,
        'comparison_direction': comparison_direction,
        'diff_threshold': actual_diff,
        'sort_order': sort_order,
        'max_display': max_display
    }

def apply_filters(df, filter_config):
    """フィルター条件に基づいて商品コードを抽出"""
    
    # 必要な列が存在するかチェック
    required_columns = ['P_code', 'Date', 'Actual', 'AI_pred', 'Plan_01']
    missing_columns = [col for col in required_columns if col not in df.columns]
    if missing_columns:
        st.error(f"必要な列が不足しています: {missing_columns}")
        return []
    
    # 基本フィルターの適用
    filtered_df = df.copy()
    
    # 分類フィルター
    if filter_config['selected_category'] != '全て':
        filtered_df = filtered_df[filtered_df['category_code'] == filter_config['selected_category']]
    
    # ABC区分フィルター
    if filter_config['selected_abc'] and 'Class_abc' in filtered_df.columns:
        filtered_df = filtered_df[filtered_df['Class_abc'].isin(filter_config['selected_abc'])]
    
    # Plan_02の存在チェック
    has_plan02 = 'Plan_02' in df.columns
    
    # 商品コード別の平均絶対誤差率を計算
    product_error_rates = {}
    
    for product_code in filtered_df['P_code'].unique():
        product_data = filtered_df[filtered_df['P_code'] == product_code].copy()
        
        # AI予測値の誤差率
        ai_errors = calculate_error_rates(product_data, 'AI_pred', 'Actual')
        ai_avg_error = calculate_weighted_average_error_rate(ai_errors, 'absolute_error_rate', 'Actual')
        
        # 計画値01の誤差率
        plan01_errors = calculate_error_rates(product_data, 'Plan_01', 'Actual')
        plan01_avg_error = calculate_weighted_average_error_rate(plan01_errors, 'absolute_error_rate', 'Actual')
        
        # 計画値02の誤差率（存在する場合）
        plan02_avg_error = None
        if has_plan02:
            plan02_errors = calculate_error_rates(product_data, 'Plan_02', 'Actual')
            plan02_avg_error = calculate_weighted_average_error_rate(plan02_errors, 'absolute_error_rate', 'Actual')
        
        product_error_rates[product_code] = {
            'ai_error': ai_avg_error,
            'plan01_error': plan01_avg_error,
            'plan02_error': plan02_avg_error
        }
    
    # フィルター条件に基づいて商品コードを抽出
    filtered_products = []
    comparison_direction = filter_config['comparison_direction']
    threshold = filter_config['diff_threshold']
    
    for product_code, errors in product_error_rates.items():
        ai_error = errors['ai_error']
        plan01_error = errors['plan01_error']
        plan02_error = errors['plan02_error']
        
        # NaN値のチェック
        if pd.isna(ai_error) or pd.isna(plan01_error):
            continue
        
        # 条件判定
        if comparison_direction == "AI予測値の誤差率 ＜ 計画値01の誤差率":
            if (plan01_error - ai_error) >= threshold:
                diff_value = plan01_error - ai_error
                filtered_products.append((product_code, diff_value))
        
        elif comparison_direction == "AI予測値の誤差率 ＞ 計画値01の誤差率":
            if (ai_error - plan01_error) >= threshold:
                diff_value = ai_error - plan01_error
                filtered_products.append((product_code, diff_value))
        
        elif comparison_direction == "AI予測値の誤差率 ＜ 計画値02の誤差率":
            if plan02_error is not None and not pd.isna(plan02_error):
                if (plan02_error - ai_error) >= threshold:
                    diff_value = plan02_error - ai_error
                    filtered_products.append((product_code, diff_value))
        
        elif comparison_direction == "AI予測値の誤差率 ＞ 計画値02の誤差率":
            if plan02_error is not None and not pd.isna(plan02_error):
                if (ai_error - plan02_error) >= threshold:
                    diff_value = ai_error - plan02_error
                    filtered_products.append((product_code, diff_value))
    
    # 並び順の適用
    if filter_config['sort_order'] == "降順（差分の大きい順）":
        filtered_products.sort(key=lambda x: x[1], reverse=True)
    else:
        filtered_products.sort(key=lambda x: x[1])
    
    # 表示件数制限
    max_display = filter_config['max_display']
    filtered_products = filtered_products[:max_display]
    
    return [product_code for product_code, _ in filtered_products]

def display_monthly_trend_graphs(df, filtered_products, filter_config):
    """月次推移グラフを表示"""
    
    if not filtered_products:
        st.warning("表示対象の商品コードがありません。")
        return
    
    # 項目名カスタマイズの取得
    mapping = st.session_state.get('mapping', {})
    
    # 列名の表示用マッピング
    display_names = {
        'AI_pred': mapping.get('AI_pred', COLUMN_MAPPING.get('AI_pred', 'AI予測値')),
        'Plan_01': mapping.get('Plan_01', COLUMN_MAPPING.get('Plan_01', '計画値01')),
        'Plan_02': mapping.get('Plan_02', COLUMN_MAPPING.get('Plan_02', '計画値02')),
        'Actual': mapping.get('Actual', COLUMN_MAPPING.get('Actual', '実績値'))
    }
    
    # 結果表示
    st.subheader(f"📊 月次推移グラフ（{len(filtered_products)}件）")
    
    # フィルター条件の表示
    threshold_percent = filter_config['diff_threshold'] * 100
    st.info(f"フィルター条件: {filter_config['comparison_direction']} （差分閾値: {threshold_percent:.0f}ポイント以上）")
    
    # 各商品コードのグラフを表示
    for i, product_code in enumerate(filtered_products):
        
        # 商品コードのデータを取得
        product_data = df[df['P_code'] == product_code].copy()
        
        if product_data.empty:
            continue
        
        # 日付でソート
        if 'Date' in product_data.columns:
            product_data = product_data.sort_values('Date')
        
        # 誤差率を計算
        ai_errors = calculate_error_rates(product_data, 'AI_pred', 'Actual')
        plan01_errors = calculate_error_rates(product_data, 'Plan_01', 'Actual')
        
        ai_avg_error = calculate_weighted_average_error_rate(ai_errors, 'absolute_error_rate', 'Actual')
        plan01_avg_error = calculate_weighted_average_error_rate(plan01_errors, 'absolute_error_rate', 'Actual')
        
        # 計画値02の誤差率（存在する場合）
        plan02_avg_error = None
        if 'Plan_02' in product_data.columns:
            plan02_errors = calculate_error_rates(product_data, 'Plan_02', 'Actual')
            plan02_avg_error = calculate_weighted_average_error_rate(plan02_errors, 'absolute_error_rate', 'Actual')
        
        # グラフコンテナ
        with st.container():
            # 商品コードタイトル
            st.markdown(f"""
            <div class="graph-container">
                <div class="product-code-title">商品コード：{product_code}</div>
            """, unsafe_allow_html=True)
            
            # 横並びレイアウト
            col_graph, col_error = st.columns([2, 1])
            
            with col_graph:
                # Plotlyグラフの作成
                fig = go.Figure()
                
                # 横軸のデータ（日付またはインデックス）
                if 'Date' in product_data.columns:
                    x_data = product_data['Date'].copy()
                    # 日付を適切な形式に変換
                    try:
                        # 数値形式（例：202406）から日付に変換
                        if x_data.dtype == 'object':
                            x_data = pd.to_datetime(x_data.astype(str), format='%Y%m').dt.strftime('%Y年%m月')
                        else:
                            x_data = pd.to_datetime(x_data.astype(str), format='%Y%m').dt.strftime('%Y年%m月')
                    except:
                        try:
                            # 他の形式を試す
                            x_data = pd.to_datetime(x_data).dt.strftime('%Y年%m月')
                        except:
                            # 変換に失敗した場合は文字列として処理
                            x_data = x_data.astype(str)
                else:
                    x_data = product_data.index
                
                # 実績値
                fig.add_trace(go.Scatter(
                    x=x_data,
                    y=product_data['Actual'],
                    mode='lines+markers',
                    name=display_names['Actual'],
                    line=dict(color='#333333', width=3),
                    marker=dict(size=8)
                ))
                
                # AI予測値
                fig.add_trace(go.Scatter(
                    x=x_data,
                    y=product_data['AI_pred'],
                    mode='lines+markers',
                    name=display_names['AI_pred'],
                    line=dict(color=COLOR_PALETTE['AI_pred'], width=2),
                    marker=dict(size=6)
                ))
                
                # 計画値01
                fig.add_trace(go.Scatter(
                    x=x_data,
                    y=product_data['Plan_01'],
                    mode='lines+markers',
                    name=display_names['Plan_01'],
                    line=dict(color=COLOR_PALETTE['Plan_01'], width=2),
                    marker=dict(size=6)
                ))
                
                # 計画値02（存在する場合）
                if 'Plan_02' in product_data.columns:
                    fig.add_trace(go.Scatter(
                        x=x_data,
                        y=product_data['Plan_02'],
                        mode='lines+markers',
                        name=display_names['Plan_02'],
                        line=dict(color=COLOR_PALETTE['Plan_02'], width=2),
                        marker=dict(size=6)
                    ))
                
                # レイアウト設定（軸ラベルを非表示）
                fig.update_layout(
                    title="",
                    xaxis_title="",
                    yaxis_title="",
                    height=280,
                    showlegend=True,
                    legend=dict(
                        orientation="h",
                        yanchor="bottom",
                        y=1.02,
                        xanchor="right",
                        x=1
                    ),
                    hovermode='x unified',
                    margin=dict(l=10, r=10, t=30, b=10),
                    plot_bgcolor='rgba(0,0,0,0)',
                    paper_bgcolor='rgba(0,0,0,0)'
                )
                
                # 軸の設定（フォーマットを調整）
                fig.update_xaxes(
                    tickangle=0,
                    tickfont=dict(size=10),
                    showgrid=True,
                    gridcolor='rgba(128,128,128,0.2)'
                )
                fig.update_yaxes(
                    tickfont=dict(size=10),
                    showgrid=True,
                    gridcolor='rgba(128,128,128,0.2)'
                )
                
                # グラフ表示
                st.plotly_chart(fig, use_container_width=True)
            
            with col_error:
                # 誤差率情報をStreamlitの標準コンポーネントで表示
                st.markdown("**月平均誤差率**")
                
                # 差分を計算（パーセンテージポイントで計算）
                diff_value = abs(ai_avg_error - plan01_avg_error)
                
                # メトリクス表示
                col_metrics1, col_metrics2 = st.columns(2)
                
                with col_metrics1:
                    st.metric(
                        label="AI予測値",
                        value=f"{ai_avg_error:.2%}",
                        help="AI予測値の平均絶対誤差率"
                    )
                    
                with col_metrics2:
                    st.metric(
                        label="計画値01",
                        value=f"{plan01_avg_error:.2%}",
                        help="計画値01の平均絶対誤差率"
                    )
                
                # 計画値02がある場合
                if plan02_avg_error is not None:
                    st.metric(
                        label="計画値02",
                        value=f"{plan02_avg_error:.2%}",
                        help="計画値02の平均絶対誤差率"
                    )
                
                # 差分表示
                st.markdown("---")
                st.metric(
                    label="差分（AI vs 計画値01）",
                    value=f"{diff_value:.2%}",
                    help="AI予測値と計画値01の平均絶対誤差率の差",
                    delta=f"{-diff_value:.2%}" if ai_avg_error < plan01_avg_error else f"{diff_value:.2%}"
                )
            
            # コンテナを閉じる
            st.markdown("</div>", unsafe_allow_html=True)
            
            # コンパクトな区切り線
            if i < len(filtered_products) - 1:
                st.markdown('<hr class="compact-divider">', unsafe_allow_html=True)
    
    # 集計情報の表示
    st.subheader("📈 集計情報")
    st.info(f"表示件数: {len(filtered_products)} / 全商品コード数: {df['P_code'].nunique()}") 