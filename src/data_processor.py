"""
データ処理モジュール

CSV読込、複数ファイル統合、データクリーニング、フィルター機能を提供します。
"""

import pandas as pd
import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import os

# ロガー設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 定数定義
MAX_FILE_SIZE_MB = 200
REQUIRED_COLUMNS = ['Order Date', 'Sales', 'Profit', 'Product Name']
NUMERIC_COLUMNS = ['Sales', 'Profit', 'Quantity', 'Discount']
DATE_COLUMNS = ['Order Date', 'Ship Date']


class DataValidationError(Exception):
    """データバリデーションエラー"""
    pass


def validate_file_size(file) -> Tuple[bool, Optional[str]]:
    """
    ファイルサイズをチェックする

    Args:
        file: アップロードされたファイルオブジェクト

    Returns:
        Tuple[bool, Optional[str]]: (有効かどうか, エラーメッセージ)
    """
    try:
        if hasattr(file, 'size'):
            size_mb = file.size / (1024 * 1024)
            if size_mb > MAX_FILE_SIZE_MB:
                return False, f"ファイルサイズが大きすぎます（{size_mb:.1f}MB）。{MAX_FILE_SIZE_MB}MB以下のファイルをアップロードしてください。"
            elif size_mb == 0:
                return False, "空のファイルです。データが含まれるファイルをアップロードしてください。"
            logger.info(f"ファイルサイズチェック: {size_mb:.2f}MB")
        return True, None
    except Exception as e:
        logger.error(f"ファイルサイズチェックエラー: {e}")
        return True, None  # エラー時は処理を続行


def validate_file_extension(file) -> Tuple[bool, Optional[str]]:
    """
    ファイル拡張子をチェックする

    Args:
        file: アップロードされたファイルオブジェクト

    Returns:
        Tuple[bool, Optional[str]]: (有効かどうか, エラーメッセージ)
    """
    try:
        if hasattr(file, 'name'):
            filename = file.name.lower()
            if not filename.endswith('.csv'):
                return False, f"CSVファイルのみ対応しています。アップロードされたファイル: {file.name}"
        return True, None
    except Exception as e:
        logger.error(f"ファイル拡張子チェックエラー: {e}")
        return True, None


def validate_required_columns(df: pd.DataFrame) -> Tuple[bool, Optional[str]]:
    """
    必須カラムの存在をチェックする

    Args:
        df: チェック対象のDataFrame

    Returns:
        Tuple[bool, Optional[str]]: (有効かどうか, エラーメッセージ)
    """
    missing_columns = [col for col in REQUIRED_COLUMNS if col not in df.columns]

    if missing_columns:
        error_msg = f"❌ このCSVファイルは対応していない形式です。\n\n"
        error_msg += f"必須カラムが不足しています:\n"
        error_msg += "\n".join([f"  - {col}" for col in missing_columns])
        error_msg += f"\n\n必要なカラム:\n"
        error_msg += "\n".join([f"  - {col}" for col in REQUIRED_COLUMNS])
        error_msg += f"\n\n現在のファイルのカラム:\n  {', '.join(df.columns.tolist())}"
        error_msg += f"\n\nこのダッシュボードは売上データ（Superstore形式）専用です。\n正しい形式のCSVファイルをアップロードしてください。"
        return False, error_msg

    logger.info(f"必須カラムチェック: すべて存在 ({', '.join(REQUIRED_COLUMNS)})")
    return True, None


def validate_data_types(df: pd.DataFrame) -> List[str]:
    """
    データ型をチェックし、警告メッセージのリストを返す

    Args:
        df: チェック対象のDataFrame

    Returns:
        List[str]: 警告メッセージのリスト
    """
    warnings = []

    # 日付カラムのチェック
    for col in DATE_COLUMNS:
        if col in df.columns:
            try:
                parsed = pd.to_datetime(df[col], errors='coerce')
                null_count = parsed.isnull().sum()
                if null_count > 0:
                    warnings.append(f"⚠️ '{col}': {null_count}個の日付が不正な形式です")

                # 未来の日付チェック
                if col == 'Order Date':
                    future_dates = (parsed > datetime.now()).sum()
                    if future_dates > 0:
                        warnings.append(f"⚠️ '{col}': {future_dates}個の未来の日付があります")
            except Exception as e:
                warnings.append(f"❌ '{col}': 日付変換エラー ({str(e)})")

    # 数値カラムのチェック
    for col in NUMERIC_COLUMNS:
        if col in df.columns:
            try:
                numeric_data = pd.to_numeric(df[col], errors='coerce')
                null_count = numeric_data.isnull().sum()
                if null_count > 0:
                    warnings.append(f"⚠️ '{col}': {null_count}個の値が数値に変換できません")

                # 負の値チェック（SalesとQuantity）
                if col in ['Sales', 'Quantity']:
                    negative_count = (numeric_data < 0).sum()
                    if negative_count > 0:
                        warnings.append(f"⚠️ '{col}': {negative_count}個の負の値があります")

                # 極端に大きい値（外れ値）チェック
                if not numeric_data.empty:
                    q99 = numeric_data.quantile(0.99)
                    outliers = (numeric_data > q99 * 100).sum()  # 99パーセンタイルの100倍以上
                    if outliers > 0:
                        warnings.append(f"⚠️ '{col}': {outliers}個の極端に大きい値（外れ値）があります")
            except Exception as e:
                warnings.append(f"❌ '{col}': 数値変換エラー ({str(e)})")

    return warnings


def validate_missing_values(df: pd.DataFrame) -> List[str]:
    """
    欠損値をチェックし、警告メッセージのリストを返す

    Args:
        df: チェック対象のDataFrame

    Returns:
        List[str]: 警告メッセージのリスト
    """
    warnings = []
    missing_summary = df.isnull().sum()
    missing_summary = missing_summary[missing_summary > 0]

    if not missing_summary.empty:
        total_rows = len(df)
        for col, count in missing_summary.items():
            percentage = (count / total_rows) * 100

            # 重要カラムの欠損
            if col in REQUIRED_COLUMNS:
                warnings.append(f"❌ '{col}' (重要): {count}個の欠損値 ({percentage:.1f}%)")
            # 欠損率が50%超える場合
            elif percentage > 50:
                warnings.append(f"❌ '{col}': {count}個の欠損値 ({percentage:.1f}%) - 欠損率が高すぎます")
            # 通常の欠損値
            elif percentage > 10:
                warnings.append(f"⚠️ '{col}': {count}個の欠損値 ({percentage:.1f}%)")

    return warnings


def validate_data_completeness(df: pd.DataFrame) -> Tuple[bool, Optional[str]]:
    """
    データの完全性をチェックする

    Args:
        df: チェック対象のDataFrame

    Returns:
        Tuple[bool, Optional[str]]: (有効かどうか, エラーメッセージ)
    """
    # 空のDataFrameチェック
    if df.empty:
        return False, "データが空です。データが含まれるファイルをアップロードしてください。"

    # 行数が少なすぎる場合
    if len(df) < 10:
        return False, f"データ行数が少なすぎます（{len(df)}行）。少なくとも10行以上のデータが必要です。"

    logger.info(f"データ完全性チェック: {len(df)}行, {len(df.columns)}列")
    return True, None


def load_csv(file) -> pd.DataFrame:
    """
    CSVファイルを読み込みDataFrameを返す（バリデーション付き）

    Args:
        file: アップロードされたファイルオブジェクト（BytesIO）またはファイルパス（str）

    Returns:
        pd.DataFrame: 読み込まれたデータフレーム

    Raises:
        DataValidationError: バリデーションエラーの場合
        ValueError: ファイル形式が不正な場合
    """
    # ファイルパス（文字列）の場合は簡易チェックのみ
    is_file_path = isinstance(file, str)

    if not is_file_path:
        # 1. ファイル拡張子チェック（ファイルオブジェクトの場合のみ）
        is_valid, error_msg = validate_file_extension(file)
        if not is_valid:
            raise DataValidationError(error_msg)

        # 2. ファイルサイズチェック（ファイルオブジェクトの場合のみ）
        is_valid, error_msg = validate_file_size(file)
        if not is_valid:
            raise DataValidationError(error_msg)
    else:
        # ファイルパスの場合はファイル存在チェック
        if not os.path.exists(file):
            raise DataValidationError(f"ファイルが見つかりません: {file}")
        logger.info(f"ファイルパスからCSV読み込み: {file}")

    # 3. CSV読み込み（複数エンコーディング試行）
    encodings = ['utf-8', 'shift-jis', 'cp932', 'iso-8859-1', 'latin1']

    for encoding in encodings:
        try:
            if hasattr(file, 'seek'):
                file.seek(0)  # ファイルポインタを先頭に戻す
            df = pd.read_csv(file, encoding=encoding)
            logger.info(f"CSVファイル読み込み成功（{encoding}）: {len(df)}行, {len(df.columns)}列")

            # 4. データ完全性チェック
            is_valid, error_msg = validate_data_completeness(df)
            if not is_valid:
                raise DataValidationError(error_msg)

            # 5. 必須カラムチェック
            is_valid, error_msg = validate_required_columns(df)
            if not is_valid:
                raise DataValidationError(error_msg)

            return df
        except DataValidationError:
            raise  # バリデーションエラーはそのまま再送出
        except (UnicodeDecodeError, UnicodeError):
            continue
        except pd.errors.EmptyDataError:
            raise DataValidationError("空のCSVファイルです。データが含まれるファイルをアップロードしてください。")
        except Exception as e:
            logger.error(f"CSVファイル読み込み失敗（{encoding}）: {e}")
            continue

    # すべてのエンコーディングで失敗した場合
    logger.error("すべてのエンコーディングでCSV読み込みに失敗しました")
    raise ValueError(f"ファイルの読み込みに失敗しました。対応エンコーディング: {', '.join(encodings)}")


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


def export_to_excel(df: pd.DataFrame) -> bytes:
    """
    DataFrameをExcelファイル（バイナリ）に変換する

    Args:
        df: Excel出力するDataFrame

    Returns:
        bytes: Excelファイルのバイナリデータ
    """
    from io import BytesIO

    output = BytesIO()

    # ExcelWriterを使用してDataFrameを書き込み
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Sales Data')

        # ワークシートの取得と書式設定
        worksheet = writer.sheets['Sales Data']

        # 列幅の自動調整
        for column in worksheet.columns:
            max_length = 0
            column_letter = column[0].column_letter
            for cell in column:
                try:
                    if len(str(cell.value)) > max_length:
                        max_length = len(str(cell.value))
                except:
                    pass
            adjusted_width = min(max_length + 2, 50)  # 最大50文字
            worksheet.column_dimensions[column_letter].width = adjusted_width

    output.seek(0)
    logger.info(f"Excelファイル生成完了: {len(df)}行, {len(df.columns)}列")

    return output.getvalue()
