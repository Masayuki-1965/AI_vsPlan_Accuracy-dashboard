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
    'category_code': '分類',
    'Class_abc': 'ABC区分'
}

# 必須項目（ABC区分は任意項目）
REQUIRED_COLUMNS = ['P_code', 'Date', 'Actual', 'AI_pred', 'Plan_01']

# 数値項目
NUMERIC_COLUMNS = ['Actual', 'AI_pred', 'Plan_01', 'Plan_02']

# ABC区分設定
ABC_CLASSIFICATION_SETTINGS = {
    # デフォルトの区分定義（整数パーセンテージ対応）
    'default_categories': [
        {'name': 'A', 'start_ratio': 0.0, 'end_ratio': 0.5, 'description': 'A区分：高頻度・重要商品'},
        {'name': 'B', 'start_ratio': 0.5, 'end_ratio': 0.8, 'description': 'B区分：中頻度・標準商品'},
        {'name': 'C', 'start_ratio': 0.8, 'end_ratio': 1.0, 'description': 'C区分：低頻度・その他商品'}
    ],
    # 追加可能な区分
    'additional_categories': [
        {'name': 'D', 'description': 'D区分：特別管理商品'},
        {'name': 'E', 'description': 'E区分：季節商品'},
        {'name': 'F', 'description': 'F区分：新商品'},
        {'name': 'G', 'description': 'G区分：廃番予定商品'},
        {'name': 'H', 'description': 'H区分：保守部品'},
        {'name': 'Z', 'description': 'Z区分：特殊商品'}
    ],
    # 自動設定時の基準項目
    'base_column': 'Actual',  # 実績値を基準にする
    # 最小値・最大値の制約
    'min_ratio': 0.0,
    'max_ratio': 1.0,
    # 区分間の最小間隔
    'min_gap': 0.01  # 1%
}

# 誤差率区分設定
ERROR_RATE_CATEGORIES = {
    'absolute': [
        {'min': 0.0, 'max': 0.1, 'label': '0〜10%'},
        {'min': 0.1, 'max': 0.2, 'label': '10〜20%'},
        {'min': 0.2, 'max': 0.3, 'label': '20〜30%'},
        {'min': 0.3, 'max': 0.5, 'label': '30〜50%'},
        {'min': 0.5, 'max': 1.0, 'label': '50〜100%'},
        {'min': 1.0, 'max': float('inf'), 'label': '100%以上'},
        {'special': 'actual_zero', 'label': '計算不能 (実績0)'}
    ],
    'positive': [
        {'min': 0.0, 'max': 0.1, 'label': '＋0〜10%'},
        {'min': 0.1, 'max': 0.2, 'label': '＋10〜20%'},
        {'min': 0.2, 'max': 0.3, 'label': '＋20〜30%'},
        {'min': 0.3, 'max': 0.5, 'label': '＋30〜50%'},
        {'min': 0.5, 'max': 1.0, 'label': '＋50〜100%'},
        {'min': 1.0, 'max': float('inf'), 'label': '＋100%超'},
        {'special': 'actual_zero', 'label': '計算不能 (実績0)'}
    ],
    'negative': [
        {'min': 0.0, 'max': 0.1, 'label': '▲0〜10%'},
        {'min': 0.1, 'max': 0.2, 'label': '▲10〜20%'},
        {'min': 0.2, 'max': 0.3, 'label': '▲20〜30%'},
        {'min': 0.3, 'max': 0.5, 'label': '▲30〜50%'},
        {'min': 0.5, 'max': 1.0, 'label': '▲50〜100%'},
        {'min': 1.0, 'max': float('inf'), 'label': '▲100%超'},
        {'special': 'actual_zero', 'label': '計算不能 (実績0)'}
    ]
}

# マトリクス表示設定
MATRIX_DISPLAY_SETTINGS = {
    'show_index': False,  # 左側インデックス（0,1,2...）を非表示
    'bold_summary_rows': ['合計（件数）', '加重平均誤差率（%）'],  # 太字で表示する行
    'hatching_rows': ['加重平均誤差率（%）'],  # ハッチング適用行
    'column_groups': {
        '合計': ['合計_AI予測', '合計_計画'],
        'A区分': ['A区分_AI予測', 'A区分_計画'],
        'B区分': ['B区分_AI予測', 'B区分_計画'],
        'C区分': ['C区分_AI予測', 'C区分_計画']
    }
}

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
    'title': 'AI需要予測値 vs 計画値 精度比較分析ダッシュボード',
    'version': '1.0.0',
    'phase': 'Phase 1 (MVP-50%)',
    'icon': '📊'
} 