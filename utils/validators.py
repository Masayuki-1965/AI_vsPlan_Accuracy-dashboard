import pandas as pd
import numpy as np

def validate_data(df):
    """基本的なデータ検証を実行"""
    errors = []
    warnings = []
    
    # 空のデータフレームチェック
    if df is None or df.empty:
        errors.append("データが空です")
        return False, errors, warnings
    
    # データサイズチェック
    if len(df) > 100000:
        warnings.append(f"データ件数が多すぎます: {len(df)}件（推奨: 100,000件以下）")
    
    return len(errors) == 0, errors, warnings

def validate_required_columns(df, required_columns):
    """必須カラムの存在確認"""
    missing_columns = []
    
    for col in required_columns:
        if col not in df.columns:
            missing_columns.append(col)
    
    return len(missing_columns) == 0, missing_columns

def validate_numeric_columns(df, numeric_columns):
    """数値カラムの検証"""
    errors = []
    
    for col in numeric_columns:
        if col in df.columns:
            try:
                pd.to_numeric(df[col], errors='raise')
            except:
                errors.append(f"{col}に数値以外のデータが含まれています")
    
    return len(errors) == 0, errors

def validate_date_format(df, date_column, format='%Y%m'):
    """日付形式の検証"""
    if date_column not in df.columns:
        return False, [f"日付カラム '{date_column}' が見つかりません"]
    
    try:
        pd.to_datetime(df[date_column].astype(str), format=format)
        return True, []
    except:
        return False, [f"日付形式が正しくありません（期待形式: {format}）"] 