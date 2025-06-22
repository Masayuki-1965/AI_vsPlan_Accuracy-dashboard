# 共通定数設定ファイル

# 予測・計画タイプの表示名マッピング
PREDICTION_TYPE_NAMES = {
    'AI_pred': 'AI予測',
    'Plan_01': '計画01',
    'Plan_02': '計画02'
}

# 予測・計画タイプ別の計画名取得
PLAN_TYPE_NAMES = {
    'Plan_01': '計画01',
    'Plan_02': '計画02'
}

# 統一カラーパレット（全モジュール共通）
UNIFIED_COLOR_PALETTE = {
    'AI_pred': '#FF6B6B',   # AI予測: レッド系
    'Plan_01': '#4ECDC4',   # 計画01: ティール系
    'Plan_02': '#45B7D1',   # 計画02: ブルー系
    # ABC区分用カラー
    'A': '#FF9999',
    'B': '#66B2FF', 
    'C': '#99FF99',
    'D': '#FFCC99',
    'E': '#FF99CC',
    'F': '#99CCFF',
    'G': '#CCFF99'
}

# データ処理関連の定数
DATA_PROCESSING_CONSTANTS = {
    'default_preview_rows': 10,
    'max_file_size_mb': 100,
    'max_data_rows': 100000,
    'min_data_rows': 1,
    'date_format': '%Y%m',
    'encoding_detection_bytes': 10000
}

# UI表示関連の定数
UI_DISPLAY_CONSTANTS = {
    'default_chart_height': 600,
    'sidebar_width': 300,
    'max_abc_display': 3,  # ABC区分の最大表示数
    'selectbox_start_index': 1  # selectboxの開始インデックス（1始まり）
} 