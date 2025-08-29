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
    
    # カスタムCSS（UI/UXデザインガイド準拠）
    st.markdown("""
    <style>
    .main-title {
        font-size: 2.2em;
        font-weight: bold;
        color: #1976d2;
        margin-bottom: 1em;
        margin-top: 1em;
    }
    .main-description {
        color: #666666;
        font-size: 1.05em;
        margin-bottom: 2em;
        line-height: 1.6;
    }
    .step-title {
        font-size: 1.4em;
        font-weight: bold;
        color: #1976d2;
        border-left: 4px solid #1976d2;
        padding-left: 12px;
        margin-bottom: 1em;
        margin-top: 2em;
    }
    .step-annotation {
        color: #666666;
        font-size: 0.95em;
        margin-bottom: 1.2em;
    }
    .section-subtitle {
        font-size: 1.1em;
        font-weight: bold;
        color: #333333;
        margin-bottom: 0.8em;
        margin-top: 1.2em;
    }
    .result-section {
        margin-top: 1.5em;
        margin-bottom: 2em;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # セッション状態の初期化
    if 'original_data' not in st.session_state:
        st.session_state.original_data = None
    if 'uploaded_filename' not in st.session_state:
        st.session_state.uploaded_filename = None
    if 'data_columns' not in st.session_state:
        st.session_state.data_columns = []
    if 'current_mapping' not in st.session_state:
        st.session_state.current_mapping = {}
    if 'mapping_completed' not in st.session_state:
        st.session_state.mapping_completed = False
    if 'monthly_correction_enabled' not in st.session_state:
        st.session_state.monthly_correction_enabled = False
    if 'monthly_correction_completed' not in st.session_state:
        st.session_state.monthly_correction_completed = False
    if 'abc_categories' not in st.session_state:
        st.session_state.abc_categories = ABC_CLASSIFICATION_SETTINGS['default_categories'].copy()
    if 'abc_auto_generate' not in st.session_state:
        st.session_state.abc_auto_generate = True
    if 'abc_setting_mode' not in st.session_state:
        st.session_state.abc_setting_mode = 'ratio'
    if 'abc_quantity_categories' not in st.session_state:
        st.session_state.abc_quantity_categories = [
            {'name': 'A', 'min_value': 1000, 'description': 'A区分：高実績商品'},
            {'name': 'B', 'min_value': 100, 'description': 'B区分：中実績商品'},
            {'name': 'C', 'min_value': 0, 'description': 'C区分：低実績商品'}
        ]
    if 'selected_generation_categories' not in st.session_state:
        st.session_state.selected_generation_categories = []
    if 'abc_generation_completed' not in st.session_state:
        st.session_state.abc_generation_completed = False
    if 'custom_column_names' not in st.session_state:
        st.session_state.custom_column_names = {
            'Plan_01': '計画01',
            'Plan_02': '計画02',
            'AI_pred': 'AI予測値'
        }
    
    # 大項目タイトル（STEP1スタイルに統一）
    st.markdown("""
    <div style="
        background: #e8f4fd;
        color: #1976d2;
        padding: 1rem 1.5rem;
        border-radius: 12px;
        text-align: left;
        margin-bottom: 1rem;
        box-shadow: 0 1px 4px rgba(33, 150, 243, 0.1);
    ">
        <h2 style="
            font-size: 1.9rem;
            margin: 0 0 0.2rem 0;
            font-weight: 600;
            color: #1976d2;
        ">■ データセット作成</h2>
        <p style="
            font-size: 1.05rem;
            margin: 0;
            color: #4a90e2;
            line-height: 1.6;
        ">このセクションでは、AI予測値と現行計画値の精度を比較・分析するために必要なCSVデータを読み込み、分析用のデータセットを作成します。</p>
    </div>
    """, unsafe_allow_html=True)
    
    # STEP 1: CSVファイルアップロード
    show_step1()
    
    # STEP 2: データマッピング（データが読み込まれた場合のみ表示）
    if st.session_state.original_data is not None:
        show_step2()
    
    # STEP 3: 月別合計値補正（マッピングが完了した場合のみ表示）
    if st.session_state.mapping_completed:
        show_step3()
    
    # STEP 4: ABC区分自動生成（マッピングが完了した場合のみ表示）
    if st.session_state.mapping_completed:
        show_step4()

def show_step1():
    """STEP 1: CSVファイルアップロード"""
    st.markdown('<div class="step-title">CSVファイルアップロード</div>', unsafe_allow_html=True)
    st.markdown('<div class="step-annotation">Browse filesでファイルを指定、またはCSVファイルをドラッグ＆ドロップしてください。</div>', unsafe_allow_html=True)
    
    uploaded_file = st.file_uploader(
        "ファイル選択",
        type=['csv'],
        help=HELP_TEXTS['file_upload_help'],
        label_visibility="collapsed"
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
                st.session_state.monthly_correction_completed = False
                st.session_state.abc_generation_completed = False
                
                st.success(f"✅ データを読み込みました（{len(df)}行×{len(df.columns)}列）。下記にプレビューを表示します。")
                
            except Exception as e:
                st.error(f"❌ ファイル読み込みエラー: {str(e)}")
                return
    
    # データプレビューの表示（読み込み済みファイル情報は削除）
    if st.session_state.original_data is not None:
        
        # データプレビュー
        st.markdown('<div class="result-section">', unsafe_allow_html=True)
        st.markdown(f'<div class="section-subtitle">データプレビュー（上位{DATA_PROCESSING_CONSTANTS["default_preview_rows"]}件）</div>', unsafe_allow_html=True)
        
        df = st.session_state.original_data
        preview_df = df.head(DATA_PROCESSING_CONSTANTS['default_preview_rows']).copy()
        preview_df.index = range(UI_DISPLAY_CONSTANTS['selectbox_start_index'], len(preview_df) + UI_DISPLAY_CONSTANTS['selectbox_start_index'])
        st.dataframe(preview_df, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

def show_step2():
    """STEP 2: データマッピング"""
    st.markdown('<div class="step-title">データマッピング</div>', unsafe_allow_html=True)
    st.markdown('<div class="step-annotation">CSVのカラム名をシステム項目にマッピングしてください（基本的に1回のみ実行）。</div>', unsafe_allow_html=True)
    
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
        
        # 任意項目の説明を追加
        # スペース調整用
        st.markdown('<div style="margin-bottom: 0.5rem;"></div>', unsafe_allow_html=True)
        
        # ABC区分の選択（任意項目に移動）
        mapping['Class_abc'] = st.selectbox(
            "ABC区分（Class_abc）",
            options=[''] + st.session_state.data_columns,
            index=get_selectbox_index(st.session_state.data_columns, st.session_state.current_mapping.get('Class_abc', '')),
            help=HELP_TEXTS['abc_class_help']
        )
    
    # 任意項目についての説明
    st.markdown("---")
    st.markdown('<div class="step-annotation">※ 任意項目について：詳細分析を行う場合は「分類」の設定を、既にABC区分を設定済みの場合は「ABC区分」をマッピングしてください。</div>', unsafe_allow_html=True)
    
    # 項目名変更機能の追加
    with st.expander("項目名カスタマイズ（任意）"):
        st.markdown('<div class="step-annotation">「計画値01」「計画値02」「AI予測値」の項目名は変更可能です。その他の項目は、システム項目として固定です。</div>', unsafe_allow_html=True)
        
        col_custom1, col_custom2, col_custom3 = st.columns(3)
        
        with col_custom1:
            st.session_state.custom_column_names['Plan_01'] = st.text_input(
                "計画値01の表示名",
                value=st.session_state.custom_column_names['Plan_01'],
                max_chars=20
            )
        
        with col_custom2:
            st.session_state.custom_column_names['Plan_02'] = st.text_input(
                "計画値02の表示名",
                value=st.session_state.custom_column_names['Plan_02'],
                max_chars=20
            )
        
        with col_custom3:
            st.session_state.custom_column_names['AI_pred'] = st.text_input(
                "AI予測値の表示名",
                value=st.session_state.custom_column_names['AI_pred'],
                max_chars=20
            )
    
    # 現在のマッピング状態を更新
    st.session_state.current_mapping = mapping
    
    # マッピング実行ボタン
    if st.button("マッピング設定を適用する", type="primary", use_container_width=True):
        # 必須項目のチェック
        required_fields = ['P_code', 'Date', 'Actual', 'AI_pred', 'Plan_01']
        missing_fields = [field for field in required_fields if not mapping.get(field)]
        
        if missing_fields:
            st.error(f"❌ 必須項目が未設定です: {', '.join(missing_fields)}")
        else:
            try:
                # データマッピング実行
                with st.status("🔄 データマッピング実行中...", expanded=True) as status:
                    st.write("カラム名を変換中...")
                    
                    mapped_df = apply_mapping(st.session_state.original_data, mapping)
                    
                    # データ検証
                    st.write("🔍 データを検証中...")
                    validation_result = validate_mapped_data(mapped_df)
                    
                    if validation_result:
                        st.session_state.data = mapped_df
                        st.session_state.mapping = mapping
                        st.session_state.mapping_completed = True
                        st.write("✅ データマッピング完了")
                        status.update(label="✅ データマッピング完了", state="complete")
                        st.rerun()
                    else:
                        st.error("❌ データ検証でエラーが発生しました")
                        status.update(label="❌ データ検証エラー", state="error")
                        
            except Exception as e:
                st.error(f"❌ マッピング処理エラー: {str(e)}")
    
    # マッピング結果の表示
    if st.session_state.mapping_completed:
        st.markdown('<div class="result-section">', unsafe_allow_html=True)
        st.success("✅ マッピングが完了しました。変換後のデータプレビューを下記に表示していますので、ご確認ください。")
        
        # 変換後データプレビュー
        st.markdown('<div class="section-subtitle">変換後データプレビュー（上位5件）</div>', unsafe_allow_html=True)
        preview_df = st.session_state.data.head(5).copy()
        preview_df.index = range(1, len(preview_df) + 1)
        
        # 年月の表示形式を統一（YYYYMM → YYYY年MM月）
        if 'Date' in preview_df.columns:
            preview_df['Date'] = preview_df['Date'].apply(lambda x: 
                f"{str(x)[:4]}年{str(x)[4:6]}月" if len(str(x)) == 6 else str(x)
            )
        
        # カスタム項目名を反映
        display_names = get_display_column_names()
        preview_df_display = preview_df.copy()
        for col in preview_df_display.columns:
            if col in display_names:
                preview_df_display = preview_df_display.rename(columns={col: display_names[col]})
        
        st.dataframe(preview_df_display, use_container_width=True)
        
        st.markdown('</div>', unsafe_allow_html=True)

def show_step3():
    """STEP 3: 月別合計値補正"""
    st.markdown('<div class="step-title">月別合計値補正</div>', unsafe_allow_html=True)
    st.markdown('<div class="step-annotation">分類ごとの月別合計値を計画値01に合わせて調整します。AI予測値および計画値02（存在する場合）が対象です。</div>', unsafe_allow_html=True)
    
    # 月別合計値補正の選択
    st.session_state.monthly_correction_enabled = st.checkbox(
        "月別合計値補正を実行する（全分類対象）",
        value=st.session_state.monthly_correction_enabled
    )
    
    if st.session_state.monthly_correction_enabled and not st.session_state.monthly_correction_completed:
        # 補正実行
        try:
            with st.status("🔄 月別合計値補正を実行中...", expanded=True) as status:
                st.write("分類ごとの月別合計値を分析中...")
                
                corrected_df = apply_monthly_correction(st.session_state.data)
                st.session_state.data = corrected_df
                st.session_state.monthly_correction_completed = True
                
                st.write("✅ 月別合計値補正完了")
                status.update(label="✅ 月別合計値補正完了", state="complete")
                st.rerun()
                
        except Exception as e:
            st.error(f"❌ 月別合計値補正エラー: {str(e)}")
    
    # 結果表示
    if st.session_state.monthly_correction_completed:
        st.markdown('<div class="result-section">', unsafe_allow_html=True)
        st.success("✅ 年月別データの集計結果です。月別合計値補正を実施した場合は、AI予測値と計画値の月別合計が一致しているかをご確認ください。")
        
        # 分類フィルター（エラー防止強化版）
        selected_category = '全て'  # デフォルト値
        
        try:
            # 分類データの存在確認と安全な処理
            has_category_data = False
            category_options = ['全て']
            
            if 'category_code' in st.session_state.data.columns:
                # 分類データの取得（null値を除外し、文字列として処理）
                category_values = st.session_state.data['category_code'].dropna()
                if not category_values.empty:
                    # 文字列変換して重複を除去
                    unique_categories = sorted(list(set(category_values.astype(str))))
                    if unique_categories:
                        category_options.extend(unique_categories)
                        has_category_data = True
            
            # 分類フィルターの表示
            if has_category_data:
                selected_category = st.selectbox(
                    "分類フィルター", 
                    category_options,
                    key="monthly_summary_filter",
                    help="分類ごとの月別合計値を確認できます"
                )
            else:
                pass  # 分類データがない場合は注釈を削除
        
        except Exception as e:
            st.warning(f"⚠️ 分類フィルター処理中にエラーが発生しました: {str(e)}")
            st.info("全データを表示します。")
        
        # 月別集計表の表示（フィルター適用）
        try:
            # 分類フィルターが適用された場合の処理
            if selected_category != '全て' and 'category_code' in st.session_state.data.columns:
                # 選択された分類でフィルタリング
                filtered_data = st.session_state.data[
                    st.session_state.data['category_code'].astype(str) == selected_category
                ]
                if not filtered_data.empty:
                    monthly_summary = create_monthly_summary_table(filtered_data)
                else:
                    st.warning(f"⚠️ 選択された分類「{selected_category}」にデータが見つかりません。")
                    monthly_summary = create_monthly_summary_table(st.session_state.data)
            else:
                # 全データまたは分類フィルターなしの場合
                monthly_summary = create_monthly_summary_table(st.session_state.data)
            
            # テーブル表示（Streamlit標準のcolumn_configで数値項目を左詰めカンマ付き）
            if not monthly_summary.empty:
                # カラム設定を動的に作成（均等割り）
                column_config = {
                    "年月": st.column_config.TextColumn(
                        "年月",
                        help="対象年月",
                        width="medium"
                    ),
                    "実績合計": st.column_config.TextColumn(
                        "実績合計",
                        help="実績値の合計",
                        width="medium"
                    )
                }
                
                # 動的なカラム名に対応
                for col in monthly_summary.columns:
                    if col not in ["年月", "実績合計"]:
                        column_config[col] = st.column_config.TextColumn(
                            col,
                            help=f"{col}の合計値",
                            width="medium"
                        )
                
                # 数値項目にカンマを追加
                formatted_summary = monthly_summary.copy()
                for col in formatted_summary.columns:
                    if col != "年月":  # 年月以外の数値項目
                        formatted_summary[col] = formatted_summary[col].apply(
                            lambda x: f"{x:,}" if isinstance(x, (int, float)) and str(x) != "合計" else x
                        )
                
                st.dataframe(
                    formatted_summary, 
                    use_container_width=True, 
                    hide_index=True,
                    column_config=column_config
                )
            else:
                st.warning("⚠️ 表示するデータがありません。")
                
        except Exception as e:
            st.error(f"❌ 月別集計表作成エラー: {str(e)}")
            st.info("データの内容を確認してください。")
        
        st.markdown('</div>', unsafe_allow_html=True)

def show_step4():
    """STEP 4: ABC区分自動生成"""
    st.markdown('<div class="step-title">ABC区分自動生成</div>', unsafe_allow_html=True)
    st.markdown('<div class="step-annotation">ABC区分を自動生成するか、既存を使用するかを選択してください。※ 一部分類のみを対象とした自動生成も可能です。</div>', unsafe_allow_html=True)
    
    # ABC区分生成の選択肢（排他制御に変更）
    col1, col2 = st.columns(2)
    
    with col1:
        execute_abc_generation = st.checkbox("ABC区分を自動生成する（分類単位）")
    
    with col2:
        use_existing_abc = st.checkbox("既存のABC区分を使用する（全分類）", disabled=execute_abc_generation)
    
    # 排他制御: 一方が選択されたら他方を無効化
    if execute_abc_generation and use_existing_abc:
        st.session_state.use_existing_abc = False
        use_existing_abc = False
        st.rerun()
    
    if execute_abc_generation:
        # 区分設定方式の選択
        st.markdown('<div class="section-subtitle">設定方法</div>', unsafe_allow_html=True)
        abc_method_col1, abc_method_col2 = st.columns(2)
        
        with abc_method_col1:
            if st.radio("区分設定方式", ["構成比率範囲", "数量範囲"], horizontal=True) == "構成比率範囲":
                st.session_state.abc_setting_mode = 'ratio'
            else:
                st.session_state.abc_setting_mode = 'quantity'
        
        # 対象分類の選択
        if 'category_code' in st.session_state.data.columns:
            st.markdown('<div class="section-subtitle">対象分類選択</div>', unsafe_allow_html=True)
            available_categories = sorted(st.session_state.data['category_code'].dropna().unique().tolist())
            # 「全て」選択肢を先頭に追加
            category_options = ['全て'] + available_categories
            
            # 現在の選択状態を確認・調整
            current_selection = st.session_state.selected_generation_categories if hasattr(st.session_state, 'selected_generation_categories') else []
            
            selected_categories = st.multiselect(
                "「分類」フィルター（※ 複数選択可）",
                category_options,
                default=current_selection if current_selection else ['全て']
            )
            
            # 「全て」が選択された場合の処理
            if '全て' in selected_categories:
                # 「全て」と他の項目が同時選択された場合は「全て」のみにする
                if len(selected_categories) > 1:
                    selected_categories = ['全て']
                    st.rerun()
                st.session_state.selected_generation_categories = []  # 全分類対象の場合は空リストで処理
                st.info("💡 「全て」を選択：すべての分類に対して、同じ基準で分類単位ごとにABC区分を自動生成します。")
            else:
                st.session_state.selected_generation_categories = selected_categories
        
        # ABC区分設定の詳細設定
        show_abc_settings()
        
        # 実行ボタン
        if st.button("ABC区分自動生成を実行する", type="primary", use_container_width=True):
            execute_abc_generation_process()
    
    elif use_existing_abc:
        st.info("💡 既存のABC区分をそのまま使用して集計結果を表示します。")
        if st.button("既存区分で集計のみ行う", type="secondary", use_container_width=True):
            st.session_state.abc_generation_completed = True
    
    # 結果表示
    if st.session_state.abc_generation_completed:
        st.markdown('<div class="result-section">', unsafe_allow_html=True)
        st.success("✅ ABC区分の集計結果です。分類単位で内容を確認のうえ、必要に応じて分類フィルターで対象を選択し、ABC区分の自動生成を繰り返し実行してください。")
        
        # ABC区分集計結果の表示
        show_abc_generation_results()
        
        st.markdown('<div class="step-annotation">分類単位で複数回実行可能です。必要に応じて、分類フィルターから対象を選択して再実行してください。</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

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
    """データフレームにマッピングを適用（カスタム項目名対応）"""
    mapped_df = pd.DataFrame()
    
    for system_field, csv_column in mapping.items():
        if csv_column and csv_column in df.columns:
            mapped_df[system_field] = df[csv_column]
    
    # ABC区分が未選択の場合は「未区分」で補完
    if 'Class_abc' not in mapped_df.columns or mapped_df['Class_abc'].isna().all():
        mapped_df['Class_abc'] = '未区分'
    
    # 分類データの安全な処理
    if 'category_code' in mapped_df.columns:
        # null値や空文字を適切に処理
        mapped_df['category_code'] = mapped_df['category_code'].fillna('未分類')
        # 文字列型に統一
        mapped_df['category_code'] = mapped_df['category_code'].astype(str)
        # 空文字列を「未分類」に置換
        mapped_df['category_code'] = mapped_df['category_code'].replace('', '未分類')
    
    return mapped_df

def get_display_column_names():
    """表示用のカラム名を取得"""
    display_names = COLUMN_MAPPING.copy()
    
    # カスタム項目名を反映
    if 'custom_column_names' in st.session_state:
        for key, custom_name in st.session_state.custom_column_names.items():
            if custom_name.strip():  # 空でない場合のみ
                # 10文字以内に省略
                if len(custom_name) > 10:
                    display_names[key] = custom_name[:9] + '…'
                else:
                    display_names[key] = custom_name
    
    return display_names

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
        
        # カスタマイズされた項目名を取得
        def get_custom_column_name(col_key):
            """カスタマイズされた項目名を取得（10文字制限付き）"""
            if 'custom_column_names' in st.session_state and col_key in st.session_state.custom_column_names:
                custom_name = st.session_state.custom_column_names[col_key].strip()
                if custom_name:
                    # 全角10文字を超える場合は省略
                    if len(custom_name) > 10:
                        return custom_name[:9] + '…'
                    else:
                        return custom_name
            
            # デフォルト名称
            defaults = {
                'AI_pred': 'AI予測',
                'Plan_01': '計画01',
                'Plan_02': '計画02'
            }
            return defaults.get(col_key, col_key)
        
        # カスタム項目名を取得
        ai_pred_name = get_custom_column_name('AI_pred')
        plan_01_name = get_custom_column_name('Plan_01')
        plan_02_name = get_custom_column_name('Plan_02')
        
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
                ai_pred_name: int(date_data['AI_pred'].sum()),
                plan_01_name: int(date_data['Plan_01'].sum())
            }
            
            # Plan_02が存在する場合は追加
            if 'Plan_02' in df.columns:
                row[plan_02_name] = int(date_data['Plan_02'].sum())
            
            summary_data.append(row)
        
        # 合計行を追加
        total_row = {
            '年月': '合計',
            '実績合計': int(df[df['Date'].isin(unique_dates)]['Actual'].sum()),
            ai_pred_name: int(df[df['Date'].isin(unique_dates)]['AI_pred'].sum()),
            plan_01_name: int(df[df['Date'].isin(unique_dates)]['Plan_01'].sum())
        }
        
        if 'Plan_02' in df.columns:
            total_row[plan_02_name] = int(df[df['Date'].isin(unique_dates)]['Plan_02'].sum())
        
        summary_data.append(total_row)
        
        result_df = pd.DataFrame(summary_data)
        
        return result_df
        
    except Exception as e:
        st.error(f"年月別集計テーブル作成エラー: {str(e)}")
        return pd.DataFrame()

def show_abc_settings():
    """ABC区分設定の詳細設定画面を表示"""
    if st.session_state.abc_setting_mode == 'ratio':
        show_ratio_settings()
    else:
        show_quantity_settings()

def show_ratio_settings():
    """構成比率範囲設定画面"""
    st.markdown("**構成比率範囲設定**")
    st.info(ABC_EXPLANATION['category_description_ratio'])
    
    # 区分の追加
    col1, col2 = st.columns([3, 1])
    with col1:
        additional_options = [''] + [f"{cat['name']}区分" for cat in ABC_CLASSIFICATION_SETTINGS['additional_categories']]
        new_category_display = st.selectbox("追加する区分", options=additional_options)
    with col2:
        if st.button("区分を追加する", disabled=not new_category_display):
            add_abc_category(new_category_display.replace('区分', ''), 'ratio')
    
    # 区分設定の編集
    edited_categories = []
    for i, category in enumerate(st.session_state.abc_categories):
        col1, col2, col3, col4 = st.columns([1, 2, 2, 1])
        
        with col1:
            st.markdown(f"**{category['name']}区分**")
        
        with col2:
            start_ratio = 0.0 if i == 0 else edited_categories[i-1]['end_ratio']
            st.number_input(
                f"開始%", 
                value=start_ratio * 100, 
                disabled=True, 
                step=1.0,
                format="%.1f",
                key=f"start_{i}"
            )
        
        with col3:
            is_last = (i == len(st.session_state.abc_categories) - 1)
            if is_last:
                end_ratio = 1.0
                st.number_input(
                    f"終了%", 
                    value=100.0, 
                    disabled=True, 
                    step=1.0,
                    format="%.1f",
                    key=f"end_{i}"
                )
            else:
                end_ratio = st.number_input(
                    f"終了%",
                    min_value=(start_ratio * 100) + 0.1,
                    max_value=100.0,
                    value=category['end_ratio'] * 100,
                    step=1.0,
                    format="%.1f",
                    key=f"end_{i}",
                    help="整数（例：25）または小数（例：25.5）を入力できます。前の区分の終了値より大きい値を入力してください。"
                ) / 100.0
        
        with col4:
            if len(st.session_state.abc_categories) > 1 and st.button("🗑️", key=f"delete_{i}"):
                st.session_state.abc_categories.pop(i)
                st.rerun()
        
        edited_categories.append({
            'name': category['name'],
            'start_ratio': start_ratio,
            'end_ratio': end_ratio,
            'description': category.get('description', f'{category["name"]}区分')
        })
    
    st.session_state.abc_categories = edited_categories

def show_quantity_settings():
    """数量範囲設定画面"""
    st.markdown("**数量範囲設定**")
    st.info(ABC_EXPLANATION['category_description_quantity'])
    
    # 区分の追加
    col1, col2 = st.columns([3, 1])
    with col1:
        additional_options = [''] + [f"{cat['name']}区分" for cat in ABC_CLASSIFICATION_SETTINGS['additional_categories']]
        new_category_display = st.selectbox("追加する区分", options=additional_options, key="qty_add")
    with col2:
        if st.button("区分を追加する", disabled=not new_category_display, key="add_qty_btn"):
            add_abc_category(new_category_display.replace('区分', ''), 'quantity')
    
    # 区分設定の編集
    edited_categories = []
    for i, category in enumerate(st.session_state.abc_quantity_categories):
        col1, col2, col3, col4 = st.columns([1, 2, 2, 1])
        
        with col1:
            st.markdown(f"**{category['name']}区分**")
        
        with col2:
            st.markdown("上限：――")
        
        with col3:
            is_last = (i == len(st.session_state.abc_quantity_categories) - 1)
            if is_last:
                min_value = 0
                st.number_input(
                    "下限値", 
                    value=0, 
                    disabled=True, 
                    step=1,
                    format="%d",
                    key=f"qty_min_{i}"
                )
            else:
                min_value = st.number_input(
                    "下限値",
                    min_value=0,
                    value=category.get('min_value', 0),
                    step=1,
                    format="%d",
                    key=f"qty_min_{i}",
                    help="整数値を入力してください（例：100）"
                )
        
        with col4:
            if len(st.session_state.abc_quantity_categories) > 1 and st.button("🗑️", key=f"qty_delete_{i}"):
                st.session_state.abc_quantity_categories.pop(i)
                st.rerun()
        
        edited_categories.append({
            'name': category['name'],
            'min_value': min_value,
            'description': category.get('description', f'{category["name"]}区分')
        })
    
    st.session_state.abc_quantity_categories = edited_categories

def add_abc_category(category_name, mode):
    """ABC区分の追加"""
    if mode == 'ratio':
        existing_names = [cat['name'] for cat in st.session_state.abc_categories]
        if category_name not in existing_names:
            last_end = max([cat['end_ratio'] for cat in st.session_state.abc_categories]) if st.session_state.abc_categories else 0.0
            # より実用的なデフォルト値を設定（10%刻み）
            default_increment = 0.1  # 10%
            new_end_ratio = min(1.0, last_end + default_increment)
            # 整数パーセンテージになるよう調整
            new_end_ratio = round(new_end_ratio, 1)
            
            new_category = {
                'name': category_name,
                'start_ratio': last_end,
                'end_ratio': new_end_ratio,
                'description': f'{category_name}区分'
            }
            st.session_state.abc_categories.append(new_category)
            st.rerun()
    else:
        existing_names = [cat['name'] for cat in st.session_state.abc_quantity_categories]
        if category_name not in existing_names:
            # より実用的なデフォルト値を設定
            default_min_value = 100  # 100単位のデフォルト値
            
            new_category = {
                'name': category_name,
                'min_value': default_min_value,
                'description': f'{category_name}区分'
            }
            st.session_state.abc_quantity_categories.append(new_category)
            st.rerun()

def execute_abc_generation_process():
    """ABC区分自動生成処理の実行"""
    try:
        with st.status("🔄 ABC区分を自動生成中...", expanded=True) as status:
            st.write("実績値データを分析中...")
            
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
            
            # 処理対象の決定
            target_categories = st.session_state.selected_generation_categories if st.session_state.selected_generation_categories else None
            preserve_existing = True
            
            # ABC区分の計算
            mapped_df = st.session_state.data.copy()
            
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
            
            st.session_state.data = mapped_df
            st.session_state.abc_generation_completed = True
            
            st.write("✅ ABC区分の割り当て完了")
            status.update(label="✅ ABC区分自動生成完了", state="complete")
            st.rerun()
            
    except Exception as e:
        st.error(f"❌ ABC区分計算エラー: {str(e)}")

def show_abc_generation_results():
    """ABC区分生成結果の表示"""
    abc_summary = get_abc_classification_summary(st.session_state.data, 'Class_abc', 'Actual')
    
    if abc_summary:
        # 分類フィルター
        if 'category_code' in st.session_state.data.columns:
            categories = ['全て'] + sorted(st.session_state.data['category_code'].dropna().unique().tolist())
            selected_category = st.selectbox("分類フィルター", categories, key="abc_filter")
            
            if selected_category != '全て':
                filtered_data = st.session_state.data[st.session_state.data['category_code'] == selected_category]
                abc_summary = get_abc_classification_summary(filtered_data, 'Class_abc', 'Actual')
        
        # 結果テーブルの作成
        abc_result_data = []
        total_count = 0
        total_actual = 0
        
        sorted_categories = sorted(abc_summary['counts'].keys())
        
        for category in sorted_categories:
            count = abc_summary['counts'].get(category, 0)
            ratio = abc_summary['ratios'].get(category, 0)
            actual_sum = abc_summary['actual_sums'].get(category, 0)
            
            abc_result_data.append({
                'ABC区分': f"{category}区分",
                '件数': count,
                '実績合計': actual_sum,
                '構成比率（%）': f"{ratio:.2f}%"
            })
            total_count += count
            total_actual += actual_sum
        
        # 合計行を追加
        abc_result_data.append({
            'ABC区分': '合計',
            '件数': total_count,
            '実績合計': total_actual,
            '構成比率（%）': "100.00%"
        })
        
        result_df = pd.DataFrame(abc_result_data)
        
        # 数値項目にカンマを追加
        formatted_abc_df = result_df.copy()
        formatted_abc_df['件数'] = formatted_abc_df['件数'].apply(
            lambda x: f"{x:,}" if isinstance(x, (int, float)) else x
        )
        formatted_abc_df['実績合計'] = formatted_abc_df['実績合計'].apply(
            lambda x: f"{x:,.0f}" if isinstance(x, (int, float)) else x
        )
        
        # Streamlit標準のcolumn_configで数値項目を左詰めカンマ付き表示（均等割り）
        st.dataframe(
            formatted_abc_df, 
            use_container_width=True, 
            hide_index=True,
            column_config={
                "ABC区分": st.column_config.TextColumn(
                    "ABC区分",
                    help="ABC区分の分類",
                    width="medium"
                ),
                "件数": st.column_config.TextColumn(
                    "件数",
                    help="該当する商品の件数",
                    width="medium"
                ),
                "実績合計": st.column_config.TextColumn(
                    "実績合計",
                    help="実績値の合計",
                    width="medium"
                ),
                "構成比率（%）": st.column_config.TextColumn(
                    "構成比率（%）",
                    help="全体に占める構成比率",
                    width="medium"
                )
            }
        )