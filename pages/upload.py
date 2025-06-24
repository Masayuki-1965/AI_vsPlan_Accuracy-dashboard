import streamlit as st
import pandas as pd
import numpy as np
import chardet
from utils.validators import validate_data, validate_required_columns
from utils.data_processor import (
    preview_data, 
    calculate_abc_classification, 
    validate_abc_categories, 
    get_abc_classification_summary,
    calculate_abc_classification_by_quantity,
    validate_abc_quantity_categories,
    calculate_default_quantity_ranges
)
from config.settings import ABC_CLASSIFICATION_SETTINGS, COLUMN_MAPPING
from config.ui_styles import HELP_TEXTS, ABC_EXPLANATION
from config.constants import DATA_PROCESSING_CONSTANTS, UI_DISPLAY_CONSTANTS

def show():
    """データセット作成ページを表示"""
    st.header("🛠️ データセット作成")
    
    # セッション状態の初期化
    if 'original_data' not in st.session_state:
        st.session_state.original_data = None
    if 'uploaded_filename' not in st.session_state:
        st.session_state.uploaded_filename = None
    if 'data_columns' not in st.session_state:
        st.session_state.data_columns = []
    if 'current_mapping' not in st.session_state:
        st.session_state.current_mapping = {}
    if 'encoding_info' not in st.session_state:
        st.session_state.encoding_info = None
    if 'mapping_completed' not in st.session_state:
        st.session_state.mapping_completed = False
    if 'abc_categories' not in st.session_state:
        st.session_state.abc_categories = ABC_CLASSIFICATION_SETTINGS['default_categories'].copy()
    if 'abc_auto_generate' not in st.session_state:
        st.session_state.abc_auto_generate = True
    if 'abc_setting_mode' not in st.session_state:
        st.session_state.abc_setting_mode = 'ratio'  # 'ratio' または 'quantity'
    if 'abc_quantity_categories' not in st.session_state:
        st.session_state.abc_quantity_categories = [
            {'name': 'A', 'min_value': 1000},
            {'name': 'B', 'min_value': 100},
            {'name': 'C', 'min_value': 0}
        ]
    if 'monthly_correction_enabled' not in st.session_state:
        st.session_state.monthly_correction_enabled = False
    if 'selected_generation_categories' not in st.session_state:
        st.session_state.selected_generation_categories = []
    
    # アップロードセクション
    st.subheader("1. CSVファイルアップロード")
    uploaded_file = st.file_uploader(
        "CSVファイルを選択してください",
        type=['csv'],
        help=HELP_TEXTS['file_upload_help']
    )
    
    # 新しいファイルがアップロードされた場合
    if uploaded_file is not None:
        # ファイル名が変わった場合のみ処理
        if st.session_state.uploaded_filename != uploaded_file.name:
            try:
                # データ読み込み（エンコーディング自動判別）
                df, _ = read_csv_with_encoding(uploaded_file)
                
                # セッション状態に保存
                st.session_state.original_data = df
                st.session_state.uploaded_filename = uploaded_file.name
                st.session_state.data_columns = list(df.columns)
                st.session_state.current_mapping = {}
                st.session_state.mapping_completed = False
                
                st.success(f"✅ ファイル読み込み成功: {len(df)}行 x {len(df.columns)}列")
                
            except Exception as e:
                st.error(f"❌ ファイル読み込みエラー: {str(e)}")
                return
    
    # 保存されたデータがある場合の表示
    if st.session_state.original_data is not None:
        df = st.session_state.original_data
        
        # ファイル情報表示
        st.info(f"📁 読み込み済みファイル: {st.session_state.uploaded_filename}")
        
        # データプレビュー
        st.subheader(f"2. データプレビュー（上位{DATA_PROCESSING_CONSTANTS['default_preview_rows']}件表示）")
        # インデックスを1始まりに変更
        preview_df = df.head(DATA_PROCESSING_CONSTANTS['default_preview_rows']).copy()
        preview_df.index = range(UI_DISPLAY_CONSTANTS['selectbox_start_index'], len(preview_df) + UI_DISPLAY_CONSTANTS['selectbox_start_index'])
        st.dataframe(preview_df, use_container_width=True)
        
        # データマッピング
        st.subheader("3. データマッピング設定")
        st.info("CSVのカラム名をシステム項目にマッピングしてください")
        
        # マッピング設定UI
        mapping = {}
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**必須項目**")
            mapping['P_code'] = st.selectbox(
                "商品コード（P_code）",
                options=[''] + st.session_state.data_columns,
                index=get_selectbox_index(st.session_state.data_columns, st.session_state.current_mapping.get('P_code', '')),
                help=HELP_TEXTS['product_code_help']
            )
            mapping['Date'] = st.selectbox(
                "年月（Date）",
                options=[''] + st.session_state.data_columns,
                index=get_selectbox_index(st.session_state.data_columns, st.session_state.current_mapping.get('Date', '')),
                help=HELP_TEXTS['date_help']
            )
            mapping['Actual'] = st.selectbox(
                "実績値（Actual）",
                options=[''] + st.session_state.data_columns,
                index=get_selectbox_index(st.session_state.data_columns, st.session_state.current_mapping.get('Actual', '')),
                help=HELP_TEXTS['actual_help']
            )
            mapping['AI_pred'] = st.selectbox(
                "AI予測値（AI_pred）", 
                options=[''] + st.session_state.data_columns,
                index=get_selectbox_index(st.session_state.data_columns, st.session_state.current_mapping.get('AI_pred', '')),
                help=HELP_TEXTS['ai_pred_help']
            )
            mapping['Plan_01'] = st.selectbox(
                "計画値01（Plan_01）",
                options=[''] + st.session_state.data_columns,
                index=get_selectbox_index(st.session_state.data_columns, st.session_state.current_mapping.get('Plan_01', '')),
                help=HELP_TEXTS['plan_01_help']
            )
            
            # ABC区分を必須項目として追加
            st.markdown("**ABC区分設定（必須）**")
            mapping['Class_abc'] = st.selectbox(
                "ABC区分（Class_abc）",
                options=[''] + st.session_state.data_columns,
                index=get_selectbox_index(st.session_state.data_columns, st.session_state.current_mapping.get('Class_abc', '')),
                help=HELP_TEXTS['abc_class_help']
            )
            
            # ABC区分の自動生成設定
            abc_has_column = bool(mapping['Class_abc'])
            if not abc_has_column:
                st.info(ABC_EXPLANATION['auto_no_column'])
                st.session_state.abc_auto_generate = True
            else:
                st.session_state.abc_auto_generate = st.checkbox(
                    "ABC区分を自動生成で上書きする", 
                    value=False,
                    help="チェックすると、CSVのABC区分を無視して実績値から自動計算します"
                )
            
        with col2:
            st.markdown("**任意項目**")
            mapping['category_code'] = st.selectbox(
                "分類（category_code）",
                options=[''] + st.session_state.data_columns,
                index=get_selectbox_index(st.session_state.data_columns, st.session_state.current_mapping.get('category_code', '')),
                help=HELP_TEXTS['class_01_help']
            )
            mapping['Plan_02'] = st.selectbox(
                "計画値02（Plan_02）",
                options=[''] + st.session_state.data_columns,
                index=get_selectbox_index(st.session_state.data_columns, st.session_state.current_mapping.get('Plan_02', '')),
                help=HELP_TEXTS['plan_02_help']
            )
        
        # 現在のマッピング状態を更新
        st.session_state.current_mapping = mapping
        
        # 月別合計値補正設定の追加
        st.markdown("---")
        st.markdown("**月別合計値補正設定**")
        st.session_state.monthly_correction_enabled = st.checkbox(
            "月別合計値補正を有効にする",
            value=st.session_state.monthly_correction_enabled,
            help="分類ごとの月別合計値を計画値01に合わせて調整します。AI予測および計画値02（存在する場合）が対象となります。"
        )
        
        if st.session_state.monthly_correction_enabled:
            st.info("💡 補正ロジック：\n- AI予測の月別合計値 ← 計画値01の月別合計値に調整\n- 計画値02の月別合計値 ← 計画値01の月別合計値に調整（存在する場合）")
        
        # ABC区分設定エクスパンダー（常に表示）
        with st.expander("🔧 ABC区分自動生成設定", expanded=st.session_state.abc_auto_generate):
                # 現在の状態表示
                if st.session_state.abc_auto_generate:
                    st.success(ABC_EXPLANATION['auto_mode'])
                else:
                    st.info(ABC_EXPLANATION['manual_mode'])
                
                # 分類単位での自動生成設定
                st.markdown("### 自動生成対象の分類選択")
                if mapping.get('category_code') and st.session_state.original_data is not None:
                    category_column = mapping['category_code']
                    if category_column in st.session_state.original_data.columns:
                        available_categories = sorted(st.session_state.original_data[category_column].dropna().unique().tolist())
                        if available_categories:
                            selected_categories = st.multiselect(
                                "自動生成を実行する分類を選択してください：",
                                options=available_categories,
                                default=[],
                                help="選択した分類のみABC区分を自動生成します。選択しない分類は既存の値を保持します。"
                            )
                            if 'selected_generation_categories' not in st.session_state:
                                st.session_state.selected_generation_categories = []
                            st.session_state.selected_generation_categories = selected_categories
                        else:
                            st.warning("分類データが見つかりません")
                            st.session_state.selected_generation_categories = []
                    else:
                        st.info("分類カラムが設定されていないため、全データを対象として自動生成します")
                        st.session_state.selected_generation_categories = []
                else:
                    st.info("分類カラムが設定されていないため、全データを対象として自動生成します")
                    st.session_state.selected_generation_categories = []
                
                # 設定パターンの選択
                st.markdown("### 設定パターンの選択")
                setting_mode = st.radio(
                    "区分設定方法",
                    options=['ratio', 'quantity'],
                    format_func=lambda x: '構成比率範囲' if x == 'ratio' else '数量範囲',
                    horizontal=True,
                    index=0 if st.session_state.abc_setting_mode == 'ratio' else 1
                )
                st.session_state.abc_setting_mode = setting_mode
                
                st.markdown("### 自動生成時の区分追加")
                if setting_mode == 'ratio':
                    st.markdown(ABC_EXPLANATION['category_description_ratio'])
                else:
                    st.markdown(ABC_EXPLANATION['category_description_quantity'])
                
                # 現在の区分設定を表示・編集
                categories_df = pd.DataFrame(st.session_state.abc_categories)
                
                # 区分の追加
                col1, col2 = st.columns([3, 1])
                with col1:
                    # 追加可能な区分を「区分」付きで表示
                    additional_options = [''] + [f"{cat['name']}区分" for cat in ABC_CLASSIFICATION_SETTINGS['additional_categories']]
                    new_category_display = st.selectbox(
                        "追加する区分",
                        options=additional_options,
                        help=HELP_TEXTS['abc_additional_help']
                    )
                with col2:
                    # プルダウンのラベル高さに合わせるため調整
                    st.write("")  # ラベル分の高さ調整（selectboxのラベルと合わせる）
                    if st.button("区分を追加する", type="primary", disabled=not new_category_display):
                        # 表示名から区分名を抽出（「D区分」→「D」）
                        new_category_name = new_category_display.replace('区分', '')
                        
                        # 設定パターンに応じて適切なリストを選択
                        if setting_mode == 'ratio':
                            existing_names = [cat['name'] for cat in st.session_state.abc_categories]
                            target_list = st.session_state.abc_categories
                        else:
                            existing_names = [cat['name'] for cat in st.session_state.abc_quantity_categories]
                            target_list = st.session_state.abc_quantity_categories
                        
                        if new_category_name not in existing_names:
                            if setting_mode == 'ratio':
                                # 構成比率パターンの場合
                                last_end = max([cat['end_ratio'] for cat in target_list]) if target_list else 0.0
                                new_category = {
                                    'name': new_category_name,
                                    'start_ratio': last_end,
                                    'end_ratio': min(1.0, last_end + 0.1),
                                    'description': f'{new_category_name}区分'
                                }
                            else:
                                # 数量範囲パターンの場合
                                new_category = {
                                    'name': new_category_name,
                                    'min_value': 1,  # デフォルトの下限値
                                    'description': f'{new_category_name}区分'
                                }
                            target_list.append(new_category)
                            st.rerun()
                        else:
                            st.warning(f"区分 '{new_category_display}' は既に存在します")
                
                # 区分設定の編集（パターンによって切り替え）
                if setting_mode == 'ratio':
                    # 構成比率パターンの編集
                    st.markdown("### 各区分の構成比率範囲の設定")
                    
                    # CSS スタイリング
                    st.markdown("""
                    <style>
                    .editable-field {
                        background-color: #ffffff;
                        border: 2px solid #4CAF50;
                        border-radius: 4px;
                        padding: 2px;
                    }
                    .auto-field {
                        background-color: #f5f5f5;
                        border: 1px solid #cccccc;
                        border-radius: 4px;
                        padding: 2px;
                    }
                    </style>
                    """, unsafe_allow_html=True)
                    
                    edited_categories = []
                    
                    for i, category in enumerate(st.session_state.abc_categories):
                        col1, col2, col3, col4 = st.columns([1, 2, 2, 1])
                        
                        with col1:
                            st.write("")
                            st.markdown(f"**{category['name']}区分**")
                        
                        with col2:
                            if i == 0:
                                start_ratio = 0.0
                                st.number_input(
                                    f"開始%",
                                    min_value=0.0,
                                    max_value=100.0,
                                    value=0.0,
                                    step=1.0,
                                    key=f"start_{i}",
                                    help="A区分の開始は常に0%（自動設定）",
                                    disabled=True
                                )
                            else:
                                start_ratio = edited_categories[i-1]['end_ratio']
                                st.number_input(
                                    f"開始%",
                                    min_value=0.0,
                                    max_value=100.0,
                                    value=start_ratio * 100,
                                    step=1.0,
                                    key=f"start_{i}",
                                    help="前の区分の終了値が自動設定されます",
                                    disabled=True
                                )
                        
                        with col3:
                            is_last_category = (i == len(st.session_state.abc_categories) - 1)
                            
                            if is_last_category:
                                end_ratio = 1.0
                                st.number_input(
                                    f"終了%",
                                    min_value=0.0,
                                    max_value=100.0,
                                    value=100.0,
                                    step=1.0,
                                    key=f"end_{i}",
                                    help="最終区分の終了は常に100%（自動設定）",
                                    disabled=True
                                )
                            else:
                                end_ratio = st.number_input(
                                    f"終了%",
                                    min_value=(start_ratio * 100) + 1.0,
                                    max_value=100.0,
                                    value=category['end_ratio'] * 100,
                                    step=1.0,
                                    key=f"end_{i}",
                                    help="この区分の終了構成比率（%）- 編集可能"
                                ) / 100.0
                        
                        with col4:
                            if len(st.session_state.abc_categories) > 1:
                                st.write("")
                                if st.button("🗑️", key=f"delete_{i}", help="この区分を削除"):
                                    st.session_state.abc_categories.pop(i)
                                    st.rerun()
                            else:
                                st.write("")
                        
                        edited_categories.append({
                            'name': category['name'],
                            'start_ratio': start_ratio,
                            'end_ratio': end_ratio,
                            'description': category.get('description', f'{category["name"]}区分')
                        })
                    
                    # 設定の妥当性チェック
                    is_valid, error_msg = validate_abc_categories(edited_categories)
                    if not is_valid:
                        st.error(f"❌ 区分設定エラー: {error_msg}")
                    else:
                        st.session_state.abc_categories = edited_categories
                        st.success("✅ 区分設定が有効です")
                    
                    # デフォルトに戻すボタン
                    if st.button("デフォルト設定に戻す"):
                        st.session_state.abc_categories = ABC_CLASSIFICATION_SETTINGS['default_categories'].copy()
                        st.rerun()
                
                else:
                    # 数量範囲パターンの編集
                    st.markdown("### 各区分の数量範囲の設定")
                    st.info("各区分の下限値（月平均実績値）を設定してください。最終区分（C区分）の下限値は自動的に0になります。\n\n💡 「データに基づくデフォルト値計算」ボタンを使用すると、構成比率範囲のデフォルト設定と同等の区分けができるように自動計算されます。")
                    
                    edited_quantity_categories = []
                    
                    for i, category in enumerate(st.session_state.abc_quantity_categories):
                        col1, col2, col3, col4 = st.columns([1, 2, 2, 1])
                        
                        with col1:
                            st.write("")
                            st.markdown(f"**{category['name']}区分**")
                        
                        with col2:
                            st.write("")
                            st.markdown("上限：――")
                        
                        with col3:
                            is_last_category = (i == len(st.session_state.abc_quantity_categories) - 1)
                            
                            if is_last_category:
                                min_value = 0
                                st.number_input(
                                    f"下限値",
                                    min_value=0,
                                    max_value=999999999,
                                    value=0,
                                    step=1,
                                    key=f"qty_min_{i}",
                                    help="最終区分の下限は常に0（自動設定）",
                                    disabled=True
                                )
                            else:
                                min_value = st.number_input(
                                    f"下限値",
                                    min_value=0,
                                    max_value=999999999,
                                    value=category.get('min_value', 0),
                                    step=1,
                                    key=f"qty_min_{i}",
                                    help=f"{category['name']}区分の下限値（この値以上）"
                                )
                        
                        with col4:
                            if len(st.session_state.abc_quantity_categories) > 1:
                                st.write("")
                                if st.button("🗑️", key=f"qty_delete_{i}", help="この区分を削除"):
                                    st.session_state.abc_quantity_categories.pop(i)
                                    st.rerun()
                            else:
                                st.write("")
                        
                        edited_quantity_categories.append({
                            'name': category['name'],
                            'min_value': min_value,
                            'description': category.get('description', f'{category["name"]}区分')
                        })
                    
                    # 設定の妥当性チェック
                    is_valid, error_msg = validate_abc_quantity_categories(edited_quantity_categories)
                    if not is_valid:
                        st.error(f"❌ 区分設定エラー: {error_msg}")
                    else:
                        st.session_state.abc_quantity_categories = edited_quantity_categories
                        st.success("✅ 区分設定が有効です")
                    
                    # ボタン行
                    col_btn1, col_btn2 = st.columns(2)
                    with col_btn1:
                        if st.button("データに基づくデフォルト値計算", key="calc_default_quantity"):
                            if st.session_state.original_data is not None:
                                # 現在のマッピングからActualカラムを取得
                                actual_column = mapping.get('Actual', '')
                                if actual_column and actual_column in st.session_state.original_data.columns:
                                    # マッピング済みデータを作成
                                    temp_df = apply_mapping(st.session_state.original_data, mapping)
                                    # デフォルト値を計算
                                    default_categories = calculate_default_quantity_ranges(temp_df, 'Actual')
                                    st.session_state.abc_quantity_categories = default_categories
                                    st.success("✅ データに基づくデフォルト値を計算しました")
                                    st.rerun()
                                else:
                                    st.error("❌ 実績値カラムが設定されていません")
                            else:
                                st.error("❌ データが読み込まれていません")
                    
                    with col_btn2:
                        if st.button("固定デフォルト設定に戻す", key="reset_quantity"):
                            st.session_state.abc_quantity_categories = [
                                {'name': 'A', 'min_value': 1000},
                                {'name': 'B', 'min_value': 100},
                                {'name': 'C', 'min_value': 0}
                            ]
                            st.rerun()
        
        # マッピング確認・保存（2つのボタンに分離）
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("📋 マッピング設定を適用する", type="primary", use_container_width=True):
                # 必須項目チェック（ABC区分は除く - 自動生成するため）
                required_fields = ['P_code', 'Date', 'Actual', 'AI_pred', 'Plan_01']
                missing_fields = [field for field in required_fields if not mapping[field]]
                
                if missing_fields:
                    st.error(f"❌ 必須項目が未設定です: {', '.join(missing_fields)}")
                else:
                    try:
                        # データ変換（ABC区分は既存値のみ使用）
                        mapped_df = apply_mapping(df, mapping)
                        
                        # 基本検証
                        if validate_mapped_data(mapped_df):
                            # 月別合計値補正の実行
                            if st.session_state.monthly_correction_enabled:
                                with st.status("🔄 月別合計値補正を実行中...", expanded=True) as status:
                                    st.write("📊 分類ごとの月別合計値を分析中...")
                                    
                                    try:
                                        mapped_df = apply_monthly_correction(mapped_df)
                                        st.write("✅ 月別合計値補正完了")
                                        status.update(label="✅ 月別合計値補正完了", state="complete")
                                    except Exception as e:
                                        st.error(f"❌ 月別合計値補正エラー: {str(e)}")
                                        status.update(label="❌ 月別合計値補正エラー", state="error")
                                        return
                            
                            st.session_state.data = mapped_df
                            st.session_state.mapping = mapping
                            st.session_state.mapping_completed = True
                            st.success("✅ データマッピング完了！")
                            
                            # ABC区分がない場合の案内
                            if 'Class_abc' not in mapped_df.columns or mapped_df['Class_abc'].isna().all():
                                st.info("💡 ABC区分を自動生成する場合は、右側の「ABC区分を自動生成する」ボタンをお使いください。")
                            
                            st.rerun()
                        else:
                            st.error("❌ データ検証でエラーが発生しました")
                            
                    except Exception as e:
                        st.error(f"❌ データ処理エラー: {str(e)}")
        
        with col2:
            # ABC区分自動生成ボタン（別処理として分離）
            abc_button_disabled = not st.session_state.get('mapping_completed', False)
            if st.button("🔄 ABC区分を自動生成する", 
                        type="secondary", 
                        use_container_width=True,
                        disabled=abc_button_disabled,
                        help="先にマッピング設定を適用してください" if abc_button_disabled else "選択した分類のABC区分を自動生成します"):
                
                if st.session_state.get('data') is None:
                    st.error("❌ 先にマッピング設定を適用してください")
                    return
                
                # 現在のデータを取得
                mapped_df = st.session_state.data.copy()
                
                # ABC区分の自動生成処理
                has_selected_categories = bool(st.session_state.selected_generation_categories)
                
                # ABC区分生成処理を実行
                # 【パターン②】部分上書き または 【パターン③】全体自動生成
                with st.status("🔄 ABC区分を自動生成中...", expanded=True) as status:
                    st.write("📊 実績値データを分析中...")
                    
                    # 区分設定の妥当性チェック
                    if st.session_state.abc_setting_mode == 'ratio':
                        is_valid, error_msg = validate_abc_categories(st.session_state.abc_categories)
                        current_categories = st.session_state.abc_categories
                    else:
                        is_valid, error_msg = validate_abc_quantity_categories(st.session_state.abc_quantity_categories)
                        current_categories = st.session_state.abc_quantity_categories
                    
                    if not is_valid:
                        st.error(f"❌ ABC区分設定エラー: {error_msg}")
                        status.update(label="❌ ABC区分設定エラー", state="error")
                        return
                    
                    st.write("🔢 商品コード別実績値を集計中...")
                    
                    # パターン判定と処理
                    target_categories = st.session_state.selected_generation_categories if has_selected_categories else None
                    preserve_existing = True  # 既存ABC区分を常に保持
                    
                    try:
                        if st.session_state.abc_setting_mode == 'ratio':
                            mapped_df = calculate_abc_classification(
                                mapped_df, 
                                categories=current_categories,
                                base_column='Actual',
                                target_categories=target_categories,
                                preserve_existing=preserve_existing
                            )
                        else:
                            mapped_df = calculate_abc_classification_by_quantity(
                                mapped_df, 
                                categories=current_categories,
                                base_column='Actual',
                                target_categories=target_categories,
                                preserve_existing=preserve_existing
                            )
                        st.write("✅ ABC区分の割り当て完了")
                        
                        # 処理モードの表示
                        if target_categories:
                            st.info(f"📝 選択した分類（{', '.join(target_categories)}）のABC区分を自動生成しました")
                        else:
                            st.info("📝 全データのABC区分を自動生成しました")
                        
                        # 生成結果の表示
                        abc_summary = get_abc_classification_summary(mapped_df, 'Class_abc', 'Actual')
                        if abc_summary:
                            st.write("📈 集計結果:")
                            
                            # 各区分の詳細情報
                            if st.session_state.abc_setting_mode == 'ratio':
                                for category in sorted(current_categories, key=lambda x: x['start_ratio']):
                                    cat_name = category['name']
                                    count = abc_summary['counts'].get(cat_name, 0)
                                    ratio = abc_summary['ratios'].get(cat_name, 0)
                                    range_text = f"{category['start_ratio']*100:.0f}%-{category['end_ratio']*100:.0f}%"
                                    st.write(f"　• {cat_name}区分({range_text}): {count}件 ({ratio:.1f}%)")
                            else:
                                for category in sorted(current_categories, key=lambda x: x.get('min_value', 0), reverse=True):
                                    cat_name = category['name']
                                    count = abc_summary['counts'].get(cat_name, 0)
                                    ratio = abc_summary['ratios'].get(cat_name, 0)
                                    min_val = category.get('min_value', 0)
                                    st.write(f"　• {cat_name}区分({min_val}以上): {count}件 ({ratio:.1f}%)")
                            
                            # 未区分がある場合の警告
                            if '未区分' in abc_summary['counts']:
                                unclassified_count = abc_summary['counts']['未区分']
                                st.warning(f"⚠️ 未区分の商品が{unclassified_count}件あります。必要に応じて追加で自動生成を実行してください。")
                            
                            status.update(label="✅ ABC区分自動生成完了", state="complete")
                        else:
                            st.warning("⚠️ ABC区分の集計に問題があります")
                            
                        # セッション状態を更新
                        st.session_state.data = mapped_df
                        st.rerun()
                        
                    except Exception as e:
                        st.error(f"❌ ABC区分計算エラー: {str(e)}")
                        status.update(label="❌ ABC区分計算エラー", state="error")
                        return
        
        # マッピング完了後の表示
        if st.session_state.mapping_completed and st.session_state.data is not None:
            # マッピング結果表示
            st.subheader("4. マッピング結果")
            
            # 日本語名のマッピング
            mapping_data = []
            for k, v in st.session_state.current_mapping.items():
                if v:  # 空でない場合のみ
                    japanese_name = COLUMN_MAPPING.get(k, k)
                    system_item_display = f"{japanese_name} ({k})"
                    data_type = str(st.session_state.data[k].dtype) if k in st.session_state.data.columns else "未設定"
                    mapping_data.append({
                        "システム項目": system_item_display,
                        "CSVのカラム名": v,
                        "データ型": data_type
                    })
            
            mapping_df = pd.DataFrame(mapping_data)
            # インデックスを1始まりに変更
            mapping_df.index = range(1, len(mapping_df) + 1)
            st.dataframe(mapping_df, use_container_width=True)
            
            # 変換後データプレビュー
            st.subheader("5. 変換後データプレビュー（上位5件表示）")
            
            # カラム名を日本語に変更したデータフレームを作成
            preview_data = st.session_state.data.head(5).copy()
            
            # カラム名を日本語に変更
            japanese_column_mapping = {}
            for col in preview_data.columns:
                if col in COLUMN_MAPPING:
                    japanese_column_mapping[col] = COLUMN_MAPPING[col]
                else:
                    japanese_column_mapping[col] = col
            
            preview_data = preview_data.rename(columns=japanese_column_mapping)
            
            # ABC区分を商品コードの直後に配置
            if 'ABC区分' in preview_data.columns and '商品コード' in preview_data.columns:
                # カラムの順序を調整
                cols = list(preview_data.columns)
                # ABC区分を削除
                cols.remove('ABC区分')
                # 商品コードの位置を取得
                product_code_idx = cols.index('商品コード')
                # 商品コードの直後にABC区分を挿入
                cols.insert(product_code_idx + 1, 'ABC区分')
                preview_data = preview_data[cols]
            
            # インデックスを1始まりに変更
            preview_data.index = range(1, len(preview_data) + 1)
            st.dataframe(preview_data, use_container_width=True)
            
            # ABC区分の集計結果表示
            if 'Class_abc' in st.session_state.data.columns:
                st.subheader("6. ABC区分集計結果")
                
                # 分類フィルターの追加
                if 'category_code' in st.session_state.data.columns and st.session_state.data['category_code'].notna().any():
                    categories = ['全分類'] + sorted(st.session_state.data['category_code'].dropna().unique().tolist())
                    selected_category = st.selectbox(
                        "分類：",
                        options=categories,
                        key="abc_category_filter"
                    )
                    
                    # フィルター適用
                    if selected_category == '全分類':
                        filtered_abc_data = st.session_state.data
                        category_display = ""
                    else:
                        filtered_abc_data = st.session_state.data[st.session_state.data['category_code'] == selected_category]
                        category_display = f"分類：{selected_category}"
                else:
                    filtered_abc_data = st.session_state.data
                    category_display = ""
                
                abc_summary = get_abc_classification_summary(filtered_abc_data, 'Class_abc', 'Actual')
                
                if abc_summary:
                    # 2カラムレイアウト：左側に統合表、右側に読み込み済みデータ情報
                    col_left, col_right = st.columns([2, 1])
                    
                    with col_left:
                        # 統合表の作成（実績合計を追加）
                        abc_result_data = []
                        total_count = 0
                        total_actual = 0
                        
                        # 区分順に並べるため、A,B,C,D,...の順でソート
                        sorted_categories = sorted(abc_summary['counts'].keys())
                        
                        for category in sorted_categories:
                            count = abc_summary['counts'].get(category, 0)
                            ratio = abc_summary['ratios'].get(category, 0)
                            actual_sum = abc_summary['actual_sums'].get(category, 0)
                            
                            abc_result_data.append({
                                'ABC区分': f"{category}区分",
                                '件数': count,
                                '実績合計': int(actual_sum),
                                '構成比率（%）': f"{ratio:.2f}%"
                            })
                            total_count += count
                            total_actual += actual_sum
                        
                        # 構成比率の合計を100.00%に調整
                        if abc_result_data and total_actual > 0:
                            current_total_ratio = sum(abc_summary['ratios'].values())
                            if abs(current_total_ratio - 100.0) > 0.01:  # 誤差がある場合のみ調整
                                # 最大の区分に差分を加算
                                max_category = max(sorted_categories, key=lambda x: abc_summary['ratios'][x])
                                adjustment = 100.0 - current_total_ratio
                                for item in abc_result_data:
                                    if item['ABC区分'] == f"{max_category}区分":
                                        current_ratio = float(item['構成比率（%）'].replace('%', ''))
                                        adjusted_ratio = current_ratio + adjustment
                                        item['構成比率（%）'] = f"{adjusted_ratio:.2f}%"
                                        break
                        
                        # 合計行を追加
                        abc_result_data.append({
                            'ABC区分': '合計',
                            '件数': total_count,
                            '実績合計': int(total_actual),
                            '構成比率（%）': "100.00%"
                        })
                        
                        # データフレーム作成（インデックスなし）
                        result_df = pd.DataFrame(abc_result_data)
                        st.dataframe(result_df, use_container_width=True, hide_index=True)
                    
                    with col_right:
                        # 読み込み済みデータ情報を右側に配置
                        if filtered_abc_data is not None:
                            df = filtered_abc_data
                            
                            # 期間の年月フォーマット変換
                            def format_date(date_val):
                                date_str = str(date_val)
                                if len(date_str) == 6:  # YYYYMM形式
                                    year = date_str[:4]
                                    month = date_str[4:6]
                                    return f"{year}年{month}月"
                                return date_str
                            
                            min_date = format_date(df['Date'].min())
                            max_date = format_date(df['Date'].max())
                            
                            st.markdown("**📊 読み込み済みデータ情報**")
                            st.markdown(f"**期間範囲：** {min_date} - {max_date}")
                            st.markdown(f"**データ件数：** {len(df):,} 件")
                            st.markdown(f"**商品コード数：** {df['P_code'].nunique():,} 件")
            
            # 年月別集計結果の追加
            if 'Date' in st.session_state.data.columns:
                st.subheader("7. 年月別集計結果")
                
                # 分類フィルターの追加
                if 'category_code' in st.session_state.data.columns and st.session_state.data['category_code'].notna().any():
                    categories = ['全分類'] + sorted(st.session_state.data['category_code'].dropna().unique().tolist())
                    selected_category_monthly = st.selectbox(
                        "分類：",
                        options=categories,
                        key="monthly_category_filter"
                    )
                    
                    # フィルター適用
                    if selected_category_monthly == '全分類':
                        filtered_monthly_data = st.session_state.data
                        category_display_monthly = ""
                    else:
                        filtered_monthly_data = st.session_state.data[st.session_state.data['category_code'] == selected_category_monthly]
                        category_display_monthly = f"分類：{selected_category_monthly}"
                else:
                    filtered_monthly_data = st.session_state.data
                    category_display_monthly = ""
                
                monthly_summary_df = create_monthly_summary_table(filtered_monthly_data)
                if not monthly_summary_df.empty:
                    st.dataframe(monthly_summary_df, use_container_width=True, hide_index=True)
                    st.markdown("**※ 月別合計値補正を実施した場合は、AI予測および計画値の月別合計が一致しているかをご確認ください。**")
                else:
                    st.info("年月別集計データがありません")
    
    # 既存の読み込み済みデータ情報表示を削除（統合したため）

def get_selectbox_index(options, value):
    """selectboxのindex値を取得"""
    try:
        if value in options:
            return options.index(value) + 1  # 空の選択肢があるため+1
        else:
            return 0
    except:
        return 0

def apply_mapping(df, mapping):
    """データフレームにマッピングを適用"""
    mapped_df = pd.DataFrame()
    
    for system_field, csv_column in mapping.items():
        if csv_column and csv_column in df.columns:
            mapped_df[system_field] = df[csv_column]
    
    return mapped_df

def read_csv_with_encoding(uploaded_file):
    """複数のエンコーディングを試してCSVファイルを読み込み"""
    # 日本語ファイル用の優先エンコーディング順序（Shift_JIS系を最優先）
    encodings = ['shift_jis', 'cp932', 'utf-8', 'utf-8-sig', 'euc-jp', 'iso-2022-jp', 'latin1']
    
    # まず文字エンコーディングを自動判別
    raw_data = uploaded_file.getvalue()
    detected = chardet.detect(raw_data)
    detected_encoding = detected.get('encoding', '').lower() if detected.get('encoding') else ''
    confidence = detected.get('confidence', 0)
    
    encoding_info = f"🔍 文字エンコーディング判別結果: {detected_encoding.upper() if detected_encoding else 'Unknown'} (信頼度: {confidence:.2f})"
    
    # MacRomanや低信頼度の場合は無視してShift_JISを強制的に最初に試行
    if detected_encoding == 'macroman':
        # MacRomanは日本語ファイルでは信頼できない - 完全に無視
        pass  # Shift_JISを最優先で試行
    elif confidence < 0.5:
        # 信頼度が低い場合もShift_JISを優先
        pass  # Shift_JISを最優先で試行
    elif detected_encoding and detected_encoding not in [enc.lower() for enc in encodings]:
        # 信頼度が高い場合のみ、その他の判別結果を試行リストに追加
        encodings.insert(0, detected_encoding)
    
    # 各エンコーディングを順番に試行
    last_error = None
    best_result = None
    best_score = -1
    encoding_results = []  # デバッグ用
    
    for encoding in encodings:
        try:
            # ファイルポインタをリセット
            uploaded_file.seek(0)
            
            # CSVファイルを読み込み（区切り文字とクォート文字を自動判別）
            df = read_csv_with_options(uploaded_file, encoding)
            
            # 読み込み後の品質スコアを計算
            quality_score = calculate_japanese_quality_score(df)
            encoding_results.append(f"{encoding}: {quality_score}/10")
            
            if quality_score > best_score:
                best_result = (df, encoding, quality_score)
                best_score = quality_score
            
            # 高品質な結果が得られた場合は即座に採用
            if quality_score >= 7:  # 10点満点中7点以上
                break
                
        except (UnicodeDecodeError, UnicodeError, LookupError) as e:
            encoding_results.append(f"{encoding}: エラー({type(e).__name__})")
            last_error = e
            continue
        except Exception as e:
            encoding_results.append(f"{encoding}: エラー({type(e).__name__})")
            last_error = e
            continue
    
    # 最良の結果を採用
    if best_result and best_score >= 2:  # 最低限の品質を満たす場合
        df, successful_encoding, score = best_result
        # 一般ユーザー向けにシンプルなメッセージを返す
        return df, f"✅ ファイル読み込み完了"
    
    # すべて失敗した場合
    if last_error:
        raise Exception(f"すべてのエンコーディングで読み込みに失敗しました。最後のエラー: {str(last_error)}")
    else:
        raise Exception("CSVファイルの読み込みに失敗しました")

def read_csv_with_options(uploaded_file, encoding):
    """CSVファイルを適切なオプションで読み込み"""
    # 区切り文字の候補
    separators = [',', ';', '\t', '|']
    
    # クォート文字の候補
    quote_chars = ['"', "'", None]
    
    best_df = None
    best_columns = 0
    
    for sep in separators:
        for quote_char in quote_chars:
            try:
                uploaded_file.seek(0)
                if quote_char is None:
                    df = pd.read_csv(uploaded_file, encoding=encoding, sep=sep, quoting=3)  # QUOTE_NONE
                else:
                    df = pd.read_csv(uploaded_file, encoding=encoding, sep=sep, quotechar=quote_char)
                
                # より多くのカラムを持つ結果を優先
                if len(df.columns) > best_columns and not df.empty:
                    best_df = df
                    best_columns = len(df.columns)
                    
                # 十分な数のカラムがある場合は早期終了
                if best_columns >= 5:
                    break
                    
            except Exception:
                continue
                
        if best_columns >= 5:
            break
    
    # 最良の結果を返す、なければデフォルトで再試行
    if best_df is not None:
        return best_df
    else:
        uploaded_file.seek(0)
        return pd.read_csv(uploaded_file, encoding=encoding)

def calculate_japanese_quality_score(df):
    """読み込んだCSVの品質を0-10のスコアで評価"""
    try:
        # データフレームが空でないことを確認
        if df.empty or len(df.columns) == 0:
            return 0
        
        score = 0
        
        # カラム名と最初の数行のデータをサンプルとして検査
        sample_texts = []
        
        # カラム名をチェック
        column_names = [str(col) for col in df.columns[:10]]
        sample_texts.extend(column_names)
        
        # 最初の数行のデータをチェック
        for i in range(min(3, len(df))):
            for j in range(min(5, len(df.columns))):
                sample_texts.append(str(df.iloc[i, j]))
        
        sample_text = ' '.join(sample_texts)
        
        # 1. 文字化けパターンの検出 (マイナス点)
        garbled_patterns = [
            ('��', -5),  # よくある文字化け記号
            ('����', -5),
            ('ï¿½', -5),
            ('\ufffd', -5),  # Unicode replacement character
            ('Ã¤', -3),    # UTF-8の文字化け
            ('Ã¯', -3),
            ('Ã¦', -3),
            ('â€', -3),
            ('ã¤', -3),    # 追加の文字化けパターン
            ('ã¯', -3),
            ('ã¦', -3),
            ('ã¨', -3),
            ('ã‚', -3),
            ('ã„', -3),
            ('ã†', -3),
            ('ã…', -3),
            ('ê', -2),     # MacRoman由来の文字化け
            ('ë', -2),
            ('è', -2),
            ('é', -2),
        ]
        
        for pattern, penalty in garbled_patterns:
            if pattern in sample_text:
                score += penalty
        
        # 2. 日本語文字の存在チェック (プラス点)
        if has_japanese_characters(sample_text):
            score += 5
            
            # より詳細な日本語文字チェック
            import re
            hiragana_count = len(re.findall(r'[\u3040-\u309F]', sample_text))
            katakana_count = len(re.findall(r'[\u30A0-\u30FF]', sample_text))
            kanji_count = len(re.findall(r'[\u4E00-\u9FAF]', sample_text))
            
            # 日本語文字の種類が多いほど高得点
            if hiragana_count > 0:
                score += 1
            if katakana_count > 0:
                score += 1
            if kanji_count > 0:
                score += 2
        
        # 3. 意味のある文字列の存在チェック（このファイル特有の内容も含む）
        meaningful_patterns = [
            'コード', 'データ', '実績', '予測', '計画', '分類', '年月',
            '商品', '売上', '需要', '在庫', '価格', '金額', '数量',
            '生産工場', '生産ライン', 'ABC区分', '出庫実績', 'ハイブリッド',
            '構成比率', '異常値', '須賀川'  # このファイル特有の内容
        ]
        
        matched_patterns = 0
        for pattern in meaningful_patterns:
            if pattern in sample_text:
                matched_patterns += 1
        
        # マッチした意味のあるパターンの数に応じてスコアを加算
        if matched_patterns >= 3:
            score += 3  # 多くのパターンがマッチした場合は高得点
        elif matched_patterns >= 1:
            score += 1
        
        # 4. 基本的な読み込み成功ボーナス
        score += 2
        
        # スコアを0-10の範囲に正規化
        return max(0, min(10, score))
        
    except Exception:
        return 0

def has_japanese_characters(text):
    """テキストに日本語文字が含まれているかチェック"""
    import re
    # ひらがな、カタカナ、漢字のUnicode範囲をチェック
    japanese_pattern = re.compile(r'[\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FAF]')
    return bool(japanese_pattern.search(text))

def validate_mapped_data(df):
    """マッピングされたデータの基本検証"""
    try:
        # 必須カラムの存在確認
        required_columns = ['P_code', 'Date', 'Actual', 'AI_pred', 'Plan_01']
        for col in required_columns:
            if col not in df.columns:
                st.error(f"❌ 必須カラム '{col}' が見つかりません")
                return False
        
        # データ型の確認
        numeric_columns = ['Actual', 'AI_pred', 'Plan_01']
        if 'Plan_02' in df.columns:
            numeric_columns.append('Plan_02')
        
        for col in numeric_columns:
            if not pd.api.types.is_numeric_dtype(df[col]):
                try:
                    # 数値変換を試行
                    df[col] = pd.to_numeric(df[col], errors='coerce')
                    null_count = df[col].isnull().sum()
                    if null_count > 0:
                        st.warning(f"⚠️ {col}列に{null_count}件の数値変換できないデータがありました（NaNに変換）")
                except:
                    st.error(f"❌ {col}列を数値型に変換できません")
                    return False
        
        # 基本統計情報の確認
        if len(df) == 0:
            st.error("❌ データが空です")
            return False
        
        st.success(f"✅ データ検証完了: {len(df)}件のデータ")
        return True
        
    except Exception as e:
        st.error(f"❌ データ検証エラー: {str(e)}")
        return False

def apply_monthly_correction(df):
    """月別合計値補正を適用"""
    corrected_df = df.copy()
    
    # 分類カラムが存在する場合は分類ごとに補正
    if 'category_code' in df.columns and df['category_code'].notna().any():
        category_col = 'category_code'
        categories = df[category_col].dropna().unique()
    else:
        # 分類がない場合は全体で補正
        category_col = None
        categories = [None]
    
    # Plan_02の存在確認
    has_plan_02 = 'Plan_02' in df.columns
    
    for category in categories:
        if category_col:
            category_data = corrected_df[corrected_df[category_col] == category]
        else:
            category_data = corrected_df
        
        # 月別の集計（Plan_02の存在に応じて動的に設定）
        agg_dict = {
            'AI_pred': 'sum',
            'Plan_01': 'sum'
        }
        
        if has_plan_02:
            agg_dict['Plan_02'] = 'sum'
        
        monthly_data = category_data.groupby('Date').agg(agg_dict).reset_index()
        
        for _, month_row in monthly_data.iterrows():
            date = month_row['Date']
            plan_01_total = month_row['Plan_01']
            ai_pred_total = month_row['AI_pred']
            
            # 補正係数の計算
            if ai_pred_total > 0:
                ai_correction_factor = plan_01_total / ai_pred_total
            else:
                ai_correction_factor = 1.0
            
            # AI予測の補正
            if category_col:
                mask = (corrected_df[category_col] == category) & (corrected_df['Date'] == date)
            else:
                mask = (corrected_df['Date'] == date)
            
            # データ型の互換性を保つため、明示的にfloat64型に変換してから計算
            corrected_df.loc[mask, 'AI_pred'] = corrected_df.loc[mask, 'AI_pred'].astype('float64') * ai_correction_factor
            
            # Plan_02が存在する場合のみ補正
            if has_plan_02:
                plan_02_total = month_row['Plan_02']
                if plan_02_total > 0:
                    plan_02_correction_factor = plan_01_total / plan_02_total
                    # データ型の互換性を保つため、明示的にfloat64型に変換してから計算
                    corrected_df.loc[mask, 'Plan_02'] = corrected_df.loc[mask, 'Plan_02'].astype('float64') * plan_02_correction_factor
    
    return corrected_df

def create_monthly_summary_table(df):
    """年月別集計結果テーブルを作成"""
    try:
        # 直近12か月のデータに制限
        if 'Date' not in df.columns:
            return pd.DataFrame()
        
        # 年月データの並び替え
        unique_dates = sorted(df['Date'].unique(), reverse=True)[:12]
        
        # 集計データの作成
        summary_data = []
        
        for date in reversed(unique_dates):  # 古い順に表示
            date_data = df[df['Date'] == date]
            
            # 年月のフォーマット
            date_str = str(date)
            if len(date_str) == 6:  # YYYYMM形式
                formatted_date = f"{date_str[:4]}年{date_str[4:6]}月"
            else:
                formatted_date = str(date)
            
            row = {
                '年月': formatted_date,
                '実績合計': int(date_data['Actual'].sum()),
                'AI予測': int(date_data['AI_pred'].sum()),
                '計画01': int(date_data['Plan_01'].sum())
            }
            
            # Plan_02が存在する場合は追加
            if 'Plan_02' in df.columns:
                row['計画02'] = int(date_data['Plan_02'].sum())
            
            summary_data.append(row)
        
        # 合計行を追加
        total_row = {
            '年月': '合計',
            '実績合計': int(df[df['Date'].isin(unique_dates)]['Actual'].sum()),
            'AI予測': int(df[df['Date'].isin(unique_dates)]['AI_pred'].sum()),
            '計画01': int(df[df['Date'].isin(unique_dates)]['Plan_01'].sum())
        }
        
        if 'Plan_02' in df.columns:
            total_row['計画02'] = int(df[df['Date'].isin(unique_dates)]['Plan_02'].sum())
        
        summary_data.append(total_row)
        
        return pd.DataFrame(summary_data)
        
    except Exception as e:
        st.error(f"年月別集計テーブル作成エラー: {str(e)}")
        return pd.DataFrame() 