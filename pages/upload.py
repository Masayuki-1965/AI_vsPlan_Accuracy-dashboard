import streamlit as st
import pandas as pd
import numpy as np
import chardet
from utils.validators import validate_data, validate_required_columns
from utils.data_processor import preview_data

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
                df, encoding_info = read_csv_with_encoding(uploaded_file)
                
                # セッション状態に保存
                st.session_state.original_data = df
                st.session_state.uploaded_filename = uploaded_file.name
                st.session_state.data_columns = list(df.columns)
                st.session_state.encoding_info = encoding_info
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
        if st.session_state.encoding_info:
            st.info(f"📁 読み込み済みファイル: {st.session_state.uploaded_filename}")
            st.info(f"🔍 {st.session_state.encoding_info}")
        
        # データプレビュー
        st.subheader("2. データプレビュー")
        st.dataframe(df.head(10), use_container_width=True)
        
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
            mapping['Class_abc'] = st.selectbox(
                "ABC区分",
                options=[''] + st.session_state.data_columns,
                index=get_selectbox_index(st.session_state.data_columns, st.session_state.current_mapping.get('Class_abc', '')),
                help="ABC分析による区分（任意）"
            )
            mapping['Plan_02'] = st.selectbox(
                "計画値02",
                options=[''] + st.session_state.data_columns,
                index=get_selectbox_index(st.session_state.data_columns, st.session_state.current_mapping.get('Plan_02', '')),
                help="比較用の計画値（任意）"
            )
        
        # 現在のマッピング状態を更新
        st.session_state.current_mapping = mapping
        
        # マッピング確認・保存
        if st.button("マッピング設定を適用", type="primary"):
            # 必須項目チェック
            required_fields = ['P_code', 'Date', 'Actual', 'AI_pred', 'Plan_01']
            missing_fields = [field for field in required_fields if not mapping[field]]
            
            if missing_fields:
                st.error(f"❌ 必須項目が未設定です: {', '.join(missing_fields)}")
            else:
                # データ変換
                mapped_df = apply_mapping(df, mapping)
                
                # 基本検証
                if validate_mapped_data(mapped_df):
                    st.session_state.data = mapped_df
                    st.session_state.mapping = mapping
                    st.session_state.mapping_completed = True
                    st.success("✅ データマッピング完了！他のページで分析を開始できます。")
                    st.rerun()
                else:
                    st.error("❌ データ検証でエラーが発生しました")
        
        # マッピング完了後の表示
        if st.session_state.mapping_completed and st.session_state.data is not None:
            # マッピング結果表示
            st.subheader("4. マッピング結果")
            mapping_df = pd.DataFrame([
                {"システム項目": k, "CSVカラム": v, "データ型": str(st.session_state.data[k].dtype) if v else "未設定"}
                for k, v in st.session_state.current_mapping.items() if v
            ])
            st.dataframe(mapping_df, use_container_width=True)
            
            # 変換後データプレビュー
            st.subheader("5. 変換後データプレビュー")
            st.dataframe(st.session_state.data.head(), use_container_width=True)
    
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
    # エンコーディング候補リスト（日本語ファイルで一般的なもの）
    encodings = ['utf-8', 'shift_jis', 'cp932', 'utf-8-sig', 'euc-jp']
    
    # まず文字エンコーディングを自動判別
    raw_data = uploaded_file.getvalue()
    detected = chardet.detect(raw_data)
    detected_encoding = detected.get('encoding', 'utf-8')
    
    # 判別されたエンコーディングを最初に試す
    if detected_encoding and detected_encoding not in encodings:
        encodings.insert(0, detected_encoding)
    
    encoding_info = f"🔍 文字エンコーディング判別結果: {detected_encoding} (信頼度: {detected.get('confidence', 0):.2f})"
    
    # 各エンコーディングを順番に試行
    last_error = None
    for encoding in encodings:
        try:
            # ファイルポインタをリセット
            uploaded_file.seek(0)
            df = pd.read_csv(uploaded_file, encoding=encoding)
            success_info = f"✅ エンコーディング '{encoding}' で読み込み成功"
            return df, f"{encoding_info}\n{success_info}"
        except UnicodeDecodeError as e:
            last_error = e
            continue
        except Exception as e:
            last_error = e
            continue
    
    # すべて失敗した場合
    if last_error:
        raise Exception(f"すべてのエンコーディングで読み込みに失敗しました。最後のエラー: {str(last_error)}")
    else:
        raise Exception("CSVファイルの読み込みに失敗しました")

def validate_mapped_data(df):
    """マッピング後のデータを検証"""
    try:
        # 必須カラムの存在確認
        required_cols = ['P_code', 'Date', 'Actual', 'AI_pred', 'Plan_01']
        for col in required_cols:
            if col not in df.columns:
                st.error(f"必須カラムが見つかりません: {col}")
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