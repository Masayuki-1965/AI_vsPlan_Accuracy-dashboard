import pandas as pd
import numpy as np
from config.settings import ABC_CLASSIFICATION_SETTINGS

def preview_data(df, n_rows=5):
    """データのプレビューを生成"""
    if df is None or df.empty:
        return None
    
    return {
        'head': df.head(n_rows),
        'shape': df.shape,
        'columns': list(df.columns),
        'dtypes': df.dtypes.to_dict(),
        'missing': df.isnull().sum().to_dict()
    }

def clean_numeric_data(df, columns):
    """数値データのクリーニング"""
    cleaned_df = df.copy()
    
    for col in columns:
        if col in cleaned_df.columns:
            # 数値変換（エラーはNaNに）
            cleaned_df[col] = pd.to_numeric(cleaned_df[col], errors='coerce')
            
            # 負の値を0に変換（需要データの場合）
            cleaned_df[col] = cleaned_df[col].clip(lower=0)
    
    return cleaned_df

def detect_outliers(df, column, method='iqr', factor=1.5):
    """外れ値の検出"""
    if column not in df.columns:
        return pd.Series(dtype=bool)
    
    data = df[column].dropna()
    
    if method == 'iqr':
        Q1 = data.quantile(0.25)
        Q3 = data.quantile(0.75)
        IQR = Q3 - Q1
        lower_bound = Q1 - factor * IQR
        upper_bound = Q3 + factor * IQR
        
        outliers = (df[column] < lower_bound) | (df[column] > upper_bound)
        
    elif method == 'z_score':
        mean = data.mean()
        std = data.std()
        z_scores = np.abs((df[column] - mean) / std)
        outliers = z_scores > factor
        
    else:
        outliers = pd.Series([False] * len(df), index=df.index)
    
    return outliers.fillna(False)

def get_data_summary(df):
    """データの要約統計を取得"""
    if df is None or df.empty:
        return {}
    
    summary = {
        'total_rows': len(df),
        'total_columns': len(df.columns),
        'numeric_columns': df.select_dtypes(include=[np.number]).columns.tolist(),
        'categorical_columns': df.select_dtypes(include=['object']).columns.tolist(),
        'missing_data': df.isnull().sum().to_dict(),
        'duplicate_rows': df.duplicated().sum()
    }
    
    # 数値カラムの統計情報
    numeric_stats = {}
    for col in summary['numeric_columns']:
        numeric_stats[col] = {
            'mean': float(df[col].mean()),
            'median': float(df[col].median()),
            'std': float(df[col].std()),
            'min': float(df[col].min()),
            'max': float(df[col].max()),
            'null_count': int(df[col].isnull().sum())
        }
    
    summary['numeric_stats'] = numeric_stats
    
    return summary

def calculate_abc_classification(df, categories=None, base_column='Actual', target_categories=None, preserve_existing=False):
    """
    実績値に基づいてABC区分を自動計算（分類単位対応・部分上書き対応）
    
    Args:
        df: データフレーム
        categories: 区分設定のリスト [{'name': 'A', 'start_ratio': 0.0, 'end_ratio': 0.5}, ...]
        base_column: 基準となるカラム名（デフォルト：'Actual'）
        target_categories: 自動生成対象の分類リスト（Noneの場合は全分類対象）
        preserve_existing: 既存のABC区分を保持するかどうか
    
    Returns:
        ABC区分が追加されたデータフレーム
    """
    if df is None or df.empty:
        return df
    
    if base_column not in df.columns:
        raise ValueError(f"基準カラム '{base_column}' がデータに存在しません")
    
    # デフォルト設定を使用
    if categories is None:
        categories = ABC_CLASSIFICATION_SETTINGS['default_categories']
    
    # 基準カラムの数値チェック
    df_work = df.copy()
    df_work[base_column] = pd.to_numeric(df_work[base_column], errors='coerce')
    
    # NaNや負の値を0に変換
    df_work[base_column] = df_work[base_column].fillna(0).clip(lower=0)
    
    # ABC区分カラムの初期化処理（分類単位の部分更新に対応）
    if 'Class_abc' not in df_work.columns:
        # ABC区分カラムが存在しない場合は新規作成
        df_work['Class_abc'] = pd.NA
    elif target_categories is not None:
        # 分類を指定した部分更新の場合は既存値を保持
        pass
    elif not preserve_existing:
        # 全体の新規作成または全上書きの場合のみ初期化
        df_work['Class_abc'] = pd.NA
    # preserve_existing=Trueの場合は既存値を保持
    
    # 分類別に処理
    if 'category_code' in df_work.columns and df_work['category_code'].notna().any():
        # 処理対象の分類を決定
        if target_categories is not None:
            # 指定された分類のみ処理
            categories_list = [cat for cat in df_work['category_code'].dropna().unique() if cat in target_categories]
        else:
            # 全分類を処理
            categories_list = df_work['category_code'].dropna().unique()
        
        for category_code in categories_list:
            category_data = df_work[df_work['category_code'] == category_code]
            
            # 商品コード別の実績値合計を計算
            product_totals = category_data.groupby('P_code')[base_column].sum().reset_index()
            product_totals = product_totals.sort_values(base_column, ascending=False)
            
            # 分類内の実績値合計
            total_actual = product_totals[base_column].sum()
            
            if total_actual > 0:
                # 累積構成比を計算
                product_totals['cumsum'] = product_totals[base_column].cumsum()
                product_totals['cumsum_ratio'] = product_totals['cumsum'] / total_actual
                
                # ABC区分を割り当て（累積構成比に基づく）
                product_totals['Class_abc'] = 'C'  # デフォルト
                
                # 区分を構成比の順序で処理（小さい順）
                sorted_categories = sorted(categories, key=lambda x: x['start_ratio'])
                
                for category in sorted_categories:
                    # 累積構成比がこの区分の範囲内の商品を対象
                    if category['start_ratio'] == 0:
                        mask = product_totals['cumsum_ratio'] <= category['end_ratio']
                    else:
                        mask = (product_totals['cumsum_ratio'] > category['start_ratio']) & \
                               (product_totals['cumsum_ratio'] <= category['end_ratio'])
                    product_totals.loc[mask, 'Class_abc'] = category['name']
                
                # 元のデータフレームにマージ（該当分類のみ）
                abc_mapping = dict(zip(product_totals['P_code'], product_totals['Class_abc']))
                mask = df_work['category_code'] == category_code
                # 該当分類の商品コードのみを更新（既存値を保持）
                for product_code, abc_class in abc_mapping.items():
                    product_mask = mask & (df_work['P_code'] == product_code)
                    df_work.loc[product_mask, 'Class_abc'] = abc_class
            else:
                # 実績値が全て0の場合はC区分を割り当て
                mask = df_work['category_code'] == category_code
                df_work.loc[mask, 'Class_abc'] = 'C'
        
        # 処理されなかった分類または分類が設定されていない行の処理
        if target_categories is None and not preserve_existing:
            # 全分類処理の場合のみ、分類が設定されていない行にもC区分を割り当て
            mask_no_category = df_work['category_code'].isna()
            df_work.loc[mask_no_category, 'Class_abc'] = 'C'
        # target_categoriesが指定されている場合、未処理の分類や行は既存値またはNaNのまま保持
        
    else:
        # 分類がない場合は従来通りの全体処理
        # 商品コード別の実績値合計を計算
        if 'P_code' in df_work.columns:
            # 商品コード別に実績値を集計
            product_totals = df_work.groupby('P_code')[base_column].sum().reset_index()
            product_totals = product_totals.sort_values(base_column, ascending=False)
            
            # 全体の実績値合計
            total_actual = product_totals[base_column].sum()
            
            if total_actual > 0:
                # 累積構成比を計算
                product_totals['cumsum'] = product_totals[base_column].cumsum()
                product_totals['cumsum_ratio'] = product_totals['cumsum'] / total_actual
                
                # ABC区分を割り当て（累積構成比に基づく）
                product_totals['Class_abc'] = 'C'  # デフォルト
                
                # 区分を構成比の順序で処理（小さい順）
                sorted_categories = sorted(categories, key=lambda x: x['start_ratio'])
                
                for category in sorted_categories:
                    # 累積構成比がこの区分の範囲内の商品を対象
                    if category['start_ratio'] == 0:
                        mask = product_totals['cumsum_ratio'] <= category['end_ratio']
                    else:
                        mask = (product_totals['cumsum_ratio'] > category['start_ratio']) & \
                               (product_totals['cumsum_ratio'] <= category['end_ratio'])
                    product_totals.loc[mask, 'Class_abc'] = category['name']
                
                # 元のデータフレームにマージ（分類単位処理と同様に個別更新）
                abc_mapping = dict(zip(product_totals['P_code'], product_totals['Class_abc']))
                for product_code, abc_class in abc_mapping.items():
                    product_mask = df_work['P_code'] == product_code
                    df_work.loc[product_mask, 'Class_abc'] = abc_class
            else:
                # 実績値が全て0の場合はC区分を割り当て
                df_work['Class_abc'] = 'C'
        else:
            # 商品コードがない場合は行別に処理
            df_sorted = df_work.sort_values(base_column, ascending=False)
            total_actual = df_sorted[base_column].sum()
            
            if total_actual > 0:
                df_sorted['cumsum'] = df_sorted[base_column].cumsum()
                df_sorted['cumsum_ratio'] = df_sorted['cumsum'] / total_actual
                
                # ABC区分を割り当て（累積構成比に基づく）
                df_sorted['Class_abc'] = 'C'  # デフォルト
                
                # 区分を構成比の順序で処理（小さい順）
                sorted_categories = sorted(categories, key=lambda x: x['start_ratio'])
                
                for category in sorted_categories:
                    # 累積構成比がこの区分の範囲内の行を対象
                    if category['start_ratio'] == 0:
                        mask = df_sorted['cumsum_ratio'] <= category['end_ratio']
                    else:
                        mask = (df_sorted['cumsum_ratio'] > category['start_ratio']) & \
                               (df_sorted['cumsum_ratio'] <= category['end_ratio'])
                    df_sorted.loc[mask, 'Class_abc'] = category['name']
                
                # 元のインデックス順に戻す
                df_work = df_sorted.sort_index()
            else:
                df_work['Class_abc'] = 'C'
    
    # 未区分（NaN）の処理（分類単位部分更新時は対象外分類の既存値を保持）
    if target_categories is None:
        # 全体処理の場合のみNaNを未区分に変換
        mask_unclassified = df_work['Class_abc'].isna()
        if mask_unclassified.any():
            df_work.loc[mask_unclassified, 'Class_abc'] = '未区分'
    
    return df_work

def validate_abc_categories(categories):
    """
    ABC区分設定の妥当性をチェック
    
    Args:
        categories: 区分設定のリスト
    
    Returns:
        (is_valid, error_message)
    """
    if not categories:
        return False, "区分設定が空です"
    
    # 重複チェック
    names = [cat['name'] for cat in categories]
    if len(names) != len(set(names)):
        return False, "区分名に重複があります"
    
    # 範囲チェック
    for cat in categories:
        if cat['start_ratio'] < 0 or cat['end_ratio'] > 1:
            return False, f"区分 '{cat['name']}' の範囲が無効です（0-1の範囲で設定してください）"
        
        if cat['start_ratio'] >= cat['end_ratio']:
            return False, f"区分 '{cat['name']}' の開始値が終了値以上です"
    
    # 重複範囲チェック
    sorted_categories = sorted(categories, key=lambda x: x['start_ratio'])
    for i in range(len(sorted_categories) - 1):
        if sorted_categories[i]['end_ratio'] > sorted_categories[i+1]['start_ratio']:
            return False, f"区分 '{sorted_categories[i]['name']}' と '{sorted_categories[i+1]['name']}' の範囲が重複しています"
    
    return True, ""

def get_abc_classification_summary(df, abc_column='Class_abc', base_column='Actual'):
    """
    ABC区分の集計結果を取得（商品コード単位で集計・未区分対応）
    
    Args:
        df: データフレーム
        abc_column: ABC区分カラム名
        base_column: 基準カラム名
    
    Returns:
        集計結果の辞書
    """
    if df is None or df.empty or abc_column not in df.columns:
        return {}
    
    # 基準カラムの数値化
    df_work = df.copy()
    if base_column in df_work.columns:
        df_work[base_column] = pd.to_numeric(df_work[base_column], errors='coerce').fillna(0)
    
    # ABC区分の未区分処理
    df_work[abc_column] = df_work[abc_column].fillna('未区分')
    
    # ABC区分別の集計
    summary = {}
    
    # 商品コード単位での集計（商品コード数と一致させるため）
    if 'P_code' in df_work.columns:
        # 商品コード別の実績値合計とABC区分を取得（重複を排除）
        product_data = df_work.groupby('P_code').agg({
            base_column: 'sum',
            abc_column: 'first'  # 各商品コードのABC区分（同一商品は同じ区分なので最初の値を取得）
        }).reset_index()
        
        # 区分別の商品コード数（未区分も含む）
        abc_counts = product_data[abc_column].value_counts().sort_index()
        summary['counts'] = abc_counts.to_dict()
        
        if base_column in df_work.columns:
            # 区分別の実績値合計（未区分も含む）
            abc_totals = product_data.groupby(abc_column)[base_column].sum().sort_index()
            total_actual = product_data[base_column].sum()
            
            summary['totals'] = abc_totals.to_dict()
            summary['actual_sums'] = abc_totals.to_dict()  # 実績合計として追加
            summary['ratios'] = (abc_totals / total_actual * 100).round(2).to_dict() if total_actual > 0 else {}
            summary['total_actual'] = total_actual
    else:
        # 商品コードがない場合は従来通りの行単位での集計
        abc_counts = df_work[abc_column].value_counts().sort_index()
        summary['counts'] = abc_counts.to_dict()
        
        if base_column in df_work.columns:
            abc_totals = df_work.groupby(abc_column)[base_column].sum().sort_index()
            total_actual = df_work[base_column].sum()
            
            summary['totals'] = abc_totals.to_dict()
            summary['actual_sums'] = abc_totals.to_dict()  # 実績合計として追加
            summary['ratios'] = (abc_totals / total_actual * 100).round(2).to_dict() if total_actual > 0 else {}
            summary['total_actual'] = total_actual
    
    return summary

def calculate_abc_classification_by_quantity(df, categories=None, base_column='Actual', target_categories=None, preserve_existing=False):
    """
    月平均実績値に基づいてABC区分を数量範囲で自動計算（分類単位対応・部分上書き対応）
    
    Args:
        df: データフレーム
        categories: 区分設定のリスト [{'name': 'A', 'min_value': 100}, {'name': 'B', 'min_value': 50}, ...]
        base_column: 基準となるカラム名（デフォルト：'Actual'）
        target_categories: 自動生成対象の分類リスト（Noneの場合は全分類対象）
        preserve_existing: 既存のABC区分を保持するかどうか
    
    Returns:
        ABC区分が追加されたデータフレーム
    """
    if df is None or df.empty:
        return df
    
    if base_column not in df.columns:
        raise ValueError(f"基準カラム '{base_column}' がデータに存在しません")
    
    # デフォルト設定（ダミー - 実際は呼び出し側で設定）
    if categories is None:
        return df
    
    # 基準カラムの数値チェック
    df_work = df.copy()
    df_work[base_column] = pd.to_numeric(df_work[base_column], errors='coerce')
    
    # NaNや負の値を0に変換
    df_work[base_column] = df_work[base_column].fillna(0).clip(lower=0)
    
    # ABC区分カラムの初期化処理（分類単位の部分更新に対応）
    if 'Class_abc' not in df_work.columns:
        # ABC区分カラムが存在しない場合は新規作成
        df_work['Class_abc'] = pd.NA
    elif target_categories is not None:
        # 分類を指定した部分更新の場合は既存値を保持
        pass
    elif not preserve_existing:
        # 全体の新規作成または全上書きの場合のみ初期化
        df_work['Class_abc'] = pd.NA
    # preserve_existing=Trueの場合は既存値を保持
    
    # 分類別に処理
    if 'category_code' in df_work.columns and df_work['category_code'].notna().any():
        # 処理対象の分類を決定
        if target_categories is not None:
            # 指定された分類のみ処理
            categories_list = [cat for cat in df_work['category_code'].dropna().unique() if cat in target_categories]
        else:
            # 全分類を処理
            categories_list = df_work['category_code'].dropna().unique()
        
        for category_code in categories_list:
            category_data = df_work[df_work['category_code'] == category_code]
            
            # 商品コード別の月平均実績値を計算
            monthly_averages = calculate_monthly_average_actual(category_data, base_column)
            
            # 数量範囲に基づいてABC区分を割り当て
            for product_code, monthly_avg_value in monthly_averages.items():
                # デフォルトは最後の区分
                assigned_category = categories[-1]['name']
                
                # 上位の区分から順番にチェック（数量の多い順）
                for category in categories:
                    if monthly_avg_value >= category.get('min_value', 0):
                        assigned_category = category['name']
                        break
                
                # 該当分類の商品コードにABC区分を割り当て
                mask = (df_work['category_code'] == category_code) & (df_work['P_code'] == product_code)
                df_work.loc[mask, 'Class_abc'] = assigned_category
        
        # 処理されなかった分類または分類が設定されていない行の処理
        if target_categories is None and not preserve_existing:
            # 全分類処理の場合のみ、分類が設定されていない行にも最後の区分を割り当て
            mask_no_category = df_work['category_code'].isna()
            df_work.loc[mask_no_category, 'Class_abc'] = categories[-1]['name']
        # target_categoriesが指定されている場合、未処理の分類や行は既存値またはNaNのまま保持
        
    else:
        # 分類がない場合は全体処理
        if 'P_code' in df_work.columns:
            # 商品コード別の月平均実績値を計算
            monthly_averages = calculate_monthly_average_actual(df_work, base_column)
            
            # ABC区分を割り当て
            for product_code, monthly_avg_value in monthly_averages.items():
                # デフォルトは最後の区分
                assigned_category = categories[-1]['name']
                
                # 上位の区分から順番にチェック（数量の多い順）
                for category in categories:
                    if monthly_avg_value >= category.get('min_value', 0):
                        assigned_category = category['name']
                        break
                
                # 商品コードにABC区分を割り当て
                mask = df_work['P_code'] == product_code
                df_work.loc[mask, 'Class_abc'] = assigned_category
        else:
            # 商品コードがない場合は行別に処理（月平均を計算するのが困難なので通常の実績値を使用）
            for index, row in df_work.iterrows():
                actual_value = row[base_column]
                
                # デフォルトは最後の区分
                assigned_category = categories[-1]['name']
                
                # 上位の区分から順番にチェック（数量の多い順）
                for category in categories:
                    if actual_value >= category.get('min_value', 0):
                        assigned_category = category['name']
                        break
                
                df_work.loc[index, 'Class_abc'] = assigned_category
    
    # 未区分（NaN）の処理（分類単位部分更新時は対象外分類の既存値を保持）
    if target_categories is None:
        # 全体処理の場合のみNaNを未区分に変換
        mask_unclassified = df_work['Class_abc'].isna()
        if mask_unclassified.any():
            df_work.loc[mask_unclassified, 'Class_abc'] = '未区分'
    
    return df_work

def validate_abc_quantity_categories(categories):
    """
    ABC区分数量範囲設定の妥当性をチェック
    
    Args:
        categories: 区分設定のリスト [{'name': 'A', 'min_value': 100}, ...]
    
    Returns:
        (is_valid, error_message)
    """
    if not categories:
        return False, "区分設定が空です"
    
    # 重複チェック
    names = [cat['name'] for cat in categories]
    if len(names) != len(set(names)):
        return False, "区分名に重複があります"
    
    # 数量範囲の妥当性チェック
    for cat in categories:
        min_value = cat.get('min_value', 0)
        if min_value < 0:
            return False, f"区分 '{cat['name']}' の下限値が負の値です"
    
    # 数量範囲の重複チェック（上位区分ほど下限値が大きい必要がある）
    sorted_categories = sorted(categories, key=lambda x: x.get('min_value', 0), reverse=True)
    for i in range(len(sorted_categories) - 1):
        current_min = sorted_categories[i].get('min_value', 0)
        next_min = sorted_categories[i+1].get('min_value', 0)
        if current_min <= next_min:
            return False, f"区分 '{sorted_categories[i]['name']}' の下限値が '{sorted_categories[i+1]['name']}' 以下です"
    
    return True, ""

def calculate_monthly_average_actual(df, base_column='Actual'):
    """
    月平均実績値を計算（商品コード別）
    
    Args:
        df: データフレーム
        base_column: 基準となるカラム名（デフォルト：'Actual'）
    
    Returns:
        商品コード別月平均実績値の辞書
    """
    if df is None or df.empty or 'P_code' not in df.columns:
        return {}
    
    if base_column not in df.columns:
        return {}
    
    # 数値化
    df_work = df.copy()
    df_work[base_column] = pd.to_numeric(df_work[base_column], errors='coerce').fillna(0)
    df_work['Date'] = pd.to_numeric(df_work['Date'], errors='coerce')
    
    # 期間の月数を計算
    if 'Date' in df_work.columns:
        unique_dates = df_work['Date'].dropna().unique()
        month_count = len(unique_dates) if len(unique_dates) > 0 else 1
    else:
        month_count = 1
    
    # 商品コード別の全期間実績値合計を計算
    product_totals = df_work.groupby('P_code')[base_column].sum()
    
    # 月平均を計算
    monthly_averages = product_totals / month_count
    
    return monthly_averages.to_dict()

def calculate_default_quantity_ranges(df, base_column='Actual'):
    """
    データに基づいてデフォルトの数量範囲を計算
    
    Args:
        df: データフレーム
        base_column: 基準となるカラム名（デフォルト：'Actual'）
    
    Returns:
        デフォルト数量範囲のリスト
    """
    if df is None or df.empty:
        return [
            {'name': 'A', 'min_value': 50},
            {'name': 'B', 'min_value': 10},
            {'name': 'C', 'min_value': 0}
        ]
    
    try:
        # 月平均実績値を計算
        monthly_averages = calculate_monthly_average_actual(df, base_column)
        
        if not monthly_averages:
            return [
                {'name': 'A', 'min_value': 50},
                {'name': 'B', 'min_value': 10},
                {'name': 'C', 'min_value': 0}
            ]
        
        # 月平均実績値を降順でソート
        sorted_averages = sorted(monthly_averages.values(), reverse=True)
        
        if len(sorted_averages) == 0:
            a_threshold = 50
            b_threshold = 10
        else:
            # A区分（上位50%相当）の下限値
            a_index = int(len(sorted_averages) * 0.5)
            a_threshold = max(1, int(sorted_averages[a_index])) if a_index < len(sorted_averages) else 1
            
            # B区分（上位90%相当）の下限値
            b_index = int(len(sorted_averages) * 0.9)
            b_threshold = max(1, int(sorted_averages[b_index])) if b_index < len(sorted_averages) else 1
            
            # A区分とB区分の下限値が同じ場合の調整
            if a_threshold <= b_threshold:
                a_threshold = b_threshold + 1
        
        return [
            {'name': 'A', 'min_value': a_threshold},
            {'name': 'B', 'min_value': b_threshold},
            {'name': 'C', 'min_value': 0}
        ]
        
    except Exception:
        # エラーが発生した場合はデフォルト値を返す
        return [
            {'name': 'A', 'min_value': 50},
            {'name': 'B', 'min_value': 10},
            {'name': 'C', 'min_value': 0}
        ] 