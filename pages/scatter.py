import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from utils.error_calculator import calculate_error_rates, calculate_weighted_average_error_rate

# カラーパレット（統一デザイン）
COLOR_PALETTE = {
    'AI_pred': '#FF6B6B',   # レッド系
    'Plan_01': '#4ECDC4',   # ティール系
    'Plan_02': '#45B7D1'    # ブルー系
}

def show():
    """散布図分析ページを表示"""
    st.header("📈 散布図分析")
    
    # データ確認
    if st.session_state.data is None:
        st.warning("⚠️ データが読み込まれていません。データアップロードページからデータを読み込んでください。")
        return
    
    df = st.session_state.data
    
    # フィルター設定
    st.subheader("🔍 フィルター設定")
    filtered_df = apply_filters(df)
    
    if filtered_df.empty:
        st.warning("⚠️ フィルター条件に該当するデータがありません。")
        return
    
    st.info(f"📊 フィルター後データ件数: {len(filtered_df)}件")
    
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
            ['誤差率散布図', '予測vs実績散布図']
        )
    
    if not selected_predictions:
        st.warning("⚠️ 表示する予測・計画を選択してください。")
        return
    
    # 散布図作成・表示
    if plot_type == '誤差率散布図':
        create_error_rate_scatter(filtered_df, selected_predictions)
    else:
        create_prediction_vs_actual_scatter(filtered_df, selected_predictions)

def apply_filters(df):
    """フィルター設定UIとフィルター適用"""
    col1, col2, col3 = st.columns(3)
    
    with col1:
        # 分類01フィルター
        if 'Class_01' in df.columns:
            class_01_options = ['全て'] + sorted(df['Class_01'].dropna().unique().tolist())
            selected_class_01 = st.selectbox("分類01", class_01_options)
        else:
            selected_class_01 = '全て'
    
    with col2:
        # ABC区分フィルター
        if 'Class_abc' in df.columns:
            abc_options = ['全て'] + sorted(df['Class_abc'].dropna().unique().tolist())
            selected_abc = st.selectbox("ABC区分", abc_options)
        else:
            selected_abc = '全て'
    
    with col3:
        # 期間フィルター
        if 'Date' in df.columns:
            date_options = ['全て'] + sorted(df['Date'].dropna().unique().tolist())
            selected_date = st.selectbox("期間", date_options)
        else:
            selected_date = '全て'
    
    # フィルター適用
    filtered_df = df.copy()
    
    if selected_class_01 != '全て' and 'Class_01' in df.columns:
        filtered_df = filtered_df[filtered_df['Class_01'] == selected_class_01]
    
    if selected_abc != '全て' and 'Class_abc' in df.columns:
        filtered_df = filtered_df[filtered_df['Class_abc'] == selected_abc]
    
    if selected_date != '全て' and 'Date' in df.columns:
        filtered_df = filtered_df[filtered_df['Date'] == selected_date]
    
    return filtered_df

def get_prediction_name(pred_type):
    """予測タイプの表示名を取得"""
    name_mapping = {
        'AI_pred': 'AI予測',
        'Plan_01': '計画01',
        'Plan_02': '計画02'
    }
    return name_mapping.get(pred_type, pred_type)

def create_error_rate_scatter(df, selected_predictions):
    """誤差率散布図を作成"""
    st.subheader("📊 誤差率散布図")
    
    # サブプロット作成
    fig = make_subplots(
        rows=1, 
        cols=len(selected_predictions),
        subplot_titles=[get_prediction_name(pred) for pred in selected_predictions]
    )
    
    # ABC区分別の平均誤差率を計算・表示
    if 'Class_abc' in df.columns:
        abc_avg_errors = calculate_abc_average_errors(df, selected_predictions)
        st.subheader("📋 ABC区分別平均誤差率")
        display_abc_average_table(abc_avg_errors)
    
    for i, pred_col in enumerate(selected_predictions):
        # 誤差率計算
        df_with_errors = calculate_error_rates(df, pred_col, 'Actual')
        
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
                'G': '#CCFF99'
            }
        else:
            color_col = None
            color_discrete_map = None
        
        # 実績がゼロの場合を除外（計算不能）
        valid_data = df_with_errors[~df_with_errors['is_actual_zero']].copy()
        
        # 散布図作成
        scatter = px.scatter(
            valid_data,
            x='error_rate',
            y=pred_col,
            color=color_col,
            color_discrete_map=color_discrete_map,
            hover_data=['P_code', 'Actual', pred_col, 'absolute_error_rate'],
            title=f"{get_prediction_name(pred_col)}の誤差率散布図（分母：実績値）"
        )
        
        # サブプロットに追加
        for trace in scatter.data:
            fig.add_trace(trace, row=1, col=i+1)
        
        # X軸に0の線を追加
        fig.add_vline(x=0, line_dash="dash", line_color="gray", 
                     row=1, col=i+1, annotation_text="完全一致")
    
    # レイアウト調整
    fig.update_layout(
        height=600,
        showlegend=True,
        title_text="誤差率散布図（横軸: 誤差率、縦軸: 予測・計画値）※分母：実績値"
    )
    
    fig.update_xaxes(title_text="誤差率", tickformat='.1%')
    fig.update_yaxes(title_text="予測・計画値")
    
    st.plotly_chart(fig, use_container_width=True)

def create_prediction_vs_actual_scatter(df, selected_predictions):
    """予測vs実績散布図を作成"""
    st.subheader("📊 予測値 vs 実績値散布図")
    
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
                'G': '#CCFF99'
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
        
        # サブプロットに追加
        for trace in scatter.data:
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
        title_text="予測値 vs 実績値散布図"
    )
    
    fig.update_xaxes(title_text="実績値")
    fig.update_yaxes(title_text="予測・計画値")
    
    st.plotly_chart(fig, use_container_width=True)

def calculate_abc_average_errors(df, selected_predictions):
    """ABC区分別の平均誤差率を計算"""
    if 'Class_abc' not in df.columns:
        return {}
    
    abc_errors = {}
    
    for pred_col in selected_predictions:
        df_with_errors = calculate_error_rates(df, pred_col, 'Actual')
        
        # ABC区分別の加重平均誤差率計算
        abc_stats = {}
        for abc_class in ['A', 'B', 'C']:  # A, B, C区分のみ
            abc_data = df_with_errors[df_with_errors['Class_abc'] == abc_class]
            if not abc_data.empty:
                weighted_avg = calculate_weighted_average_error_rate(
                    abc_data, 'absolute_error_rate', 'Actual'
                )
                abc_stats[abc_class] = {
                    'weighted_avg_error_rate': weighted_avg,
                    'count': len(abc_data),
                    'actual_sum': abc_data['Actual'].sum()
                }
        
        abc_errors[pred_col] = abc_stats
    
    return abc_errors

def display_abc_average_table(abc_errors):
    """ABC区分別平均誤差率のテーブルを表示"""
    if not abc_errors:
        st.info("ABC区分データがありません")
        return
    
    # テーブル用データ作成
    table_data = []
    
    for pred_col, abc_stats in abc_errors.items():
        for abc_class, stats in abc_stats.items():
            table_data.append({
                '予測・計画': get_prediction_name(pred_col),
                'ABC区分': abc_class,
                '件数': stats['count'],
                '実績合計': stats['actual_sum'],
                '加重平均誤差率': stats['weighted_avg_error_rate']
            })
    
    if table_data:
        df_table = pd.DataFrame(table_data)
        
        # フォーマット適用
        st.dataframe(
            df_table.style.format({
                '件数': '{:,}',
                '実績合計': '{:,.0f}',
                '加重平均誤差率': '{:.1%}'
            }),
            use_container_width=True
        ) 