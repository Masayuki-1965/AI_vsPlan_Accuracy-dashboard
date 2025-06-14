import pandas as pd
import numpy as np

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