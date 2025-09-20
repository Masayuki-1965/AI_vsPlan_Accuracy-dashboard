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
    
    # CSSスタイル（UI/UXデザイン統一ガイドライン準拠）
    st.markdown("""
    <style>
    /* セクションヘッダー */
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

    /* STEP注釈・説明文 */
    .step-annotation {
        color: #666666;
        font-size: 0.95em;
        margin-bottom: 1.2em;
    }

    /* 中項目・セクション小見出し */
    .section-subtitle {
        font-size: 1.1em;
        font-weight: bold;
        color: #333333;
        margin-bottom: 0.8em;
        margin-top: 1.2em;
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
        <h2>■ 月次推移比較</h2>
        <p>このセクションでは、AI予測値、計画値（複数可）の<strong>月平均絶対誤差率</strong>（詳細は注釈参照）のポイント差を指定して該当商品コードを抽出し、AI予測値・計画値・実績値の月次推移を折れ線グラフで重ねて表示します。「AI予測値の精度はどれくらいか」「改善余地があるとすれば、誤差の傾向や特徴はどこにあるか？」を把握できます。</p>
    </div>
    """, unsafe_allow_html=True)
    
    # 月平均_絶対誤差率の注釈（展開式）
    with st.expander("月平均絶対誤差率とは", expanded=False):
        st.markdown("""
        <div style="font-size: 0.9rem; color: #666666; line-height: 1.6;">
            各月の絶対誤差率を月別実績値で重みづけして算出した加重平均値です。<br>
            <br>
            <strong>👉 サンプル事例で説明すると、以下のようになります。</strong>
        </div>
        """, unsafe_allow_html=True)
        
        # 事例の表形式表示
        import pandas as pd
        example_data = {
            '': ['実績', '予測', '誤差', '絶対誤差率'],
            '2025年3月': [10, 8, 2, '20%'],
            '2025年4月': [15, 12, 3, '20%'],
            '2025年5月': [20, 18, 2, '10%']
        }
        example_df = pd.DataFrame(example_data)
        
        # 表のスタイリング
        st.markdown("""
        <style>
        .example-table {
            font-size: 0.9rem;
            margin: 1rem 0;
        }
        .example-table table {
            width: 100%;
            border-collapse: collapse;
            background: white;
        }
        .example-table th, .example-table td {
            padding: 0.5rem;
            text-align: center;
            border: 1px solid #dee2e6;
        }
        .example-table th {
            background-color: #f8f9fa;
            font-weight: 600;
        }
        .example-table tbody tr:first-child {
            font-weight: 600;
        }
        </style>
        """, unsafe_allow_html=True)
        
        # データフレームを表として表示（横幅を制限して左詰め）
        col1, col2 = st.columns([2, 3])
        with col1:
            st.markdown('<div class="example-table">', unsafe_allow_html=True)
            st.dataframe(example_df, use_container_width=True, hide_index=True)
            st.markdown('</div>', unsafe_allow_html=True)
        
        st.markdown("""
        <div style="font-size: 0.9rem; color: #666666; line-height: 1.6; margin-top: 1rem;">
            <strong>加重平均：</strong>(<strong>20%</strong> × 10 + <strong>20%</strong> × 15 + <strong>10%</strong> × 20) ÷ (10 + 15 + 20) = 700 ÷ 45 ≒ 15.6%<br>
            <strong>単純平均：</strong>(<strong>20%</strong> + <strong>20%</strong> + <strong>10%</strong>) ÷ 3 = 16.7%<br>
            <br>
            ※ 実績値の大きい月を重みづけして平均することで、より実態に即した精度評価が可能です。
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
        # フィルター設定
        filter_config = create_filter_ui(df)
        
        # フィルター設定が有効な場合のみ処理続行
        if filter_config is None:
            return
        
        # グラフ出力ボタン
        if st.button("月次推移折れ線グラフ一覧を出力する", type="primary", use_container_width=True):
            # データフィルタリング
            filtered_products = apply_filters(df, filter_config)
            
            if not filtered_products:
                st.warning("⚠️ フィルター条件に該当する商品コードがありません。")
                return
            
            # 月次推移折れ線グラフ一覧の見出し（ボタン直下に追加）
            st.markdown('<div class="step-title">月次推移折れ線グラフ一覧</div>', unsafe_allow_html=True)
            
            # グラフ表示
            display_monthly_trend_graphs(df, filtered_products, filter_config)
        
    except Exception as e:
        st.error(f"エラーが発生しました: {str(e)}")
        st.write("デバッグ情報:")
        st.write(f"データフレームの形状: {df.shape}")
        st.write(f"列名: {list(df.columns)}")

def create_filter_ui(df):
    """抽出条件の設定（可視化対象）UIを作成"""
    
    # セッション状態の初期化（状態保持用）
    if 'monthly_trend_filter' not in st.session_state:
        st.session_state.monthly_trend_filter = {
            'category_filter': '全て',
            'abc_filter': [],
            'comparison_items': ['AI_pred', 'Plan_01'],
            'comparison_direction': 0,
            'diff_threshold': 0.1,  # 内部的には0.01単位で管理（0.1 = 10ポイント）
            'sort_order': '降順（差分の大きい順）',
            'max_display': 20
        }
    
    # 抽出条件の設定（可視化対象）見出し（セクション見出しとして統一）
    st.markdown('<div class="step-title">抽出条件の設定（可視化対象）</div>', unsafe_allow_html=True)
    st.markdown('<div class="step-annotation">以下の条件で可視化対象を絞り込んでください。</div>', unsafe_allow_html=True)
    
    # 分類およびABC区分の選択
    st.markdown('<div class="section-subtitle">分類およびABC区分の選択</div>', unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    
    with col1:
        # 分類フィルター
        if 'category_code' in df.columns and not df['category_code'].isna().all():
            category_options = ['全て'] + sorted(df['category_code'].dropna().unique().tolist())
            
            # 保存された状態を初期値として使用
            default_index = 0
            if st.session_state.monthly_trend_filter['category_filter'] in category_options:
                default_index = category_options.index(st.session_state.monthly_trend_filter['category_filter'])
            
            selected_category = st.selectbox(
                "分類",
                category_options,
                index=default_index,
                key="category_filter_ui"
            )
            # 状態を保存
            st.session_state.monthly_trend_filter['category_filter'] = selected_category
        else:
            selected_category = '全て'
            st.info("分類情報がありません")
    
    with col2:
        # ABC区分フィルター
        if 'Class_abc' in df.columns and not df['Class_abc'].isna().all():
            abc_options = sorted(df['Class_abc'].dropna().unique().tolist())
            
            # 保存された状態を初期値として使用
            default_abc = st.session_state.monthly_trend_filter['abc_filter']
            if not default_abc:
                default_abc = abc_options
            
            selected_abc = st.multiselect(
                "ABC区分（複数選択可）",
                abc_options,
                default=default_abc,
                key="abc_filter_ui"
            )
            # 状態を保存
            st.session_state.monthly_trend_filter['abc_filter'] = selected_abc
        else:
            selected_abc = []
            st.info("ABC区分情報がありません")
    
    # 比較対象（2項目選択に限定）
    st.markdown('<div class="section-subtitle">比較対象</div>', unsafe_allow_html=True)
    
    # 項目名カスタマイズの取得（upload.pyのcustom_column_names対応）
    custom_names = st.session_state.get('custom_column_names', {})
    
    # 利用可能な項目とその表示名
    available_items = []
    item_display_names = {}
    
    # AI予測値
    ai_display_name = custom_names.get('AI_pred', 'AI予測値')
    available_items.append('AI_pred')
    item_display_names['AI_pred'] = ai_display_name
    
    # 計画値01
    plan01_display_name = custom_names.get('Plan_01', '計画値01')
    available_items.append('Plan_01')
    item_display_names['Plan_01'] = plan01_display_name
    
    # 計画値02（存在する場合のみ選択可能）
    if 'Plan_02' in df.columns:
        plan02_display_name = custom_names.get('Plan_02', '計画値02')
        available_items.append('Plan_02')
        item_display_names['Plan_02'] = plan02_display_name
    
    # 比較対象の選択（2項目限定）
    # 保存された状態を初期値として使用
    default_items = st.session_state.monthly_trend_filter['comparison_items']
    # 存在しない項目は除外
    default_items = [item for item in default_items if item in available_items]
    if len(default_items) != 2:
        default_items = ['AI_pred', 'Plan_01']
    
    # 表示用のラベルを作成（動的に生成）
    item_labels = [item_display_names[item] for item in available_items]
    label_text = f"{ai_display_name}、{plan01_display_name}"
    if 'Plan_02' in available_items:
        label_text += f"、{plan02_display_name}"
    label_text += "から任意の2項目を選択（2者比較に限定）"
    
    selected_items = st.multiselect(
        label_text,
        available_items,
        default=default_items,
        max_selections=2,
        format_func=lambda x: item_display_names[x],
        key="comparison_items_ui"
    )
    # 状態を保存
    st.session_state.monthly_trend_filter['comparison_items'] = selected_items
    
    if len(selected_items) != 2:
        st.warning("⚠️ 比較対象は必ず2項目を選択してください。")
        return None
    
    # 月平均_絶対誤差率の比較基準（選択された項目に応じて動的に変更）
    st.markdown('<div class="section-subtitle">月平均_絶対誤差率の比較基準</div>', unsafe_allow_html=True)
    
    item1_name = item_display_names[selected_items[0]]
    item2_name = item_display_names[selected_items[1]]
    
    # AI予測値項目を特定（AIを含む項目名を検索）
    ai_item = None
    plan_item = None
    for item in selected_items:
        if 'AI' in item_display_names[item] or 'ai' in item_display_names[item] or 'ハイブリッド' in item_display_names[item]:
            ai_item = item
        else:
            plan_item = item
    
    # 保存された状態を初期値として使用（デフォルトは「AIの誤差率が低い」= index 0）
    default_direction_index = st.session_state.monthly_trend_filter.get('comparison_direction', 0)
    
    # AI項目が特定できた場合は、AIを基準とした表示にする
    if ai_item and plan_item:
        ai_name = item_display_names[ai_item]
        plan_name = item_display_names[plan_item]
        
        comparison_options = [
            f"{ai_name} ＜ {plan_name} （AIの誤差率が低い）",
            f"{ai_name} ＞ {plan_name} （AIの誤差率が高い）"
        ]
        
        comparison_direction = st.selectbox(
            "誤差率の大小",
            comparison_options,
            index=default_direction_index,
            key="comparison_direction_ui",
            help="どちらの誤差率が小さいか（＝精度が高いか）を選択してください"
        )
        
        # 実際の比較方向を内部的に保存（元の形式に変換）
        if "AIの誤差率が低い" in comparison_direction:
            internal_direction = f"{ai_name} ＜ {plan_name}"
        else:
            internal_direction = f"{ai_name} ＞ {plan_name}"
    else:
        # AI項目が特定できない場合は従来の表示
        comparison_options = [
            f"{item1_name} ＜ {item2_name} （{item1_name}の誤差率が低い）",
            f"{item1_name} ＞ {item2_name} （{item1_name}の誤差率が高い）"
        ]
        
        comparison_direction = st.selectbox(
            "誤差率の大小",
            comparison_options,
            index=default_direction_index,
            key="comparison_direction_ui",
            help="どちらの誤差率が小さいか（＝精度が高いか）を選択してください"
        )
        
        # 実際の比較方向を内部的に保存
        if "誤差率が低い" in comparison_direction:
            internal_direction = f"{item1_name} ＜ {item2_name}"
        else:
            internal_direction = f"{item1_name} ＞ {item2_name}"
    # 状態を保存（新しい選択肢のインデックスを保存）
    if ai_item and plan_item:
        direction_options = comparison_options
    else:
        direction_options = comparison_options
    
    st.session_state.monthly_trend_filter['comparison_direction'] = direction_options.index(comparison_direction)
    
    # 内部処理用の比較方向も保存
    st.session_state.monthly_trend_filter['internal_comparison_direction'] = internal_direction
    
    # 誤差率の差分設定
    st.markdown('<div class="section-subtitle">誤差率の差分（何ポイント以上か？）</div>', unsafe_allow_html=True)
    
    # スライダーで設定し、右側に数値を表示
    col5, col6 = st.columns([3, 1])
    
    with col5:
        diff_threshold = st.slider(
            "差分（1ポイント = 1%の差）",
            min_value=0,
            max_value=50,
            value=int(st.session_state.monthly_trend_filter.get('diff_threshold', 0.1) * 100),
            step=1,
            key="diff_threshold_ui",
            help="例：10ポイント = 10%の差（30%と20%の差）。0ポイント = 差分に関係なく全て表示"
        )
        # 内部的には0.01単位で保存（0.01 = 1ポイント）
        internal_diff_value = diff_threshold / 100.0
        st.session_state.monthly_trend_filter['diff_threshold'] = internal_diff_value
    
    with col6:
        # 現在の設定値を数値で表示（他の表示要素とフォントスタイルを統一）
        display_text = f"{diff_threshold}ポイント" if diff_threshold > 0 else "0ポイント（全て表示）"
        st.markdown(f"""
        <div style="
            background: #f8f9fa;
            border: 1px solid #dee2e6;
            border-radius: 4px;
            padding: 0.5rem;
            text-align: center;
            margin-top: 1.5rem;
            font-size: 0.875rem;
            font-weight: 400;
            color: #495057;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', sans-serif;
        ">
            {display_text}
        </div>
        """, unsafe_allow_html=True)
    
    # 実際の差分値を決定
    actual_diff = internal_diff_value
    
    # 表示順
    st.markdown('<div class="section-subtitle">表示順</div>', unsafe_allow_html=True)
    col7, col8 = st.columns(2)
    
    with col7:
        sort_order_options = ["降順（差分の大きい順）", "昇順（差分の小さい順）"]
        default_sort_index = 0
        if st.session_state.monthly_trend_filter['sort_order'] in sort_order_options:
            default_sort_index = sort_order_options.index(st.session_state.monthly_trend_filter['sort_order'])
        
        sort_order = st.selectbox(
            "並び順",
            sort_order_options,
            index=default_sort_index,
            key="sort_order_ui"
        )
        # 状態を保存
        st.session_state.monthly_trend_filter['sort_order'] = sort_order
    
    with col8:
        # 表示件数制限
        max_display = st.slider(
            "最大表示件数",
            min_value=5,
            max_value=100,
            value=st.session_state.monthly_trend_filter['max_display'],
            step=5,
            key="max_display_ui"
        )
        # 状態を保存
        st.session_state.monthly_trend_filter['max_display'] = max_display
    
    return {
        'selected_category': selected_category,
        'selected_abc': selected_abc,
        'selected_items': selected_items,
        'comparison_direction': comparison_direction,
        'internal_comparison_direction': st.session_state.monthly_trend_filter.get('internal_comparison_direction', comparison_direction),
        'diff_threshold': actual_diff,
        'sort_order': sort_order,
        'max_display': max_display,
        'item_display_names': item_display_names
    }

def apply_filters(df, filter_config):
    """フィルター条件に基づいて商品コードを抽出"""
    
    # 必要な列が存在するかチェック
    required_columns = ['P_code', 'Date', 'Actual'] + filter_config['selected_items']
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
    
    # 商品コード別の平均絶対誤差率を計算
    product_error_rates = {}
    selected_items = filter_config['selected_items']
    
    for product_code in filtered_df['P_code'].unique():
        product_data = filtered_df[filtered_df['P_code'] == product_code].copy()
        
        # 各項目の誤差率を計算
        item_errors = {}
        for item in selected_items:
            errors = calculate_error_rates(product_data, item, 'Actual')
            avg_error = calculate_weighted_average_error_rate(errors, 'absolute_error_rate', 'Actual')
            item_errors[item] = avg_error
        
        product_error_rates[product_code] = item_errors
    
    # フィルター条件に基づいて商品コードを抽出
    filtered_products = []
    # 内部比較方向を使用（新しいUI表示に対応）
    comparison_direction = filter_config.get('internal_comparison_direction', filter_config['comparison_direction'])
    threshold = filter_config['diff_threshold']
    
    # 項目名の表示名を取得
    item_display_names = filter_config['item_display_names']
    item1_name = item_display_names[selected_items[0]]
    item2_name = item_display_names[selected_items[1]]
    
    for product_code, errors in product_error_rates.items():
        item1_error = errors[selected_items[0]]
        item2_error = errors[selected_items[1]]
        
        # NaN値のチェック
        if pd.isna(item1_error) or pd.isna(item2_error):
            continue
        
        # 条件判定（内部比較方向を使用）
        if comparison_direction == f"{item1_name} ＞ {item2_name}":
            if (item1_error - item2_error) >= threshold:
                diff_value = item1_error - item2_error
                filtered_products.append((product_code, diff_value))
        
        elif comparison_direction == f"{item1_name} ＜ {item2_name}":
            if (item2_error - item1_error) >= threshold:
                diff_value = item2_error - item1_error
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
    
    # 項目名カスタマイズの取得（upload.pyのcustom_column_names対応）
    custom_names = st.session_state.get('custom_column_names', {})
    
    # 列名の表示用マッピング
    display_names = {
        'AI_pred': custom_names.get('AI_pred', COLUMN_MAPPING.get('AI_pred', 'AI予測値')),
        'Plan_01': custom_names.get('Plan_01', COLUMN_MAPPING.get('Plan_01', '計画値01')),
        'Plan_02': custom_names.get('Plan_02', COLUMN_MAPPING.get('Plan_02', '計画値02')),
        'Actual': custom_names.get('Actual', COLUMN_MAPPING.get('Actual', '実績値'))
    }
    
    # フィルター条件の表示
    threshold_percent = filter_config['diff_threshold'] * 100
    st.info(f"フィルター条件： {filter_config['comparison_direction']} （誤差率の差分： {threshold_percent:.0f}ポイント以上）　表示件数： {len(filtered_products)}件")
    
    # 各商品コードのグラフを表示
    for i, product_code in enumerate(filtered_products):
        
        # 商品コードのデータを取得
        product_data = df[df['P_code'] == product_code].copy()
        
        if product_data.empty:
            continue
        
        # 日付でソート
        if 'Date' in product_data.columns:
            product_data = product_data.sort_values('Date')
        
        # ABC区分を取得（該当商品コードの最初の行から取得）
        abc_class = ""
        if 'Class_abc' in product_data.columns and not product_data['Class_abc'].isna().all():
            abc_value = product_data['Class_abc'].iloc[0]
            if pd.notna(abc_value) and str(abc_value) != '未区分':
                abc_class = f"（{abc_value}区分）"
        
        # 選択された項目の誤差率を計算
        selected_items = filter_config['selected_items']
        item_display_names = filter_config['item_display_names']
        item_errors = {}
        
        for item in selected_items:
            errors = calculate_error_rates(product_data, item, 'Actual')
            avg_error = calculate_weighted_average_error_rate(errors, 'absolute_error_rate', 'Actual')
            item_errors[item] = avg_error
        
        # 差分を計算
        diff_value = abs(item_errors[selected_items[0]] - item_errors[selected_items[1]])
        
        # グラフコンテナ
        with st.container():
            # 商品コードタイトル（ABC区分を併記）
            st.markdown(f"""
            <div class="graph-container">
                <div class="product-code-title">商品コード：{product_code}{abc_class}</div>
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
                # 比較対象名を8文字で省略
                def truncate_name(name, max_length=8):
                    if len(name) > max_length:
                        return name[:max_length] + '…'
                    return name
                
                item1_name = truncate_name(item_display_names[selected_items[0]])
                item2_name = truncate_name(item_display_names[selected_items[1]])
                
                # 比較方向を判定して符号を決定
                comparison_direction = filter_config['comparison_direction']
                item1_error = item_errors[selected_items[0]]
                item2_error = item_errors[selected_items[1]]
                
                # 差分値と符号を計算
                if "＞" in comparison_direction:
                    diff_with_sign = item1_error - item2_error
                    sign_symbol = "＋" if diff_with_sign >= 0 else "ー"
                else:  # "＜"の場合
                    diff_with_sign = item2_error - item1_error
                    sign_symbol = "▲" if diff_with_sign >= 0 else "▼"
                
                # 選択された項目に応じた色を取得
                item1_color = COLOR_PALETTE.get(selected_items[0], '#007bff')
                item2_color = COLOR_PALETTE.get(selected_items[1], '#007bff')
                
                # やや下に配置した横並びレイアウトで表示
                st.markdown("""
                <div style="background: #f8f9fa; padding: 1rem; border-radius: 8px; border: 1px solid #e9ecef; margin-top: 4rem;">
                    <div style="font-weight: 600; font-size: 1rem; margin-bottom: 0.8rem; text-align: center;">
                        【<strong>月平均_絶対誤差率</strong>】
                    </div>
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem;">
                        <div style="text-align: center; flex: 1;">
                            <div style="font-size: 0.85rem; color: #495057; margin-bottom: 0.2rem;">{}</div>
                            <div style="font-size: 0.9rem; font-weight: 500; color: {};">{:.2%}</div>
                        </div>
                        <div style="text-align: center; flex: 1;">
                            <div style="font-size: 0.85rem; color: #495057; margin-bottom: 0.2rem;">{}</div>
                            <div style="font-size: 0.9rem; font-weight: 500; color: {};">{:.2%}</div>
                        </div>
                        <div style="text-align: center; flex: 1;">
                            <div style="font-size: 0.85rem; color: #000000; margin-bottom: 0.2rem;">差分</div>
                            <div style="font-size: 1rem; font-weight: bold; color: #000000;">{}{:.2%}</div>
                        </div>
                    </div>
                </div>
                """.format(
                    item1_name, 
                    item1_color,
                    item1_error, 
                    item2_name, 
                    item2_color,
                    item2_error,
                    sign_symbol, 
                    abs(diff_with_sign)
                ), unsafe_allow_html=True)
            
            # コンテナを閉じる
            st.markdown("</div>", unsafe_allow_html=True)
            
            # コンパクトな区切り線
            if i < len(filtered_products) - 1:
                st.markdown('<hr class="compact-divider">', unsafe_allow_html=True)
    
    # 集計情報の表示
    st.info(f"表示件数: {len(filtered_products)} / 全商品コード数: {df['P_code'].nunique()}") 