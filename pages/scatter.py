import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from utils.error_calculator import calculate_error_rates, calculate_weighted_average_error_rate
from config.constants import UNIFIED_COLOR_PALETTE, PREDICTION_TYPE_NAMES

def show():
    """散布図分析ページを表示"""
    # CSSスタイル（UI/UXガイドライン準拠）の適用
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
    </style>
    """, unsafe_allow_html=True)
    
    # ① 大項目デザイン修正（データセット作成と同じ階層の見出しスタイル）
    st.markdown("""
    <div class="section-header-box">
        <h2>■ 散布図分析（誤差率散布図・予測値vs実績値散布図）</h2>
        <p>このセクションでは、分類単位でABC区分別の誤差率を多角的に分析・可視化し、各区分における誤差の傾向や特徴を明らかにします。</p>
    </div>
    """, unsafe_allow_html=True)
    
    # データ確認
    if st.session_state.data is None:
        st.warning("⚠️ データが読み込まれていません。データアップロードページからデータを読み込んでください。")
        return
    
    df = st.session_state.data
    
    # ③ フィルター項目の追加：「分類」「期間」の順で配置
    filtered_df = apply_filters(df)
    
    if filtered_df.empty:
        st.warning("⚠️ フィルター条件に該当するデータがありません。")
        return
    
    # ② ABC区分別加重平均誤差率表を中項目見出しスタイルで表示
    if 'Class_abc' in filtered_df.columns:
        prediction_columns = ['AI_pred', 'Plan_01']
        if 'Plan_02' in df.columns:
            prediction_columns.append('Plan_02')
        
        abc_avg_errors = calculate_abc_average_errors(filtered_df, prediction_columns)
        display_abc_average_table(abc_avg_errors, filtered_df)
    
    # グラフタイプ選択とオプション設定
    st.markdown("---")
    
    col1, col2 = st.columns(2)
    
    with col1:
        plot_type = st.selectbox(
            "グラフタイプ",
            ['誤差率散布図（横軸：誤差率 ／ 縦軸：計画値）', '予測値 vs 実績値散布図'],
            key="plot_type_selector"
        )
    
    with col2:
        prediction_columns = ['AI_pred', 'Plan_01']
        if 'Plan_02' in df.columns:
            prediction_columns.append('Plan_02')
        
        # 初期選択は全て
        default_selections = prediction_columns
        
        selected_predictions = st.multiselect(
            "表示する予測・計画",
            prediction_columns,
            default=default_selections,
            format_func=get_prediction_name,
            key="prediction_selector"
        )
    
    # ④ 不要な「対比する予測・計画」フィルターを削除
    
    if not selected_predictions:
        st.warning("⚠️ 表示する予測・計画を選択してください。")
        return

    # デフォルト値の計算（分類ごとに最適化）
    default_y_max = get_optimal_y_max(filtered_df, selected_predictions)
    
    # 分類フィルターの値と比較対象を取得（キー生成のため）
    current_category = st.session_state.get('category_filter', '全て')
    current_date = st.session_state.get('date_filter', '全期間')
    predictions_key = '_'.join(sorted(selected_predictions))  # 比較対象もキーに含める
    filter_key = f"{current_category}_{current_date}_{predictions_key}"
    
    # 前回のフィルター値を記録・比較
    previous_filter_key = st.session_state.get('previous_filter_key', '')
    if previous_filter_key != filter_key:
        # フィルターまたは比較対象が変更された場合、古いキーの値をクリア
        st.session_state['previous_filter_key'] = filter_key
        # 既存の軸スケール設定をリセット
        for key in list(st.session_state.keys()):
            if key.startswith('x_min_scatter_') or key.startswith('x_max_scatter_') or key.startswith('y_max_scatter_'):
                if key != f"x_min_scatter_{filter_key}" and key != f"x_max_scatter_{filter_key}" and key != f"y_max_scatter_{filter_key}":
                    del st.session_state[key]
    
    # 軸スケール設定UI（見出しなし、グラフ前に配置）
    col1, col2, col3 = st.columns(3)
    
    with col1:
        x_min_input = st.number_input(
            "横軸最小値 (%)",
            value=-100,
            step=10,
            format="%d",
            key=f"x_min_scatter_{filter_key}"
        )
    
    with col2:
        x_max_input = st.number_input(
            "横軸最大値 (%)",
            value=200,
            step=10,
            format="%d",
            key=f"x_max_scatter_{filter_key}"
        )
    
    with col3:
        # 縦軸最大値の自動最適化（比較対象変更時も含む）
        current_y_max = default_y_max
        
        # 前回と同じフィルターで、かつユーザーが手動調整済みの場合のみ保持
        # ただし、比較対象が変更された場合は新しい最適値を使用
        if (previous_filter_key == filter_key and 
            f"y_max_scatter_{filter_key}" in st.session_state):
            # 前回の値を取得
            previous_y_max = st.session_state[f"y_max_scatter_{filter_key}"]
            # 前回の最適値を計算（比較対象が変更されていない場合）
            previous_optimal = st.session_state.get(f"optimal_y_max_{filter_key}", default_y_max)
            
            # ユーザーが手動調整している場合のみ保持
            if previous_y_max != previous_optimal:
                current_y_max = previous_y_max
        
        # 現在の最適値を記録（次回の判定用）
        st.session_state[f"optimal_y_max_{filter_key}"] = default_y_max
        
        y_max_input = st.number_input(
            "縦軸最大値",
            value=current_y_max,
            step=100,
            format="%d",
            key=f"y_max_scatter_{filter_key}"
        )

    # 散布図作成・表示
    if plot_type == '誤差率散布図（横軸：誤差率 ／ 縦軸：計画値）':
        create_error_rate_scatter(filtered_df, selected_predictions, x_min_input/100, x_max_input/100, y_max_input)
    else:
        create_prediction_vs_actual_scatter(filtered_df, selected_predictions)

def apply_filters(df):
    """③ フィルター設定UIとフィルター適用（分類・期間の順）"""
    # 分類がマッピングされているかどうかを確認
    has_category = 'category_code' in df.columns and not df['category_code'].isna().all()
    
    if has_category:
        # 分類フィルターありの場合
        col1, col2 = st.columns(2)
        
        with col1:
            # 分類フィルター（初期値：全て）
            category_options = ['全て'] + sorted(df['category_code'].dropna().unique().tolist())
            selected_category = st.selectbox("分類", category_options, key="category_filter")
        
        with col2:
            # 期間フィルター（初期値：全期間）
            if 'Date' in df.columns:
                date_options = ['全期間'] + sorted(df['Date'].dropna().unique().tolist())
                selected_date = st.selectbox("期間", date_options, key="date_filter")
            else:
                selected_date = '全期間'
    else:
        # 分類フィルターなしの場合（期間フィルターのみ）
        selected_category = '全て'
        
        # 期間フィルター（初期値：全期間）
        if 'Date' in df.columns:
            date_options = ['全期間'] + sorted(df['Date'].dropna().unique().tolist())
            selected_date = st.selectbox("期間", date_options, key="date_filter")
        else:
            selected_date = '全期間'
    
    # フィルター適用
    filtered_df = df.copy()
    
    # 分類フィルター適用
    if selected_category != '全て':
        filtered_df = filtered_df[filtered_df['category_code'] == selected_category]
    
    # 期間フィルター適用
    if selected_date != '全期間':
        filtered_df = filtered_df[filtered_df['Date'] == selected_date]
    
    return filtered_df

def get_prediction_name(pred_type):
    """予測タイプの表示名を取得（カスタム項目名対応・6文字省略対応）"""
    # カスタム項目名があるかチェック
    if 'custom_column_names' in st.session_state and pred_type in st.session_state.custom_column_names:
        custom_name = st.session_state.custom_column_names[pred_type].strip()
        if custom_name:
            # 全角6文字を超える場合は省略
            if len(custom_name) > 6:
                return custom_name[:6] + '…'
            else:
                return custom_name
    
    # デフォルト名を取得
    default_name = PREDICTION_TYPE_NAMES.get(pred_type, pred_type)
    # デフォルト名も6文字チェック
    if len(default_name) > 6:
        return default_name[:6] + '…'
    else:
        return default_name

def get_optimal_y_max(df, selected_predictions):
    """⑤ 分類ごとに最適化されたデフォルト縦軸最大値を計算"""
    max_values = []
    for pred_col in selected_predictions:
        if pred_col in df.columns:
            max_val = df[pred_col].max()
            if not pd.isna(max_val):
                max_values.append(max_val)
    
    if max_values:
        overall_max = max(max_values)
        # 10%のマージンを追加し、適切な単位で丸める
        margin_added = overall_max * 1.1
        
        # データ規模に応じて適切な単位で丸める
        if margin_added <= 100:
            # 100以下の場合：10の倍数
            optimized_max = int((margin_added // 10 + 1) * 10)
        elif margin_added <= 1000:
            # 1000以下の場合：50の倍数
            optimized_max = int((margin_added // 50 + 1) * 50)
        else:
            # 1000超の場合：100の倍数
            optimized_max = int((margin_added // 100 + 1) * 100)
        
        # 最低値は50（データがある場合）
        return max(optimized_max, 50)
    else:
        return 1000

def create_error_rate_scatter(df, selected_predictions, x_min, x_max, y_max):
    """誤差率散布図を作成（⑤スケール調整対応、⑥凡例修正）"""
    
    # ② グラフタイトルを中項目見出しスタイルで表示
    st.markdown('<div class="step-title">誤差率散布図（横軸：誤差率 ／ 縦軸：計画値）</div>', unsafe_allow_html=True)
    
    # ③ 説明文追加
    st.markdown(
        '<div class="step-annotation">各区分の誤差率を商品コード単位で可視化し、「絶対誤差率」「負の誤差率（欠品リスク）」「正の誤差率（過剰在庫リスク）」を表示します。</div>',
        unsafe_allow_html=True
    )
    
    try:
        # データ検証
        if df.empty:
            st.warning("⚠️ 表示するデータがありません。")
            return
        
        # サブプロット作成
        fig = make_subplots(
            rows=1, 
            cols=len(selected_predictions),
            subplot_titles=[get_prediction_name(pred) for pred in selected_predictions]
        )

        # ⑥ 凡例用の区分を整理（アルファベット順）
        all_abc_classes = set()
        if 'Class_abc' in df.columns:
            all_abc_classes = set(df['Class_abc'].dropna().unique())
        
        # アルファベット順にソート
        sorted_abc_classes = sorted(list(all_abc_classes))
        
        for i, pred_col in enumerate(selected_predictions):
            try:
                # 予測カラムが存在するかチェック
                if pred_col not in df.columns:
                    st.warning(f"⚠️ カラム '{pred_col}' が見つかりません。")
                    continue
                
                # 誤差率計算
                df_with_errors = calculate_error_rates(df, pred_col, 'Actual')
                
                # データ検証：NaN、Inf値を除去
                df_with_errors = df_with_errors.replace([np.inf, -np.inf], np.nan)
                df_with_errors = df_with_errors.dropna(subset=['error_rate', pred_col, 'Actual'])
                
                # 実績がゼロの場合を除外（計算不能）
                valid_data = df_with_errors[~df_with_errors['is_actual_zero']].copy()
                
                if valid_data.empty:
                    st.warning(f"⚠️ {get_prediction_name(pred_col)} の有効なデータがありません。")
                    continue
                
                # 極端な値を制限（グラフ表示範囲外のデータをクリップ）
                valid_data.loc[:, 'error_rate'] = valid_data['error_rate'].clip(lower=x_min*2, upper=x_max*2)
                valid_data.loc[:, pred_col] = valid_data[pred_col].clip(lower=0, upper=y_max*2)
                
                # 色分け用の列を作成（ABC区分があれば使用）
                if 'Class_abc' in df.columns:
                    color_col = 'Class_abc'
                    # ABC区分カラーを統一パレットから取得
                    color_discrete_map = {k: v for k, v in UNIFIED_COLOR_PALETTE.items() 
                                        if k in ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'Z']}
                    # ② 凡例をアルファベット順に表示するためのcategory_orders
                    category_orders = {color_col: sorted_abc_classes}
                else:
                    color_col = None
                    color_discrete_map = None
                    category_orders = None
                
                # 散布図作成（エラーハンドリング付き）
                scatter = px.scatter(
                    valid_data,
                    x='error_rate',
                    y=pred_col,
                    color=color_col,
                    color_discrete_map=color_discrete_map,
                    category_orders=category_orders,
                    hover_data=['P_code', 'Actual', pred_col, 'absolute_error_rate'],
                    title=f"{get_prediction_name(pred_col)}"
                )
                
                # ⑥ 凡例の表示順・ラベルの修正（アルファベット順、重複解消）
                added_legends = set()
                for trace in scatter.data:
                    if 'Class_abc' in df.columns and trace.name and trace.name in sorted_abc_classes:
                        legend_name = f"{trace.name}区分"
                        trace.name = legend_name
                        # 重複削除のため、既に追加済みの凡例は非表示
                        if legend_name in added_legends or i > 0:
                            trace.showlegend = False
                        else:
                            added_legends.add(legend_name)
                    elif not trace.name:  # 空の名前の場合はデフォルト名を設定
                        trace.name = "データ"
                        trace.showlegend = False
                    fig.add_trace(trace, row=1, col=i+1)
                
                # X軸に0の線を追加
                fig.add_vline(x=0, line_dash="dash", line_color="gray", 
                             row=1, col=i+1, annotation_text="完全一致")
                
            except Exception as sub_error:
                st.error(f"❌ {get_prediction_name(pred_col)} の散布図作成でエラー: {str(sub_error)}")
                continue
        
        # レイアウト調整
        fig.update_layout(
            height=600,
            showlegend=True
        )
        
        # ⑤ カスタムスケール適用
        fig.update_xaxes(
            title_text="誤差率", 
            range=[x_min, x_max],
            tickformat='+.0%',
            dtick=0.5
        )
        
        fig.update_yaxes(
            title_text="計画値",
            range=[0, y_max]
        )
        
        # グラフ表示（エラーハンドリング付き）
        st.plotly_chart(fig, use_container_width=True)
        
        # 凡例による表示切替機能の周知
        st.markdown(
            '<div class="step-annotation">※ 凡例項目をクリックすると、該当する区分の表示/非表示を切り替えできます。</div>',
            unsafe_allow_html=True
        )
        
    except Exception as e:
        st.error(f"❌ 散布図の作成でエラーが発生しました: {str(e)}")
        st.info("💡 以下の方法をお試しください：\n- ブラウザの更新（Ctrl+F5）\n- 異なるブラウザでのアクセス\n- データの確認")

def create_prediction_vs_actual_scatter(df, selected_predictions):
    """予測vs実績散布図を作成（⑥凡例修正）"""
    
    # ② グラフタイトルを中項目見出しスタイルで表示
    st.markdown('<div class="step-title">予測値 vs 実績値散布図</div>', unsafe_allow_html=True)
    
    # ④ 説明文追加
    st.markdown(
        '<div class="step-annotation">各区分の予測精度を商品コード単位で可視化し、実績値に対する計画値の妥当性を確認します（破線は完全一致ラインを示します）。</div>',
        unsafe_allow_html=True
    )
    
    try:
        # データ検証
        if df.empty:
            st.warning("⚠️ 表示するデータがありません。")
            return
        
        # サブプロット作成
        fig = make_subplots(
            rows=1, 
            cols=len(selected_predictions),
            subplot_titles=[get_prediction_name(pred) for pred in selected_predictions]
        )
        
        # ⑥ 凡例用の区分を整理（アルファベット順）
        all_abc_classes = set()
        if 'Class_abc' in df.columns:
            all_abc_classes = set(df['Class_abc'].dropna().unique())
        
        sorted_abc_classes = sorted(list(all_abc_classes))
        
        for i, pred_col in enumerate(selected_predictions):
            try:
                # 予測カラムが存在するかチェック
                if pred_col not in df.columns:
                    st.warning(f"⚠️ カラム '{pred_col}' が見つかりません。")
                    continue
                
                # データ検証：NaN、Inf値を除去
                plot_data = df[['Actual', pred_col, 'P_code', 'Date'] + 
                              (['Class_abc'] if 'Class_abc' in df.columns else [])].copy()
                plot_data = plot_data.replace([np.inf, -np.inf], np.nan)
                plot_data = plot_data.dropna(subset=['Actual', pred_col])
                
                if plot_data.empty:
                    st.warning(f"⚠️ {get_prediction_name(pred_col)} の有効なデータがありません。")
                    continue
                
                # 色分け用の列を作成（ABC区分があれば使用）
                if 'Class_abc' in df.columns:
                    color_col = 'Class_abc'
                    color_discrete_map = {k: v for k, v in UNIFIED_COLOR_PALETTE.items() 
                                        if k in ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'Z']}
                    # ② 凡例をアルファベット順に表示するためのcategory_orders
                    category_orders = {color_col: sorted_abc_classes}
                else:
                    color_col = None
                    color_discrete_map = None
                    category_orders = None
                
                # 散布図作成（エラーハンドリング付き）
                scatter = px.scatter(
                    plot_data,
                    x='Actual',
                    y=pred_col,
                    color=color_col,
                    color_discrete_map=color_discrete_map,
                    category_orders=category_orders,
                    hover_data=['P_code', 'Date'],
                    title=f"{get_prediction_name(pred_col)} vs 実績"
                )
                
                # ⑥ 凡例の表示順・ラベルの修正
                added_legends = set()
                for trace in scatter.data:
                    if 'Class_abc' in df.columns and trace.name and trace.name in sorted_abc_classes:
                        legend_name = f"{trace.name}区分"
                        trace.name = legend_name
                        if legend_name in added_legends or i > 0:
                            trace.showlegend = False
                        else:
                            added_legends.add(legend_name)
                    elif not trace.name:  # 空の名前の場合はデフォルト名を設定
                        trace.name = "データ"
                        trace.showlegend = False
                    fig.add_trace(trace, row=1, col=i+1)
                
                # 完全一致ライン（y=x）を追加
                max_val = max(plot_data['Actual'].max(), plot_data[pred_col].max())
                min_val = min(plot_data['Actual'].min(), plot_data[pred_col].min())
                
                # min_val, max_valが有効な値かチェック
                if pd.isna(min_val) or pd.isna(max_val) or min_val == max_val:
                    continue
                
                fig.add_trace(
                    go.Scatter(
                        x=[min_val, max_val], 
                        y=[min_val, max_val],
                        mode='lines',
                        line=dict(color='red', dash='dash'),
                        name='完全一致線',
                        showlegend=(i == 0)  # 最初のサブプロットのみ凡例表示
                    ),
                    row=1, col=i+1
                )
                
            except Exception as sub_error:
                st.error(f"❌ {get_prediction_name(pred_col)} の散布図作成でエラー: {str(sub_error)}")
                continue
        
        # レイアウト調整
        fig.update_layout(
            height=600,
            showlegend=True
        )
        
        fig.update_xaxes(title_text="実績値")
        fig.update_yaxes(title_text="計画値")
        
        # グラフ表示（エラーハンドリング付き）
        st.plotly_chart(fig, use_container_width=True)
        
        # 凡例による表示切替機能の周知
        st.markdown(
            '<div class="step-annotation">💡 凡例項目をクリックすると、該当する区分の表示/非表示を切り替えできます。</div>',
            unsafe_allow_html=True
        )
        
    except Exception as e:
        st.error(f"❌ 散布図の作成でエラーが発生しました: {str(e)}")
        st.info("💡 以下の方法をお試しください：\n- ブラウザの更新（Ctrl+F5）\n- 異なるブラウザでのアクセス\n- データの確認")

def calculate_abc_average_errors(df, selected_predictions):
    """ABC区分別の加重平均誤差率を計算（集計方針準拠・全区分対応）"""
    if 'Class_abc' not in df.columns:
        return {}
    
    abc_errors = {}
    
    for pred_col in selected_predictions:
        df_with_errors = calculate_error_rates(df, pred_col, 'Actual')
        
        # ABC区分別の加重平均誤差率計算（全区分対応・未区分対応）
        abc_stats = {}
        # 未区分（NaN）も含めて処理
        df_with_errors['Class_abc'] = df_with_errors['Class_abc'].fillna('未区分')
        unique_abc_classes = sorted(df_with_errors['Class_abc'].unique())
        
        for abc_class in unique_abc_classes:
            abc_data = df_with_errors[df_with_errors['Class_abc'] == abc_class]
            if not abc_data.empty and len(abc_data) > 0:
                # 絶対誤差率の加重平均（全データ対象）
                absolute_weighted_avg = calculate_weighted_average_error_rate(
                    abc_data, 'absolute_error_rate', 'Actual'
                )
                
                # 正の誤差率の加重平均（positive_error_rate列を使用、誤差率0%を含む）
                positive_weighted_avg = calculate_weighted_average_error_rate(
                    abc_data, 'positive_error_rate', 'Actual'
                )
                
                # 負の誤差率の加重平均（negative_error_rate列を使用、誤差率0%を除外）
                negative_weighted_avg = calculate_weighted_average_error_rate(
                    abc_data, 'negative_error_rate', 'Actual'
                )
                
                # NaNの場合は0.0に設定
                if pd.isna(positive_weighted_avg):
                    positive_weighted_avg = 0.0
                if pd.isna(negative_weighted_avg):
                    negative_weighted_avg = 0.0
                
                abc_stats[abc_class] = {
                    'count': len(abc_data),
                    'actual_sum': abc_data['Actual'].sum(),
                    'absolute_error_rate': absolute_weighted_avg,
                    'positive_error_rate': positive_weighted_avg,
                    'negative_error_rate': negative_weighted_avg
                }
        
        abc_errors[pred_col] = abc_stats
    
    return abc_errors

def display_abc_average_table(abc_errors, filtered_df):
    """② ABC区分別加重平均誤差率のテーブルを中項目見出しスタイルで表示"""
    if not abc_errors:
        st.info("ABC区分データがありません")
        return
    
    # ② 中項目見出し（STEP見出しスタイル統一）
    st.markdown('<div class="step-title">ABC区分別 加重平均誤差率</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="step-annotation">ABC区分別の加重平均誤差率として、「絶対誤差率」、「負の誤差率（＝欠品リスク）」、「正の誤差率（＝過剰在庫リスク）」を表示します。</div>',
        unsafe_allow_html=True
    )
    
    # 全ての予測カラムから全てのABC区分を取得
    all_abc_classes = set()
    for pred_col, abc_stats in abc_errors.items():
        all_abc_classes.update(abc_stats.keys())
    
    if not all_abc_classes:
        st.info("ABC区分データがありません")
        return
    
    # ABC区分をソート（A, B, C, D...の順）
    sorted_abc_classes = sorted(list(all_abc_classes))
    
    # 2段ヘッダー構造のMultiIndex作成（1行目非表示対応）
    columns_tuples = [
        ('', '区分'),
        ('', '件数'),
        ('', '実績合計')
    ]
    
    for error_type in ['絶対誤差率', '負の誤差率', '正の誤差率']:
        for pred_col in sorted(abc_errors.keys()):
            pred_name = get_prediction_name(pred_col)
            columns_tuples.append((error_type, pred_name))
    
    multi_columns = pd.MultiIndex.from_tuples(columns_tuples)
    
    # データ作成
    table_data = []
    total_counts = {}
    total_actual_sums = {}
    
    # 予測カラム別の合計を計算
    for pred_col in abc_errors.keys():
        total_counts[pred_col] = sum(stats['count'] for stats in abc_errors[pred_col].values())
        total_actual_sums[pred_col] = sum(stats['actual_sum'] for stats in abc_errors[pred_col].values())
    
    # ABC区分別のデータ作成
    for abc_class in sorted_abc_classes:
        row_data = [f'{abc_class}区分']
        
        # 件数と実績合計の計算（全予測の平均または合計）
        total_count = 0
        total_actual = 0
        
        for pred_col in sorted(abc_errors.keys()):
            if abc_class in abc_errors[pred_col]:
                stats = abc_errors[pred_col][abc_class]
                total_count = max(total_count, stats['count'])  # 最大値を使用（同じ区分なので）
                total_actual = max(total_actual, stats['actual_sum'])  # 最大値を使用
        
        # 件数と実績合計を文字列形式でフォーマット
        row_data.extend([f"{total_count:,}", f"{total_actual:,.0f}"])
        
        # 各誤差率の値を追加（絶対、負、正の順）
        for error_type in ['absolute_error_rate', 'negative_error_rate', 'positive_error_rate']:
            for pred_col in sorted(abc_errors.keys()):
                if abc_class in abc_errors[pred_col]:
                    error_rate = abc_errors[pred_col][abc_class][error_type]
                    if error_type == 'positive_error_rate':
                        # 正の誤差率には+記号を付ける
                        formatted_rate = f"＋{error_rate:.1%}"
                    elif error_type == 'negative_error_rate':
                        # 負の誤差率には▲記号を付ける
                        formatted_rate = f"▲{abs(error_rate):.1%}"
                    else:
                        formatted_rate = f"{error_rate:.1%}"
                    row_data.append(formatted_rate)
                else:
                    # データがない場合
                    if error_type == 'positive_error_rate':
                        row_data.append("＋0.0%")
                    elif error_type == 'negative_error_rate':
                        row_data.append("▲0.0%")
                    else:
                        row_data.append("0.0%")
        
        table_data.append(row_data)
    
    # 合計行の作成
    total_row_data = ['合計']
    
    # より正確な合計計算（最初の予測カラムから全データの合計を計算）
    if abc_errors:
        first_pred = list(abc_errors.keys())[0]
        grand_total_count = sum(stats['count'] for stats in abc_errors[first_pred].values())
        grand_total_actual = sum(stats['actual_sum'] for stats in abc_errors[first_pred].values())
    else:
        grand_total_count = 0
        grand_total_actual = 0
    
    # 合計行も文字列形式でフォーマット
    total_row_data.extend([f"{grand_total_count:,}", f"{grand_total_actual:,.0f}"])
    
    # 各誤差率の全体加重平均を計算（集計方針準拠）
    for error_type in ['absolute_error_rate', 'negative_error_rate', 'positive_error_rate']:
        for pred_col in sorted(abc_errors.keys()):
            # 全体の加重平均を計算（専用の誤差率列を使用）
            df_with_errors = calculate_error_rates(filtered_df, pred_col, 'Actual')
            
            if error_type == 'positive_error_rate':
                # positive_error_rate列を使用（誤差率0%を含む）
                overall_rate = calculate_weighted_average_error_rate(df_with_errors, 'positive_error_rate', 'Actual')
                if pd.isna(overall_rate):
                    overall_rate = 0.0
                formatted_rate = f"＋{overall_rate:.1%}"
                    
            elif error_type == 'negative_error_rate':
                # negative_error_rate列を使用（誤差率0%を除外）
                overall_rate = calculate_weighted_average_error_rate(df_with_errors, 'negative_error_rate', 'Actual')
                if pd.isna(overall_rate):
                    overall_rate = 0.0
                formatted_rate = f"▲{abs(overall_rate):.1%}"
                    
            else:  # absolute_error_rate
                # absolute_error_rate列を使用（全データ対象）
                overall_rate = calculate_weighted_average_error_rate(df_with_errors, 'absolute_error_rate', 'Actual')
                if pd.isna(overall_rate):
                    overall_rate = 0.0
                formatted_rate = f"{overall_rate:.1%}"
            
            total_row_data.append(formatted_rate)
    
    table_data.append(total_row_data)
    
    # DataFrame作成
    df_table = pd.DataFrame(table_data, columns=multi_columns)
    
    # カスタムCSS for 調整済みカラム幅（1行目ヘッダー非表示）
    table_css = """
    <style>
    .stDataFrame > div {
        width: 100%;
    }
    .stDataFrame table {
        width: 100% !important;
    }
    .stDataFrame th, .stDataFrame td {
        text-align: center !important;
    }
    /* 区分列：8% */
    .stDataFrame th:nth-child(1), .stDataFrame td:nth-child(1) {
        width: 8% !important;
        min-width: 60px !important;
    }
    /* 件数列：8% */
    .stDataFrame th:nth-child(2), .stDataFrame td:nth-child(2) {
        width: 8% !important;
        min-width: 60px !important;
    }
    /* 実績合計列：8% */
    .stDataFrame th:nth-child(3), .stDataFrame td:nth-child(3) {
        width: 8% !important;
        min-width: 60px !important;
    }
    /* 残り6列（計画値01、計画値02、AI予測値のそれぞれ3種類）：各12.67% */
    .stDataFrame th:nth-child(n+4), .stDataFrame td:nth-child(n+4) {
        width: 12.67% !important;
        min-width: 80px !important;
    }
    /* 1行目のヘッダー（MultiIndexの最上位レベル）を非表示 */
    .stDataFrame thead tr:first-child {
        display: none;
    }
    /* 左側3列の1行目ヘッダーの境界線も非表示 */
    .stDataFrame thead tr:first-child th:nth-child(1),
    .stDataFrame thead tr:first-child th:nth-child(2),
    .stDataFrame thead tr:first-child th:nth-child(3) {
        border-bottom: none !important;
    }
    </style>
    """
    st.markdown(table_css, unsafe_allow_html=True)
    
    # テーブル表示
    st.dataframe(
        df_table,
        use_container_width=True,
        hide_index=True
    )
    
    # 注釈の配置とスタイル調整（表の下部に移動、UI/UXガイドライン準拠）
    st.markdown("""
    <div class="step-annotation">
    ※ 誤差率は実績値で重みづけした加重平均値です。<br>
    ※ 集計方針：誤差率0%（完全一致）は「絶対誤差率」と「正の誤差率」のみにカウントされ、「負の誤差率」からは除外されています。<br>
    ※ 負の誤差率は「▲〇.〇％」、正の誤差率は「＋〇.〇％」で表記し、すべて小数第1位で統一しています。
    </div>
    """, unsafe_allow_html=True)

 