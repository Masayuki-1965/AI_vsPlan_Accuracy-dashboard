# ヘルプテキスト・ガイド文定数
# 各ページで使用されるヘルプテキストとガイド文を統合管理

# ファイルアップロード関連
FILE_UPLOAD_TEXTS = {
    'instruction': "Browse filesでファイルを指定、またはCSVファイルをドラッグ＆ドロップしてください。",
    'success_template': "✅ データを読み込みました（{rows}行×{cols}列）。下記にプレビューを表示します。",
    'help': "分析対象のCSVファイルをアップロードしてください"
}

# データマッピング関連
MAPPING_TEXTS = {
    'product_code_help': "商品を識別するコード（必須）",
    'date_help': "YYYYMM形式の年月データ（必須）",
    'actual_help': "実際の売上・需要実績（必須）",
    'ai_pred_help': "AIによる予測値（必須）",
    'plan_01_help': "基準となる計画値（必須）",
    'plan_02_help': "比較用の計画値（任意）",
    'category_code_help': "商品分類・カテゴリコード（任意・全角半角日本語入力可）",
    'abc_class_help': "CSVファイルにABC区分がある場合は選択してください",
    'optional_items_note': "※ 任意項目について：詳細分析を行う場合は「分類」を設定してください。既にABC区分を設定している場合は「ABC区分」をマッピングしてください。",
    'custom_names_note': "『計画01』『計画02』『AI予測値』の項目名は変更可能です。その他の項目は、システム項目として固定です。",
    'success_message': "✅ マッピングを実施しました。下記に変換後のデータプレビューを表示します。"
}

# ABC区分関連
ABC_TEXTS = {
    'auto_generation_instruction': "ABC区分を自動生成するか、既存を使用するかを選択してください。※一部分類のみを対象とした自動生成も可能です。",
    'auto_generate_label': "チェックするとABC区分を自動生成します（分類単位）",
    'use_existing_label': "チェックすると既存のABC区分を使用します（全分類）",
    'ratio_explanation': "実績値の多い順にソートし、指定した累積構成比率に基づいて分類単位ごとにABC分析を行います。 \n**※実績値＝全期間の実績値合計**",
    'quantity_explanation': "月平均実績値の多い順にソートし、指定した数量範囲に基づいて分類単位ごとにABC分析を行います。 \n**※月平均実績値＝全期間の実績値合計 ÷ 対象月数**",
    'dynamic_defaults_info': "💡 **動的デフォルト値が適用されています**  \nA区分・B区分の下限値は、選択された対象分類の月平均実績値に基づき、累積構成比率50%・80%に相当する値で自動計算されています。必要に応じて手動で調整可能です。",
    'all_categories_note': "💡 「全て」を選択：すべての分類に対して、同じ基準で分類単位ごとにABC区分を自動生成します。",
    'existing_abc_note': "💡 既存のABC区分をそのまま使用して集計結果を表示します。",
    'success_message': "✅ ABC区分の集計結果です。分類単位で内容を確認のうえ、必要に応じて分類フィルターで対象を選択し、ABC区分の自動生成を繰り返し実行してください。",
    'repeat_instruction': "分類単位で複数回実行可能です。必要に応じて、分類フィルターから対象を選択して再実行してください。",
    'additional_categories_help': "D区分, E区分, F区分, G区分, H区分, Z区分を追加できます"
}

# 誤差率分析関連
ERROR_ANALYSIS_TEXTS = {
    'error_type_help': "絶対: |計画-実績|÷実績, 正: 計画>実績(滞留), 負: 計画<実績(欠品)",
    'matrix_note': "**※マトリクス内はすべて商品コードの件数です**",
    'error_definition_prefix': "**誤差率定義**：",
    'error_definition_suffix': "　 ※分母：実績値"
}

# 月次補正関連
MONTHLY_CORRECTION_TEXTS = {
    'instruction': "月次補正を実施する場合は、チェックボックスをONにしてください。",
    'help': "月次補正により、月ごとの季節変動や特殊要因を調整できます。",
    'success_message': "✅ 月次補正を実施しました。",
    'note': "※ 月次補正は任意機能です。必要に応じて実施してください。"
}

# 共通メッセージ
COMMON_MESSAGES = {
    'processing': "処理中...",
    'error_occurred': "エラーが発生しました",
    'data_not_found': "データが見つかりません",
    'invalid_data': "データが正しくありません",
    'success': "処理が完了しました"
}

# ページタイトルと説明
PAGE_DESCRIPTIONS = {
    'upload': {
        'title': "データセット作成",
        'description': "CSVファイルをアップロードし、分析用データセットを作成します。項目マッピングとデータ品質チェックを行い、後続の分析に必要なデータ形式に変換します。"
    },
    'matrix': {
        'title': "誤差率帯別評価マトリクス",
        'description': "AI予測値と計画値の誤差率を帯別に分類し、商品コード件数をマトリクス形式で可視化します。ABC区分別の詳細分析も可能です。"
    },
    'scatter': {
        'title': "散布図分析",
        'description': "誤差率散布図と予測値vs実績値散布図により、個別商品の予測精度を視覚的に分析します。軸尺度の調整により詳細な分析が可能です。"
    },
    'monthly_trend': {
        'title': "月次推移分析",
        'description': "AI予測値・計画値・実績値の月次推移を折れ線グラフで表示し、時系列での予測精度の変化を分析します。"
    }
}
