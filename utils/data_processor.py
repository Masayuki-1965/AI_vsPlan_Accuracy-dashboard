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

def calculate_abc_classification(df, categories=None, base_column='Actual'):
    """
    実績値に基づいてABC区分を自動計算
    
    Args:
        df: データフレーム
        categories: 区分設定のリスト [{'name': 'A', 'start_ratio': 0.0, 'end_ratio': 0.5}, ...]
        base_column: 基準となるカラム名（デフォルト：'Actual'）
    
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
                # 最初の区分（通常A区分）は0から開始
                if category['start_ratio'] == 0:
                    mask = product_totals['cumsum_ratio'] <= category['end_ratio']
                else:
                    mask = (product_totals['cumsum_ratio'] > category['start_ratio']) & \
                           (product_totals['cumsum_ratio'] <= category['end_ratio'])
                product_totals.loc[mask, 'Class_abc'] = category['name']
            
            # 元のデータフレームにマージ
            abc_mapping = dict(zip(product_totals['P_code'], product_totals['Class_abc']))
            df_work['Class_abc'] = df_work['P_code'].map(abc_mapping)
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
                # 最初の区分（通常A区分）は0から開始
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
    ABC区分の集計結果を取得（商品コード単位で集計）
    
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
    
    # ABC区分別の集計
    summary = {}
    
    # 商品コード単位での集計（商品コード数と一致させるため）
    if 'P_code' in df_work.columns:
        # 商品コード別の実績値合計とABC区分を取得（重複を排除）
        product_data = df_work.groupby('P_code').agg({
            base_column: 'sum',
            abc_column: 'first'  # 各商品コードのABC区分（同一商品は同じ区分なので最初の値を取得）
        }).reset_index()
        
        # 区分別の商品コード数
        abc_counts = product_data[abc_column].value_counts().sort_index()
        summary['counts'] = abc_counts.to_dict()
        
        if base_column in df_work.columns:
            # 区分別の実績値合計
            abc_totals = product_data.groupby(abc_column)[base_column].sum().sort_index()
            total_actual = product_data[base_column].sum()
            
            summary['totals'] = abc_totals.to_dict()
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
            summary['ratios'] = (abc_totals / total_actual * 100).round(2).to_dict() if total_actual > 0 else {}
            summary['total_actual'] = total_actual
    
    return summary 