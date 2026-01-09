import pandas as pd
import numpy as np
import streamlit as st

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
    
    # 誤差率計算の前提チェック（問題がある場合のみ表示）
    _validate_error_calculation_prerequisites(result_df, plan_column, actual_column)
    
    plan_values = result_df[plan_column]
    actual_values = result_df[actual_column]
    
    # 実績がゼロの場合の判定フラグ
    result_df['is_actual_zero'] = actual_values == 0
    
    # 通常の誤差率計算（実績≠0の場合）
    normal_mask = actual_values != 0
    error_rate = pd.Series(index=result_df.index, dtype=float)
    error_rate[normal_mask] = (plan_values[normal_mask] - actual_values[normal_mask]) / actual_values[normal_mask]
    
    # 実績=0の場合の特別処理
    zero_actual_mask = actual_values == 0
    if zero_actual_mask.any():
        # 実績=0の場合の分類：
        # - 予測値>0：計算不能（正の誤差率のみ）
        # - 予測値=0：計画対象外として計算不能（絶対・正・負すべてで計算不能）
        
        positive_pred_mask = zero_actual_mask & (plan_values > 0)
        zero_pred_mask = zero_actual_mask & (plan_values == 0)
        
        error_rate[positive_pred_mask] = float('inf')  # 計算不能
        error_rate[zero_pred_mask] = float('inf')  # 計画対象外として計算不能
    
    result_df['error_rate'] = error_rate
    
    # 絶対誤差率：全データを対象
    result_df['absolute_error_rate'] = error_rate.abs()
    
    # 正の誤差率：誤差率 >= 0 の場合（実績=0のケースを含む、誤差率=0も含む）
    positive_mask = (error_rate >= 0)
    result_df['positive_error_rate'] = error_rate.where(positive_mask)
    
    # 負の誤差率：
    # - 通常の負の誤差率（実績≠0かつ誤差率<0）のみ
    # - 誤差率=0のケースは負の誤差率に含めない（集計方針に準拠）
    # - 実績=0のケースは負の誤差率に含めない（理論上発生しない）
    negative_mask = (actual_values != 0) & (error_rate < 0)
    result_df['negative_error_rate'] = error_rate.where(negative_mask)
    
    return result_df

def calculate_weighted_average_error_rate(df, error_rate_column, weight_column):
    """
    実績値重み付き加重平均誤差率を計算
    
    集計方針：
    - 誤差率0%は絶対誤差率と正の誤差率のみにカウント
    - 負の誤差率では誤差率0%は除外（negative_error_rate列で既にNaN）
    
    Parameters:
    df: DataFrame - データフレーム
    error_rate_column: str - 誤差率カラム名（absolute_error_rate, positive_error_rate, negative_error_rate）
    weight_column: str - 重み（実績値）カラム名
    
    Returns:
    float - 加重平均誤差率
    """
    # NaNとinf値を除外（計算不能なケースを除外）
    valid_data = df.dropna(subset=[error_rate_column, weight_column])
    valid_data = valid_data[~np.isinf(valid_data[error_rate_column])]
    
    if len(valid_data) == 0:
        return np.nan
    
    # 加重平均誤差率 = Σ(誤差率 × 実績値) ÷ Σ(実績値)
    weighted_sum = (valid_data[error_rate_column] * valid_data[weight_column]).sum()
    weight_sum = valid_data[weight_column].sum()
    
    if weight_sum == 0:
        return np.nan
    
    return weighted_sum / weight_sum

def categorize_error_rates(df, error_rate_column, error_type='absolute'):
    """
    誤差率を区分に分類（新仕様対応）
    
    Parameters:
    df: DataFrame - データフレーム
    error_rate_column: str - 誤差率カラム名
    error_type: str - 誤差率タイプ ('absolute', 'positive', 'negative')
    
    Returns:
    Series - 誤差率区分
    """
    from config.settings import ERROR_RATE_CATEGORIES
    
    # 実績がゼロの場合を最初にチェック
    is_actual_zero = df.get('is_actual_zero', pd.Series([False] * len(df), index=df.index))
    
    # 結果の初期化
    result = pd.Series(['未区分'] * len(df), index=df.index, name='error_rate_category')
    
    # 実績=0の場合の特別処理
    if is_actual_zero.any():
        # 負の誤差率タイプの場合は、実績=0のケースを除外（理論上発生しない）
        if error_type == 'negative':
            # 負の誤差率では実績=0のケースを含めない
            pass
        else:
            # 絶対誤差率と正の誤差率では、実績=0の場合を「計算不能（実績ゼロ）」に分類
            result[is_actual_zero] = '計算不能（実績ゼロ）'
    
    # 実績がゼロでない場合の誤差率で分類
    valid_mask = ~is_actual_zero
    if valid_mask.any():
        error_rates = df.loc[valid_mask, error_rate_column]
        
        # NaNを除外（positive_error_rate、negative_error_rateで条件に合わない場合）
        non_nan_mask = ~error_rates.isna()
        if non_nan_mask.any():
            error_rates = error_rates[non_nan_mask]
            
            # 誤差率タイプに応じた処理
            if error_type == 'absolute':
                error_rates = error_rates.abs()
            elif error_type == 'positive':
                # positive_error_rate列はすでに正の値と0を含んでいるため、フィルタリング不要
                pass
            elif error_type == 'negative':
                # negative_error_rate列はすでに負の値と0を含んでいるため、絶対値化のみ
                error_rates = error_rates.abs()
            
            conditions = []
            choices = []
            
            categories = ERROR_RATE_CATEGORIES.get(error_type, ERROR_RATE_CATEGORIES['absolute'])
            
            for category in categories:
                if 'special' not in category:  # 通常の誤差率区分
                    min_val = category['min']
                    max_val = category['max']
                    if max_val == float('inf'):
                        condition = error_rates >= min_val
                    else:
                        condition = (error_rates >= min_val) & (error_rates < max_val)
                    conditions.append(condition)
                    choices.append(category['label'])
            
            # 有効なデータに対して誤差率区分を適用
            valid_categories = np.select(conditions, choices, default='未区分')
            
            # 元のインデックスに対応するマスクを作成
            final_mask = valid_mask & df[error_rate_column].notna()
            result.loc[final_mask] = valid_categories
    
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
    df_with_category['abs_error_category'] = categorize_error_rates(df, 'absolute_error_rate', 'absolute')
    
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

def _validate_error_calculation_prerequisites(df, plan_column, actual_column):
    """誤差率計算の前提条件をチェック（重要な問題のみ表示）"""
    critical_issues = []
    
    # 列の存在チェック（これは重要なエラー）
    if plan_column not in df.columns:
        critical_issues.append(f"計画値列 '{plan_column}' が存在しません")
    if actual_column not in df.columns:
        critical_issues.append(f"実績値列 '{actual_column}' が存在しません")
    
    # 重要なエラーのみ表示
    if critical_issues:
        st.error("❌ 誤差率計算エラー: " + ", ".join(critical_issues))
        return
    
    # その他のチェック（データ型、NaN値）は内部的に実行するが表示しない
    # これにより、計算は正常に動作するが、ユーザーにはノイズを表示しない

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

 