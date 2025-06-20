import streamlit as st
import pandas as pd
import numpy as np
import chardet
from utils.validators import validate_data, validate_required_columns
from utils.data_processor import (
    preview_data, 
    calculate_abc_classification, 
    validate_abc_categories, 
    get_abc_classification_summary
)
from config.settings import ABC_CLASSIFICATION_SETTINGS, COLUMN_MAPPING

def show():
    """データアップロードページを表示"""
    st.header("📤 データアップロード")
    
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
    
    # アップロードセクション
    st.subheader("1. CSVファイルアップロード")
    uploaded_file = st.file_uploader(
        "CSVファイルを選択してください",
        type=['csv'],
        help="分析対象のCSVファイルをアップロードしてください"
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
        st.subheader("2. データプレビュー（上位10件表示）")
        # インデックスを1始まりに変更
        preview_df = df.head(10).copy()
        preview_df.index = range(1, len(preview_df) + 1)
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
                "商品コード",
                options=[''] + st.session_state.data_columns,
                index=get_selectbox_index(st.session_state.data_columns, st.session_state.current_mapping.get('P_code', '')),
                help="商品を識別するコード（必須）"
            )
            mapping['Date'] = st.selectbox(
                "年月",
                options=[''] + st.session_state.data_columns,
                index=get_selectbox_index(st.session_state.data_columns, st.session_state.current_mapping.get('Date', '')),
                help="YYYYMM形式の年月データ（必須）"
            )
            mapping['Actual'] = st.selectbox(
                "実績値",
                options=[''] + st.session_state.data_columns,
                index=get_selectbox_index(st.session_state.data_columns, st.session_state.current_mapping.get('Actual', '')),
                help="実際の売上・需要実績（必須）"
            )
            mapping['AI_pred'] = st.selectbox(
                "AI予測値",
                options=[''] + st.session_state.data_columns,
                index=get_selectbox_index(st.session_state.data_columns, st.session_state.current_mapping.get('AI_pred', '')),
                help="AIによる予測値（必須）"
            )
            mapping['Plan_01'] = st.selectbox(
                "計画値01",
                options=[''] + st.session_state.data_columns,
                index=get_selectbox_index(st.session_state.data_columns, st.session_state.current_mapping.get('Plan_01', '')),
                help="基準となる計画値（必須）"
            )
            
            # ABC区分を必須項目として追加
            st.markdown("**ABC区分設定（必須）**")
            mapping['Class_abc'] = st.selectbox(
                "ABC区分",
                options=[''] + st.session_state.data_columns,
                index=get_selectbox_index(st.session_state.data_columns, st.session_state.current_mapping.get('Class_abc', '')),
                help="CSVファイルにABC区分がある場合は選択してください"
            )
            
            # ABC区分の自動生成設定
            abc_has_column = bool(mapping['Class_abc'])
            if not abc_has_column:
                st.info("💡 ABC区分が選択されていないため、実績値に基づいて自動生成されます")
                st.session_state.abc_auto_generate = True
            else:
                st.session_state.abc_auto_generate = st.checkbox(
                    "ABC区分を自動生成で上書きする", 
                    value=False,
                    help="チェックすると、CSVのABC区分を無視して実績値から自動計算します"
                )
            
        with col2:
            st.markdown("**任意項目**")
            mapping['Class_01'] = st.selectbox(
                "分類01",
                options=[''] + st.session_state.data_columns,
                index=get_selectbox_index(st.session_state.data_columns, st.session_state.current_mapping.get('Class_01', '')),
                help="商品分類・カテゴリ1（任意）"
            )
            mapping['Class_02'] = st.selectbox(
                "分類02",
                options=[''] + st.session_state.data_columns,
                index=get_selectbox_index(st.session_state.data_columns, st.session_state.current_mapping.get('Class_02', '')),
                help="商品分類・カテゴリ2（任意）"
            )
            mapping['Plan_02'] = st.selectbox(
                "計画値02",
                options=[''] + st.session_state.data_columns,
                index=get_selectbox_index(st.session_state.data_columns, st.session_state.current_mapping.get('Plan_02', '')),
                help="比較用の計画値（任意）"
            )
        
        # 現在のマッピング状態を更新
        st.session_state.current_mapping = mapping
        
        # ABC区分設定エクスパンダー（常に表示）
        with st.expander("🔧 ABC区分自動生成設定", expanded=st.session_state.abc_auto_generate):
                # 現在の状態表示
                if st.session_state.abc_auto_generate:
                    st.success("🟢 **自動生成モード**: 実績値に基づいてABC区分を自動計算します")
                else:
                    st.info("🟡 **手動指定モード**: CSVファイルのABC区分を使用します")
                
                st.markdown("### 自動生成時の区分追加")
                st.markdown("実績値の多い順にソートし、累積構成比率をもとに以下の区分を割り当てます：")
                
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
                        help="D区分, E区分, F区分, G区分, H区分, Z区分を追加できます"
                    )
                with col2:
                    st.write("")  # ラベルと高さを合わせるための空白
                    if st.button("区分を追加する", type="primary", disabled=not new_category_display):
                        # 表示名から区分名を抽出（「D区分」→「D」）
                        new_category_name = new_category_display.replace('区分', '')
                        
                        # 既存の区分名と重複チェック
                        existing_names = [cat['name'] for cat in st.session_state.abc_categories]
                        if new_category_name not in existing_names:
                            # 新しい区分を末尾に追加（デフォルト範囲は最後の区分の後）
                            last_end = max([cat['end_ratio'] for cat in st.session_state.abc_categories]) if st.session_state.abc_categories else 0.0
                            new_category = {
                                'name': new_category_name,
                                'start_ratio': last_end,
                                'end_ratio': min(1.0, last_end + 0.1),
                                'description': f'{new_category_name}区分'
                            }
                            st.session_state.abc_categories.append(new_category)
                            st.rerun()
                        else:
                            st.warning(f"区分 '{new_category_display}' は既に存在します")
                
                # 区分設定の編集
                st.markdown("### 各区分の構成比率の範囲設定")
                
                # 凡例表示を削除し、CSS スタイリングのみ保持
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
                        # 区分名を入力欄と同じ高さにするため、number_inputと同じスタイルで配置
                        st.markdown(f"**{category['name']}区分**")
                        # 縦方向の位置調整のため少し空白を追加
                        st.write("")
                    
                    with col2:
                        # 開始構成比率は自動設定（編集不可）
                        if i == 0:
                            # A区分の開始は常に0
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
                            # 前の区分の終了値を自動設定
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
                        # 最終区分以外は終了構成比率を入力可能
                        is_last_category = (i == len(st.session_state.abc_categories) - 1)
                        
                        if is_last_category:
                            # 最終区分の終了は常に100
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
                            # 編集可能（白背景）
                            end_ratio = st.number_input(
                                f"終了%",
                                min_value=(start_ratio * 100) + 1.0,  # 開始値より大きい値
                                max_value=100.0,
                                value=category['end_ratio'] * 100,
                                step=1.0,
                                key=f"end_{i}",
                                help="この区分の終了構成比率（%）- 編集可能"
                            ) / 100.0
                    
                    with col4:
                        if len(st.session_state.abc_categories) > 1:  # 最低1つは残す
                            if st.button("🗑️", key=f"delete_{i}", help="この区分を削除"):
                                st.session_state.abc_categories.pop(i)
                                st.rerun()
                    
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
        
        # マッピング確認・保存
        if st.button("マッピング設定を適用する", type="primary"):
            # 必須項目チェック（ABC区分は除く - 自動生成するため）
            required_fields = ['P_code', 'Date', 'Actual', 'AI_pred', 'Plan_01']
            missing_fields = [field for field in required_fields if not mapping[field]]
            
            if missing_fields:
                st.error(f"❌ 必須項目が未設定です: {', '.join(missing_fields)}")
            else:
                try:
                    # データ変換
                    mapped_df = apply_mapping(df, mapping)
                    
                    # ABC区分の処理
                    abc_needs_generation = st.session_state.abc_auto_generate or not mapping.get('Class_abc')
                    
                    if abc_needs_generation:
                        # ABC区分を自動生成
                        with st.status("🔄 ABC区分を自動生成中...", expanded=True) as status:
                            st.write("📊 実績値データを分析中...")
                            
                            # 区分設定の妥当性チェック
                            is_valid, error_msg = validate_abc_categories(st.session_state.abc_categories)
                            if not is_valid:
                                st.error(f"❌ ABC区分設定エラー: {error_msg}")
                                status.update(label="❌ ABC区分設定エラー", state="error")
                                return
                            
                            st.write("🔢 商品コード別実績値を集計中...")
                            
                            # ABC区分を計算
                            try:
                                mapped_df = calculate_abc_classification(
                                    mapped_df, 
                                    categories=st.session_state.abc_categories,
                                    base_column='Actual'
                                )
                                st.write("✅ ABC区分の割り当て完了")
                                
                                # 生成結果の表示
                                abc_summary = get_abc_classification_summary(mapped_df, 'Class_abc', 'Actual')
                                if abc_summary:
                                    st.write("📈 集計結果:")
                                    
                                    # 各区分の詳細情報
                                    for category in sorted(st.session_state.abc_categories, key=lambda x: x['start_ratio']):
                                        cat_name = category['name']
                                        count = abc_summary['counts'].get(cat_name, 0)
                                        ratio = abc_summary['ratios'].get(cat_name, 0)
                                        range_text = f"{category['start_ratio']*100:.0f}%-{category['end_ratio']*100:.0f}%"
                                        st.write(f"　• {cat_name}区分({range_text}): {count}件 ({ratio:.1f}%)")
                                    
                                    status.update(label="✅ ABC区分自動生成完了", state="complete")
                                else:
                                    st.warning("⚠️ ABC区分の集計に問題があります")
                                    
                            except Exception as e:
                                st.error(f"❌ ABC区分計算エラー: {str(e)}")
                                status.update(label="❌ ABC区分計算エラー", state="error")
                                return
                    else:
                        st.info("📋 CSVファイルのABC区分を使用します")
                    
                    # 基本検証
                    if validate_mapped_data(mapped_df):
                        st.session_state.data = mapped_df
                        st.session_state.mapping = mapping
                        st.session_state.mapping_completed = True
                        st.success("✅ データマッピング完了！他のページで分析を開始できます。")
                        st.rerun()
                    else:
                        st.error("❌ データ検証でエラーが発生しました")
                        
                except Exception as e:
                    st.error(f"❌ データ処理エラー: {str(e)}")
        
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
                        "CSVカラム": v,
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
                abc_summary = get_abc_classification_summary(st.session_state.data, 'Class_abc', 'Actual')
                
                if abc_summary:
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.markdown("**件数分布**")
                        counts_df = pd.DataFrame(list(abc_summary['counts'].items()), 
                                                columns=['ABC区分', '件数'])
                        st.dataframe(counts_df, use_container_width=True)
                    
                    with col2:
                        if 'ratios' in abc_summary:
                            st.markdown("**実績値構成比率**")
                            ratios_df = pd.DataFrame(list(abc_summary['ratios'].items()), 
                                                    columns=['ABC区分', '構成比率(%)'])
                            st.dataframe(ratios_df, use_container_width=True)
    
    # 既にデータが読み込まれている場合の情報表示
    if st.session_state.data is not None:
        st.subheader("💾 読み込み済みデータ情報")
        df = st.session_state.data
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("データ件数", len(df))
        with col2:
            st.metric("期間範囲", f"{df['Date'].min()} - {df['Date'].max()}")
        with col3:
            st.metric("商品コード数", df['P_code'].nunique())

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
    """マッピング後のデータを検証"""
    try:
        # 必須カラムの存在確認（ABC区分は自動生成されるため除外）
        required_cols = ['P_code', 'Date', 'Actual', 'AI_pred', 'Plan_01']
        for col in required_cols:
            if col not in df.columns:
                st.error(f"必須カラムが見つかりません: {col}")
                return False
        
        # ABC区分の存在確認（必須）
        if 'Class_abc' not in df.columns:
            st.error("ABC区分が生成されていません")
            return False
        
        # データ型チェック
        numeric_cols = ['Actual', 'AI_pred', 'Plan_01']
        if 'Plan_02' in df.columns:
            numeric_cols.append('Plan_02')
            
        for col in numeric_cols:
            df[col] = pd.to_numeric(df[col], errors='coerce')
            if df[col].isnull().any():
                st.warning(f"⚠️ {col}に数値以外のデータが含まれています（NaNに変換されました）")
        
        # 日付形式チェック（簡易）
        try:
            pd.to_datetime(df['Date'].astype(str), format='%Y%m')
        except:
            st.warning("⚠️ Date列の形式がYYYYMMでない可能性があります")
        
        return True
        
    except Exception as e:
        st.error(f"データ検証エラー: {str(e)}")
        return False 