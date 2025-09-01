# CSS スタイル定数
# 全ページで使用されるカスタムCSSスタイルを統合管理

# メインページスタイル
MAIN_PAGE_CSS = """
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
.footer-text {
    text-align: center;
    color: gray;
    font-size: 12px;
}
</style>
"""

# データテーブルスタイル
TABLE_CSS = """
<style>
.dataframe {
    font-size: 12px;
    border-collapse: collapse;
}
.dataframe th {
    background-color: #f0f2f6;
    color: #333;
    font-weight: bold;
    padding: 8px;
    text-align: center;
}
.dataframe td {
    padding: 6px 8px;
    text-align: center;
    border-bottom: 1px solid #ddd;
}
.dataframe tr:hover {
    background-color: #f5f5f5;
}
</style>
"""

# マトリクステーブルスタイル
MATRIX_TABLE_CSS = """
<style>
.matrix-table {
    margin: 20px 0;
    border-collapse: collapse;
    width: 100%;
    font-size: 14px;
}
.matrix-table th, .matrix-table td {
    border: 1px solid #ddd;
    padding: 8px 12px;
    text-align: center;
}
.matrix-table th {
    background-color: #f8f9fa;
    font-weight: bold;
    color: #333;
}
.matrix-table .header-row {
    background-color: #e3f2fd;
    font-weight: bold;
}
.matrix-table .total-row {
    background-color: #f1f8e9;
    font-weight: bold;
}
.matrix-table .total-col {
    background-color: #f1f8e9;
    font-weight: bold;
}
</style>
"""

# グラフコンテナスタイル
CHART_CONTAINER_CSS = """
<style>
.chart-container {
    margin: 20px 0;
    padding: 15px;
    border: 1px solid #e0e0e0;
    border-radius: 8px;
    background-color: #fafafa;
}
.chart-title {
    font-size: 1.2em;
    font-weight: bold;
    color: #1976d2;
    margin-bottom: 10px;
    text-align: center;
}
.chart-description {
    color: #666;
    font-size: 0.9em;
    margin-bottom: 15px;
    text-align: center;
}
</style>
"""

# フォームスタイル
FORM_CSS = """
<style>
.form-section {
    background-color: #f8f9fa;
    padding: 20px;
    border-radius: 8px;
    margin: 15px 0;
}
.form-title {
    font-size: 1.1em;
    font-weight: bold;
    color: #333;
    margin-bottom: 15px;
}
.form-description {
    color: #666;
    font-size: 0.9em;
    margin-bottom: 10px;
}
.required-field {
    color: #d32f2f;
    font-weight: bold;
}
.optional-field {
    color: #757575;
    font-style: italic;
}
</style>
"""

# アラート・メッセージスタイル
ALERT_CSS = """
<style>
.success-message {
    background-color: #e8f5e8;
    color: #2e7d32;
    padding: 12px 16px;
    border-radius: 4px;
    border-left: 4px solid #4caf50;
    margin: 10px 0;
}
.warning-message {
    background-color: #fff3cd;
    color: #856404;
    padding: 12px 16px;
    border-radius: 4px;
    border-left: 4px solid #ffc107;
    margin: 10px 0;
}
.error-message {
    background-color: #f8d7da;
    color: #721c24;
    padding: 12px 16px;
    border-radius: 4px;
    border-left: 4px solid #dc3545;
    margin: 10px 0;
}
.info-message {
    background-color: #d1ecf1;
    color: #0c5460;
    padding: 12px 16px;
    border-radius: 4px;
    border-left: 4px solid #17a2b8;
    margin: 10px 0;
}
</style>
"""

# 統合スタイル（全ページ共通）
UNIFIED_CSS = MAIN_PAGE_CSS + TABLE_CSS + CHART_CONTAINER_CSS + FORM_CSS + ALERT_CSS

# ページ別専用スタイル
PAGE_SPECIFIC_CSS = {
    'matrix': MATRIX_TABLE_CSS,
    'upload': FORM_CSS,
    'scatter': CHART_CONTAINER_CSS,
    'monthly_trend': CHART_CONTAINER_CSS
}

def get_page_css(page_name=None):
    """指定されたページのCSSスタイルを取得"""
    base_css = UNIFIED_CSS
    if page_name and page_name in PAGE_SPECIFIC_CSS:
        return base_css + PAGE_SPECIFIC_CSS[page_name]
    return base_css
