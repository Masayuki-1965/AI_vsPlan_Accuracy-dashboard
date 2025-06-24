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
    st.header("📈 散布図分析")
    
    # データ確認
    if st.session_state.data is None:
        st.warning("⚠️ データが読み込まれていません。データアップロードページからデータを読み込んでください。")
        return
    
    df = st.session_state.data
    
    # フィルター設定（期間のみ）
    st.subheader("🔍 フィルター設定")
    filtered_df = apply_filters(df)
    
    if filtered_df.empty:
        st.warning("⚠️ フィルター条件に該当するデータがありません。")
        return
    
    st.info(f"📊 フィルター後データ件数: {len(filtered_df)}件")
    
    # ABC区分別加重平均誤差率表を常時表示
    if 'Class_abc' in filtered_df.columns:
        prediction_columns = ['AI_pred', 'Plan_01']
        if 'Plan_02' in df.columns:
            prediction_columns.append('Plan_02')
        
        abc_avg_errors = calculate_abc_average_errors(filtered_df, prediction_columns)
        display_abc_average_table(abc_avg_errors, filtered_df)
    
    # 散布図表示設定
    st.subheader("⚙️ 表示設定")
    col1, col2 = st.columns(2)
    
    with col1:
        prediction_columns = ['AI_pred', 'Plan_01']
        if 'Plan_02' in df.columns:
            prediction_columns.append('Plan_02')
        
        selected_predictions = st.multiselect(
            "表示する予測・計画",
            prediction_columns,
            default=prediction_columns,
            format_func=get_prediction_name
        )
    
    with col2:
        plot_type = st.selectbox(
            "グラフタイプ",
            ['予測値 vs 実績値散布図', '誤差率散布図（横軸：誤差率 ／ 縦軸：計画値）']
        )
    
    if not selected_predictions:
        st.warning("⚠️ 表示する予測・計画を選択してください。")
        return
    
    # 散布図作成・表示
    if plot_type == '誤差率散布図（横軸：誤差率 ／ 縦軸：計画値）':
        create_error_rate_scatter(filtered_df, selected_predictions)
    else:
        create_prediction_vs_actual_scatter(filtered_df, selected_predictions)

def apply_filters(df):
    """フィルター設定UIとフィルター適用（期間のみ）"""
    # 期間フィルターのみに変更
    if 'Date' in df.columns:
        date_options = ['全期間'] + sorted(df['Date'].dropna().unique().tolist())
        selected_date = st.selectbox("期間", date_options)
    else:
        selected_date = '全期間'
    
    # フィルター適用
    filtered_df = df.copy()
    
    if selected_date != '全期間' and 'Date' in df.columns:
        filtered_df = filtered_df[filtered_df['Date'] == selected_date]
    
    return filtered_df

def get_prediction_name(pred_type):
    """予測タイプの表示名を取得"""
    return PREDICTION_TYPE_NAMES.get(pred_type, pred_type)

def create_error_rate_scatter(df, selected_predictions):
    """誤差率散布図を作成"""
    
    # 横軸スケール設定UI
    st.subheader("⚙️ 横軸スケール設定")
    col1, col2 = st.columns(2)
    
    with col1:
        x_min = st.number_input(
            "横軸最小値 (%)",
            value=-100,
            step=10,
            format="%d"
        )
    
    with col2:
        x_max = st.number_input(
            "横軸最大値 (%)",
            value=200,
            step=10,
            format="%d"
        )
    
    # パーセンテージを小数に変換
    x_min_decimal = x_min / 100
    x_max_decimal = x_max / 100
    
    # サブプロット作成
    fig = make_subplots(
        rows=1, 
        cols=len(selected_predictions),
        subplot_titles=[get_prediction_name(pred) for pred in selected_predictions]
    )

    # 各サブプロットの縦軸の最小値・最大値を統一するために事前計算
    all_y_values = []
    
    for i, pred_col in enumerate(selected_predictions):
        # 誤差率計算
        df_with_errors = calculate_error_rates(df, pred_col, 'Actual')
        
        # 色分け用の列を作成（ABC区分があれば使用）
        if 'Class_abc' in df.columns:
            color_col = 'Class_abc'
            # ABC区分カラーを統一パレットから取得
            color_discrete_map = {k: v for k, v in UNIFIED_COLOR_PALETTE.items() 
                                if k in ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'Z']}
        else:
            color_col = None
            color_discrete_map = None
        
        # 実績がゼロの場合を除外（計算不能）
        valid_data = df_with_errors[~df_with_errors['is_actual_zero']].copy()
        
        # 縦軸統一用にY値を収集
        all_y_values.extend(valid_data[pred_col].tolist())
        
        # 散布図作成
        scatter = px.scatter(
            valid_data,
            x='error_rate',
            y=pred_col,
            color=color_col,
            color_discrete_map=color_discrete_map,
            hover_data=['P_code', 'Actual', pred_col, 'absolute_error_rate'],
            title=f"{get_prediction_name(pred_col)}"
        )
        
        # サブプロットに追加（凡例の名前を区分名に変更）
        for trace in scatter.data:
            if 'Class_abc' in df.columns and trace.name in ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'Z']:
                trace.name = f"{trace.name}区分"
            fig.add_trace(trace, row=1, col=i+1)
        
        # X軸に0の線を追加
        fig.add_vline(x=0, line_dash="dash", line_color="gray", 
                     row=1, col=i+1, annotation_text="完全一致")
    
    # 縦軸の範囲を統一（全データの最小・最大値に基づく）
    if all_y_values:
        y_min = min(all_y_values)
        y_max = max(all_y_values)
        y_margin = (y_max - y_min) * 0.05  # 5%のマージン
        unified_y_range = [y_min - y_margin, y_max + y_margin]
    else:
        unified_y_range = None
    
    # レイアウト調整
    fig.update_layout(
        height=600,
        showlegend=True,
        title_text="誤差率散布図（横軸：誤差率 ／ 縦軸：計画値）",
        title_font_size=16  # フォントサイズを明示的に設定
    )
    
    # 横軸の設定（+/-記号付きの目盛り）
    fig.update_xaxes(
        title_text="誤差率", 
        range=[x_min_decimal, x_max_decimal],
        tickformat='+.0%',  # +/-記号付きのパーセンテージ表示
        dtick=0.5  # 50%刻みで目盛り表示
    )
    
    # 縦軸の設定（統一範囲）
    if unified_y_range:
        fig.update_yaxes(
            title_text="予測・計画値",
            range=unified_y_range
        )
    else:
        fig.update_yaxes(title_text="予測・計画値")
    
    st.plotly_chart(fig, use_container_width=True)

def create_prediction_vs_actual_scatter(df, selected_predictions):
    """予測vs実績散布図を作成"""
    
    # サブプロット作成
    fig = make_subplots(
        rows=1, 
        cols=len(selected_predictions),
        subplot_titles=[get_prediction_name(pred) for pred in selected_predictions]
    )
    
    for i, pred_col in enumerate(selected_predictions):
        # 色分け用の列を作成（ABC区分があれば使用）
        if 'Class_abc' in df.columns:
            color_col = 'Class_abc'
            color_discrete_map = {
                'A': '#FF9999',
                'B': '#66B2FF', 
                'C': '#99FF99',
                'D': '#FFCC99',
                'E': '#FF99CC',
                'F': '#99CCFF',
                'G': '#CCFF99',
                'Z': '#FFB366'
            }
        else:
            color_col = None
            color_discrete_map = None
        
        # 散布図作成
        scatter = px.scatter(
            df,
            x='Actual',
            y=pred_col,
            color=color_col,
            color_discrete_map=color_discrete_map,
            hover_data=['P_code', 'Date'],
            title=f"{get_prediction_name(pred_col)} vs 実績"
        )
        
        # サブプロットに追加（凡例の名前を区分名に変更）
        for trace in scatter.data:
            if 'Class_abc' in df.columns and trace.name in ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'Z']:
                trace.name = f"{trace.name}区分"
            fig.add_trace(trace, row=1, col=i+1)
        
        # 完全一致ライン（y=x）を追加
        max_val = max(df['Actual'].max(), df[pred_col].max())
        min_val = min(df['Actual'].min(), df[pred_col].min())
        
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
    
    # レイアウト調整
    fig.update_layout(
        height=600,
        showlegend=True,
        title_text="予測値 vs 実績値散布図",
        title_font_size=16  # フォントサイズを明示的に設定
    )
    
    fig.update_xaxes(title_text="実績値")
    fig.update_yaxes(title_text="予測・計画値")
    
    st.plotly_chart(fig, use_container_width=True)

def calculate_abc_average_errors(df, selected_predictions):
    """ABC区分別の加重平均誤差率を計算（全区分・3種誤差率対応）"""
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
                # 絶対誤差率の加重平均
                absolute_weighted_avg = calculate_weighted_average_error_rate(
                    abc_data, 'absolute_error_rate', 'Actual'
                )
                
                # 正の誤差率（正の値のみ）の加重平均
                positive_data = abc_data[abc_data['error_rate'] > 0]
                if not positive_data.empty:
                    positive_weighted_avg = calculate_weighted_average_error_rate(
                        positive_data, 'error_rate', 'Actual'
                    )
                else:
                    positive_weighted_avg = 0.0
                
                # 負の誤差率（負の値のみ）の加重平均
                negative_data = abc_data[abc_data['error_rate'] < 0]
                if not negative_data.empty:
                    negative_weighted_avg = calculate_weighted_average_error_rate(
                        negative_data, 'error_rate', 'Actual'
                    )
                else:
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
    """ABC区分別加重平均誤差率のテーブルを表示（2段ヘッダー・3誤差率対応）"""
    if not abc_errors:
        st.info("ABC区分データがありません")
        return
    
    # 全ての予測カラムから全てのABC区分を取得
    all_abc_classes = set()
    for pred_col, abc_stats in abc_errors.items():
        all_abc_classes.update(abc_stats.keys())
    
    if not all_abc_classes:
        st.info("ABC区分データがありません")
        return
    
    # ABC区分をソート（A, B, C, D...の順）
    sorted_abc_classes = sorted(list(all_abc_classes))
    
    # 2段ヘッダー構造のMultiIndex作成
    # レベル1: 区分、実績合計、絶対誤差率、負の誤差率、正の誤差率
    # レベル2: AI予測, 計画01
    columns_level1 = ['区分', '件数', '実績合計', '絶対誤差率', '負の誤差率', '正の誤差率']
    columns_level2 = ['', '', '']  # 区分、件数、実績合計は単列
    
    for error_type in ['絶対誤差率', '負の誤差率', '正の誤差率']:
        for pred_col in sorted(abc_errors.keys()):
            pred_name = get_prediction_name(pred_col)
            columns_level2.append(pred_name)
    
    # MultiIndex列作成
    columns_tuples = [
        ('区分', ''),
        ('件数', ''),
        ('実績合計', '')
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
                    if error_type == 'positive_error_rate' and error_rate != 0:
                        # 正の誤差率には+記号を付ける
                        formatted_rate = f"+{error_rate:.1%}"
                    else:
                        formatted_rate = f"{error_rate:.1%}"
                    row_data.append(formatted_rate)
                else:
                    # データがない場合
                    if error_type == 'positive_error_rate':
                        row_data.append("+0.0%")
                    else:
                        row_data.append("0.0%")
        
        table_data.append(row_data)
    
    # 合計行の作成
    total_row_data = ['合計']
    
    # 件数と実績合計の合計
    grand_total_count = sum(total_counts.values()) // len(total_counts) if total_counts else 0  # 重複排除
    grand_total_actual = sum(total_actual_sums.values()) // len(total_actual_sums) if total_actual_sums else 0  # 重複排除
    
    # より正確な合計計算（最初の予測カラムから全データの合計を計算）
    if abc_errors:
        first_pred = list(abc_errors.keys())[0]
        grand_total_count = sum(stats['count'] for stats in abc_errors[first_pred].values())
        grand_total_actual = sum(stats['actual_sum'] for stats in abc_errors[first_pred].values())
    
    # 合計行も文字列形式でフォーマット
    total_row_data.extend([f"{grand_total_count:,}", f"{grand_total_actual:,.0f}"])
    
    # 各誤差率の全体加重平均を計算
    for error_type in ['absolute_error_rate', 'negative_error_rate', 'positive_error_rate']:
        for pred_col in sorted(abc_errors.keys()):
            # 全体の加重平均を計算（正負の場合は該当データのみ）
            if error_type == 'positive_error_rate':
                # 正の誤差率のみでフィルタリング
                df_with_errors = calculate_error_rates(filtered_df, pred_col, 'Actual')
                positive_data = df_with_errors[df_with_errors['error_rate'] > 0]
                
                if len(positive_data) > 0:
                    overall_rate = calculate_weighted_average_error_rate(positive_data, 'error_rate', 'Actual')
                    formatted_rate = f"+{overall_rate:.1%}"
                else:
                    formatted_rate = "+0.0%"
                    
            elif error_type == 'negative_error_rate':
                # 負の誤差率のみでフィルタリング
                df_with_errors = calculate_error_rates(filtered_df, pred_col, 'Actual')
                negative_data = df_with_errors[df_with_errors['error_rate'] < 0]
                
                if len(negative_data) > 0:
                    overall_rate = calculate_weighted_average_error_rate(negative_data, 'error_rate', 'Actual')
                    formatted_rate = f"{overall_rate:.1%}"
                else:
                    formatted_rate = "0.0%"
                    
            else:  # absolute_error_rate
                # 絶対誤差率（従来通り）
                total_weighted_sum = 0
                total_weight = 0
                
                for abc_class, stats in abc_errors[pred_col].items():
                    error_rate = stats[error_type]
                    weight = stats['actual_sum']
                    total_weighted_sum += error_rate * weight
                    total_weight += weight
                
                if total_weight > 0:
                    overall_rate = total_weighted_sum / total_weight
                    formatted_rate = f"{overall_rate:.1%}"
                else:
                    formatted_rate = "0.0%"
            
            total_row_data.append(formatted_rate)
    
    table_data.append(total_row_data)
    
    # DataFrame作成
    df_table = pd.DataFrame(table_data, columns=multi_columns)
    
    # 注記付きでタイトル表示
    st.markdown("### ABC区分別 加重平均誤差率（絶対値・負方向・正方向）")
    st.markdown("**※ 誤差率は実績値で重みづけした加重平均**")
    
    # カスタムCSS for 等幅列
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
        width: 11.11% !important;  /* 9列なので各列約11% */
        min-width: 80px !important;
    }
    .stDataFrame th:first-child, .stDataFrame td:first-child {
        width: 12% !important;  /* 区分列をやや広く */
    }
    </style>
    """
    st.markdown(table_css, unsafe_allow_html=True)
    
    # テーブル表示（column_configなしでシンプルに）
    st.dataframe(
        df_table,
        use_container_width=True,
        hide_index=True
    ) 