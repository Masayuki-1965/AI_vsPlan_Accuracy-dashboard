import pandas as pd
import numpy as np

def calculate_error_rates(df, plan_column, actual_column):
    """
    誤差率を計算（分母：実績値）
    
    Parameters:
    df: DataFrame - データフレーム
    plan_column: str - 計画値のカラム名
    actual_column: str - 実績値のカラム名
    
    Returns:
    DataFrame - 誤差率が追加されたデータフレーム
    """
    result_df = df.copy()
    
    # ゼロ除算対策：実績値が0の場合はNaNにする（計算不能）
    plan_values = result_df[plan_column]
    actual_values = result_df[actual_column].replace(0, np.nan)
    
    # 絶対誤差率 = |計画値 - 実績値| ÷ 実績値
    result_df['absolute_error_rate'] = np.abs(plan_values - actual_values) / actual_values
    
    # 正の誤差率・負の誤差率 = (計画値 - 実績値) ÷ 実績値
    error_rate = (plan_values - actual_values) / actual_values
    result_df['error_rate'] = error_rate
    result_df['positive_error_rate'] = error_rate.where(error_rate >= 0)
    result_df['negative_error_rate'] = error_rate.where(error_rate < 0)
    
    # 実績がゼロの場合の判定フラグ
    result_df['is_actual_zero'] = result_df[actual_column] == 0
    
    return result_df

def calculate_weighted_average_error_rate(df, error_rate_column, weight_column):
    """
    実績値重み付き加重平均誤差率を計算
    
    Parameters:
    df: DataFrame - データフレーム
    error_rate_column: str - 誤差率カラム名
    weight_column: str - 重み（実績値）カラム名
    
    Returns:
    float - 加重平均誤差率
    """
    # NaNを除外
    valid_data = df.dropna(subset=[error_rate_column, weight_column])
    
    if len(valid_data) == 0:
        return np.nan
    
    # 加重平均誤差率 = Σ(誤差率 × 実績値) ÷ Σ(実績値)
    weighted_sum = (valid_data[error_rate_column] * valid_data[weight_column]).sum()
    weight_sum = valid_data[weight_column].sum()
    
    if weight_sum == 0:
        return np.nan
    
    return weighted_sum / weight_sum

def categorize_error_rates(df, error_rate_column):
    """
    誤差率を区分に分類（新仕様対応）
    
    Parameters:
    df: DataFrame - データフレーム
    error_rate_column: str - 誤差率カラム名
    
    Returns:
    Series - 誤差率区分
    """
    from config.settings import ERROR_RATE_CATEGORIES
    
    # 実績がゼロの場合を最初にチェック
    is_actual_zero = df.get('is_actual_zero', pd.Series([False] * len(df), index=df.index))
    
    # 実績ゼロの場合は計算不能として分類
    result = pd.Series(['計算不能（実績ゼロ）'] * len(df), index=df.index, name='error_rate_category')
    
    # 実績がゼロでない場合のみ誤差率で分類
    valid_mask = ~is_actual_zero
    if valid_mask.any():
        error_rates = df.loc[valid_mask, error_rate_column].fillna(0).abs()
        
        conditions = []
        choices = []
        
        for category in ERROR_RATE_CATEGORIES:
            if 'special' not in category:  # 通常の誤差率区分
                min_val = category['min']
                max_val = category['max']
                if max_val == float('inf'):
                    condition = error_rates > min_val
                else:
                    condition = (error_rates >= min_val) & (error_rates < max_val)
                conditions.append(condition)
                choices.append(category['label'])
        
        # 有効なデータに対して誤差率区分を適用
        valid_categories = np.select(conditions, choices, default='未分類')
        result.loc[valid_mask] = valid_categories
    
    return result

def create_error_matrix(df, group_columns=None):
    """
    誤差率評価マトリクスを作成
    
    Parameters:
    df: DataFrame - データフレーム
    group_columns: list - グループ化するカラム名のリスト
    
    Returns:
    DataFrame - 誤差率マトリクス
    """
    if group_columns is None:
        group_columns = []
    
    # 誤差率区分を追加
    df_with_category = df.copy()
    df_with_category['abs_error_category'] = categorize_error_rates(df, 'absolute_error_rate')
    
    # グループ化
    group_cols = group_columns + ['abs_error_category']
    
    # 集計
    matrix = df_with_category.groupby(group_cols).agg({
        'P_code': 'count',  # 件数
        'absolute_error_rate': lambda x: calculate_weighted_average_error_rate(
            df_with_category.loc[x.index], 'absolute_error_rate', 'Actual'
        ),
        'Actual': 'sum'  # 実績値合計
    }).rename(columns={
        'P_code': 'count',
        'absolute_error_rate': 'weighted_avg_error_rate',
        'Actual': 'actual_sum'
    })
    
    return matrix.reset_index()

def compare_prediction_accuracy(df):
    """
    AI予測・計画01・計画02の精度比較
    
    Parameters:
    df: DataFrame - データフレーム
    
    Returns:
    dict - 比較結果
    """
    results = {}
    
    prediction_columns = ['AI_pred', 'Plan_01']
    if 'Plan_02' in df.columns:
        prediction_columns.append('Plan_02')
    
    for col in prediction_columns:
        if col in df.columns:
            # 誤差率計算
            df_with_errors = calculate_error_rates(df, col, 'Actual')
            
            # 加重平均誤差率
            weighted_avg = calculate_weighted_average_error_rate(
                df_with_errors, 'absolute_error_rate', 'Actual'
            )
            
            # 各区分別の集計
            matrix = create_error_matrix(df_with_errors)
            
            results[col] = {
                'weighted_average_error_rate': weighted_avg,
                'total_records': len(df_with_errors),
                'matrix': matrix
            }
    
    return results 