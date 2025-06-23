# UIスタイル・文字列定数設定ファイル

# StreamlitアプリケーションのカスタムCSS
CUSTOM_CSS = """
<style>
    /* Streamlitのデフォルトページナビゲーション（上部のファイル名リスト）を非表示 */
    .stSidebar [data-testid="stSidebarNav"] {
        display: none !important;
    }
    
    /* 上部のファイル名リスト部分を確実に非表示 */
    .stSidebar .css-1oe5cao,
    .stSidebar .css-1d391kg,
    .stSidebar .css-10trblm,
    .stSidebar .css-184tjsw {
        display: none !important;
    }
    
    /* ページナビゲーション関連要素を非表示 */
    .stSidebar ul[role="tablist"],
    .stSidebar nav[role="navigation"] {
        display: none !important;
    }
    
    /* サイドバーの最初の子要素（通常ファイルリスト）を非表示 */
    .stSidebar > div > div > div:first-child:not(:only-child) {
        display: none !important;
    }
    
    /* ただし、タイトルや重要なナビゲーションは保持 */
    .stSidebar .element-container:has(h1),
    .stSidebar .element-container:has(.stSelectbox),
    .stSidebar .element-container:has(.stSuccess),
    .stSidebar .element-container:has(.stWarning) {
        display: block !important;
    }
</style>
"""

# フッター文字列
FOOTER_HTML = """
<div style='text-align: center; color: gray; font-size: 12px;'>
需要予測vs計画値比較分析ダッシュボード v1.0 | Phase 1 (MVP-50%)
</div>
"""

# ヘルプテキスト定数
HELP_TEXTS = {
    'error_type_help': "絶対: |計画-実績|÷実績, 正: 計画>実績(滞留), 負: 計画<実績(欠品)",
    'file_upload_help': "分析対象のCSVファイルをアップロードしてください",
    'product_code_help': "商品を識別するコード（必須）",
    'date_help': "YYYYMM形式の年月データ（必須）",
    'actual_help': "実際の売上・需要実績（必須）",
    'ai_pred_help': "AIによる予測値（必須）",
    'plan_01_help': "基準となる計画値（必須）",
    'abc_class_help': "CSVファイルにABC区分がある場合は選択してください",
    'class_01_help': "商品分類・カテゴリコード（任意・全角半角日本語入力可）",
    'plan_02_help': "比較用の計画値（任意）",
    'abc_additional_help': "D区分, E区分, F区分, G区分, H区分, Z区分を追加できます"
}

# マトリクス説明文
MATRIX_EXPLANATION = {
    'matrix_note': "**※マトリクス内はすべて商品コードの件数です**",
    'error_definition_prefix': "**誤差率定義**：",
    'error_definition_suffix': "　 ※分母：実績値"
}

# ABC区分説明文
ABC_EXPLANATION = {
    'auto_mode': "🟢 **自動生成モード**: 実績値に基づいてABC区分を自動計算します",
    'manual_mode': "🟡 **手動指定モード**: CSVファイルのABC区分を使用します",
    'auto_no_column': "💡 ABC区分が選択されていないため、実績値に基づいて自動生成されます",
    'category_description': "実績値の多い順にソートし、累積構成比率をもとに以下の区分を割り当てます："
}

# 誤差率タイプ別定義
ERROR_RATE_DEFINITIONS = {
    'absolute': '|計画値 - 実績値| ÷ 実績値',
    'positive': '(計画値 - 実績値) ÷ 実績値',
    'negative': '(計画値 - 実績値) ÷ 実績値'
} 