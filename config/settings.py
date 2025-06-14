# アプリケーション設定ファイル

# カラーパレット（統一デザイン）
COLOR_PALETTE = {
    'AI_pred': '#FF6B6B',   # AI予測: レッド系
    'Plan_01': '#4ECDC4',   # 計画01: ティール系
    'Plan_02': '#45B7D1'    # 計画02: ブルー系
}

# データ項目名マッピング
COLUMN_MAPPING = {
    'P_code': '商品コード',
    'Date': '年月',
    'Actual': '実績値',
    'AI_pred': 'AI予測値',
    'Plan_01': '計画値01',
    'Plan_02': '計画値02',
    'Class_01': '分類01',
    'Class_02': '分類02',
    'Class_abc': 'ABC区分'
}

# 必須項目
REQUIRED_COLUMNS = ['P_code', 'Date', 'Actual', 'AI_pred', 'Plan_01']

# 数値項目
NUMERIC_COLUMNS = ['Actual', 'AI_pred', 'Plan_01', 'Plan_02']

# 誤差率区分設定
ERROR_RATE_CATEGORIES = [
    {'min': 0.0, 'max': 0.1, 'label': '0-10%'},
    {'min': 0.1, 'max': 0.2, 'label': '10-20%'},
    {'min': 0.2, 'max': 0.3, 'label': '20-30%'},
    {'min': 0.3, 'max': 0.5, 'label': '30-50%'},
    {'min': 0.5, 'max': 1.0, 'label': '50-100%'},
    {'min': 1.0, 'max': float('inf'), 'label': '100%超'}
]

# データ検証設定
VALIDATION_SETTINGS = {
    'max_file_size_mb': 100,
    'max_rows': 100000,
    'min_rows': 1
}

# 表示設定
DISPLAY_SETTINGS = {
    'max_preview_rows': 10,
    'default_chart_height': 600,
    'sidebar_width': 300
}

# アプリケーション情報
APP_INFO = {
    'title': '需要予測vs計画値比較分析ダッシュボード',
    'version': '1.0.0',
    'phase': 'Phase 1 (MVP-50%)',
    'icon': '📊'
} 