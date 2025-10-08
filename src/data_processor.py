"""
データ処理モジュール

CSV読込、複数ファイル統合、データクリーニング、フィルター機能を提供します。
"""

import pandas as pd
import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime

# ロガー設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def load_csv(file) -> pd.DataFrame:
    """
    CSVファイルを読み込みDataFrameを返す

    Args:
        file: アップロードされたファイルオブジェクト（BytesIO）またはファイルパス

    Returns:
        pd.DataFrame: 読み込まれたデータフレーム

    Raises:
        ValueError: ファイル形式が不正な場合
        UnicodeDecodeError: エンコーディングエラーの場合
    """
    try:
        # まずUTF-8で試行
        df = pd.read_csv(file, encoding='utf-8')
        logger.info(f"CSVファイル読み込み成功（UTF-8）: {len(df)}行, {len(df.columns)}列")
        return df
    except UnicodeDecodeError:
        try:
            # Shift-JISで再試行
            if hasattr(file, 'seek'):
                file.seek(0)  # ファイルポインタを先頭に戻す
            df = pd.read_csv(file, encoding='shift-jis')
            logger.info(f"CSVファイル読み込み成功（Shift-JIS）: {len(df)}行, {len(df.columns)}列")
            return df
        except Exception as e:
            logger.error(f"CSVファイル読み込み失敗: {e}")
            raise ValueError(f"ファイルの読み込みに失敗しました: {e}")
    except Exception as e:
        logger.error(f"CSVファイル読み込み失敗: {e}")
        raise ValueError(f"ファイルの読み込みに失敗しました: {e}")


def merge_dataframes(dfs: List[pd.DataFrame]) -> pd.DataFrame:
    """
    複数のDataFrameを統合する

    Args:
        dfs: DataFrameのリスト

    Returns:
        pd.DataFrame: 統合されたDataFrame
    """
    if not dfs:
        raise ValueError("統合するDataFrameが指定されていません")

    if len(dfs) == 1:
        logger.info("DataFrameは1つのみです（統合不要）")
        return dfs[0]

    # 複数DataFrameを縦方向に統合
    merged_df = pd.concat(dfs, ignore_index=True)

    logger.info(f"DataFrames統合完了: {len(dfs)}個 → {len(merged_df)}行, {len(merged_df.columns)}列")

    return merged_df


def clean_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    データクリーニングを実行する

    Args:
        df: クリーニング対象のDataFrame

    Returns:
        pd.DataFrame: クリーニング済みDataFrame
    """
    df = df.copy()

    # 1. 日付カラムのパース
    date_columns = ['Order Date', 'Ship Date']
    for col in date_columns:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors='coerce')
            null_count = df[col].isnull().sum()
            if null_count > 0:
                logger.warning(f"{col}に{null_count}個の不正な日付があります")

    # 2. 欠損値チェック・レポート
    missing_summary = df.isnull().sum()
    missing_summary = missing_summary[missing_summary > 0]

    if not missing_summary.empty:
        total_rows = len(df)
        logger.warning("欠損値が検出されました:")
        for col, count in missing_summary.items():
            percentage = (count / total_rows) * 100
            logger.warning(f"  - {col}: {count}個 ({percentage:.2f}%)")

            # 欠損率が50%を超える場合は強い警告
            if percentage > 50:
                logger.error(f"  ⚠️ {col}の欠損率が50%を超えています！")

    # 3. 数値カラムの型変換
    numeric_columns = ['Sales', 'Profit', 'Quantity', 'Discount']
    for col in numeric_columns:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')

            # 異常値チェック（負の売上など）
            if col in ['Sales', 'Quantity']:
                negative_count = (df[col] < 0).sum()
                if negative_count > 0:
                    logger.warning(f"{col}に{negative_count}個の負の値があります")

    # 4. 重複行の削除
    duplicates_before = len(df)
    df = df.drop_duplicates()
    duplicates_removed = duplicates_before - len(df)

    if duplicates_removed > 0:
        logger.info(f"重複行を{duplicates_removed}個削除しました")

    logger.info(f"データクリーニング完了: {len(df)}行, {len(df.columns)}列")

    return df


def apply_filters(df: pd.DataFrame, filters: Dict[str, Any]) -> pd.DataFrame:
    """
    指定された条件でDataFrameをフィルタリングする

    Args:
        df: フィルタリング対象のDataFrame
        filters: フィルター条件の辞書
            - date_range: (start_date, end_date) のタプル
            - categories: カテゴリのリスト
            - regions: 地域のリスト
            - segments: セグメントのリスト

    Returns:
        pd.DataFrame: フィルタリング済みDataFrame
    """
    filtered_df = df.copy()
    initial_rows = len(filtered_df)

    # 1. 日付範囲フィルター
    if 'date_range' in filters and filters['date_range']:
        start_date, end_date = filters['date_range']
        if 'Order Date' in filtered_df.columns:
            if start_date:
                filtered_df = filtered_df[filtered_df['Order Date'] >= pd.to_datetime(start_date)]
            if end_date:
                filtered_df = filtered_df[filtered_df['Order Date'] <= pd.to_datetime(end_date)]
            logger.info(f"日付範囲フィルター適用: {start_date} ～ {end_date}")

    # 2. カテゴリフィルター
    if 'categories' in filters and filters['categories']:
        if 'Category' in filtered_df.columns:
            filtered_df = filtered_df[filtered_df['Category'].isin(filters['categories'])]
            logger.info(f"カテゴリフィルター適用: {filters['categories']}")

    # 3. サブカテゴリフィルター
    if 'sub_categories' in filters and filters['sub_categories']:
        if 'Sub-Category' in filtered_df.columns:
            filtered_df = filtered_df[filtered_df['Sub-Category'].isin(filters['sub_categories'])]
            logger.info(f"サブカテゴリフィルター適用: {filters['sub_categories']}")

    # 4. 地域フィルター
    if 'regions' in filters and filters['regions']:
        if 'Region' in filtered_df.columns:
            filtered_df = filtered_df[filtered_df['Region'].isin(filters['regions'])]
            logger.info(f"地域フィルター適用: {filters['regions']}")

    # 5. セグメントフィルター
    if 'segments' in filters and filters['segments']:
        if 'Segment' in filtered_df.columns:
            filtered_df = filtered_df[filtered_df['Segment'].isin(filters['segments'])]
            logger.info(f"セグメントフィルター適用: {filters['segments']}")

    final_rows = len(filtered_df)
    logger.info(f"フィルタリング完了: {initial_rows}行 → {final_rows}行 ({final_rows/initial_rows*100:.1f}%)")

    return filtered_df
