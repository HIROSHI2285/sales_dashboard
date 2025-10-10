"""
売上予測モジュール

線形回帰を使った売上予測機能を提供します。
"""

import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
from datetime import datetime, timedelta
import logging

# ロガー設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def date_to_numeric(dates: pd.Series, origin: pd.Timestamp) -> np.ndarray:
    """
    日付を起点日からの経過日数に変換

    Args:
        dates: 日付のSeries
        origin: 起点日

    Returns:
        経過日数の配列
    """
    return (dates - origin).dt.days.values


def create_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    時系列特徴量を作成

    Args:
        df: 日付カラムを持つDataFrame（'Date'カラム必須）

    Returns:
        特徴量追加済みDataFrame
    """
    df = df.copy()

    # 曜日（0=月曜, 6=日曜）
    df['DayOfWeek'] = df['Date'].dt.dayofweek

    # 月（1-12）
    df['Month'] = df['Date'].dt.month

    # 四半期（1-4）
    df['Quarter'] = df['Date'].dt.quarter

    # 年
    df['Year'] = df['Date'].dt.year

    # 月の日（1-31）
    df['DayOfMonth'] = df['Date'].dt.day

    # 週末フラグ
    df['IsWeekend'] = (df['DayOfWeek'] >= 5).astype(int)

    return df


class SalesPredictor:
    """
    売上予測クラス

    線形回帰モデルを使って将来の売上を予測します。
    """

    def __init__(self):
        """初期化"""
        self.model = LinearRegression()
        self.is_trained = False
        self.date_origin = None
        self.last_training_date = None
        self.feature_columns = ['DaysFromOrigin', 'DayOfWeek', 'Month', 'Quarter', 'DayOfMonth', 'IsWeekend']

    def prepare_data(self, df: pd.DataFrame, date_col: str = 'Order Date', sales_col: str = 'Sales'):
        """
        データ前処理

        Args:
            df: 入力DataFrame
            date_col: 日付カラム名
            sales_col: 売上カラム名

        Returns:
            tuple: (X: 特徴量DataFrame, y: 売上Series, daily_df: 日次集計DataFrame)

        Raises:
            ValueError: データが不足している場合
        """
        # データ量チェック
        if len(df) < 100:
            raise ValueError(
                f"予測に必要なデータが不足しています。\n"
                f"現在: {len(df)}行、最低必要数: 100行\n"
                f"より長期間のデータをアップロードしてください。"
            )

        df = df.copy()

        # 日次売上に集計
        daily_df = df.groupby(date_col)[sales_col].sum().reset_index()
        daily_df.columns = ['Date', 'Sales']

        # 日付でソート
        daily_df = daily_df.sort_values('Date').reset_index(drop=True)

        # 起点日と最終日を記録
        self.date_origin = daily_df['Date'].min()
        self.last_training_date = daily_df['Date'].max()

        # 日付範囲の全日付を生成（欠損日を補完）
        date_range = pd.date_range(
            start=self.date_origin,
            end=self.last_training_date,
            freq='D'
        )

        # 全日付のDataFrame作成
        full_df = pd.DataFrame({'Date': date_range})

        # 元データとマージ（欠損日は0で埋める）
        daily_df = full_df.merge(daily_df, on='Date', how='left')
        daily_df['Sales'].fillna(0, inplace=True)

        # 特徴量作成
        daily_df = create_features(daily_df)

        # 日付を数値に変換
        daily_df['DaysFromOrigin'] = date_to_numeric(daily_df['Date'], self.date_origin)

        # 特徴量とターゲットを分離
        X = daily_df[self.feature_columns]
        y = daily_df['Sales']

        logger.info(f"データ前処理完了: {len(daily_df)}日分のデータ")

        return X, y, daily_df

    def train(self, X: pd.DataFrame, y: pd.Series):
        """
        モデル訓練

        Args:
            X: 特徴量DataFrame
            y: 売上Series

        Raises:
            ValueError: データにNaNまたはInfが含まれている場合
        """
        # NaN/Infチェック
        if X.isnull().any().any():
            raise ValueError("特徴量にNaN（欠損値）が含まれています。データを確認してください。")

        if y.isnull().any():
            raise ValueError("売上データにNaN（欠損値）が含まれています。データを確認してください。")

        if np.isinf(X.values).any():
            raise ValueError("特徴量に無限大（Inf）の値が含まれています。データを確認してください。")

        if np.isinf(y.values).any():
            raise ValueError("売上データに無限大（Inf）の値が含まれています。データを確認してください。")

        try:
            self.model.fit(X, y)
            self.is_trained = True

            # 訓練データでの予測
            y_pred = self.model.predict(X)

            # 訓練スコア
            train_r2 = r2_score(y, y_pred)
            train_rmse = np.sqrt(mean_squared_error(y, y_pred))

            logger.info(f"モデル訓練完了 - R²: {train_r2:.4f}, RMSE: ${train_rmse:,.0f}")

        except Exception as e:
            self.is_trained = False
            raise ValueError(f"モデル訓練中にエラーが発生しました: {str(e)}")

    def predict(self, periods: int = 30) -> pd.DataFrame:
        """
        将来予測

        Args:
            periods: 予測期間（日数）

        Returns:
            予測結果のDataFrame（Date, Predicted_Sales）

        Raises:
            ValueError: モデルが訓練されていない場合、または予測期間が長すぎる場合
        """
        if not self.is_trained:
            raise ValueError("モデルが訓練されていません。先にtrain()を呼び出してください。")

        if self.last_training_date is None:
            raise ValueError("訓練データの最終日が記録されていません。prepare_data()を先に呼び出してください。")

        # 予測期間の妥当性チェック
        if periods > 365:
            logger.warning(f"予測期間が長すぎます（{periods}日）。精度が低下する可能性があります。")

        if periods <= 0:
            raise ValueError(f"予測期間は正の整数である必要があります。現在: {periods}日")

        # 訓練データの最終日の翌日から将来の日付を生成
        future_dates = pd.date_range(
            start=self.last_training_date + timedelta(days=1),
            periods=periods,
            freq='D'
        )

        # 将来データのDataFrame作成
        future_df = pd.DataFrame({'Date': future_dates})

        # 特徴量作成
        future_df = create_features(future_df)
        future_df['DaysFromOrigin'] = date_to_numeric(future_df['Date'], self.date_origin)

        # 予測実行
        X_future = future_df[self.feature_columns]
        future_df['Predicted_Sales'] = self.model.predict(X_future)

        # 負の予測値を0にクリップ
        future_df['Predicted_Sales'] = future_df['Predicted_Sales'].clip(lower=0)

        logger.info(f"{periods}日分の予測完了")

        return future_df[['Date', 'Predicted_Sales']]

    def evaluate(self, y_true: np.ndarray, y_pred: np.ndarray) -> dict:
        """
        予測精度評価

        Args:
            y_true: 実際の値
            y_pred: 予測値

        Returns:
            評価指標の辞書（RMSE, MAE, R²）
        """
        rmse = np.sqrt(mean_squared_error(y_true, y_pred))
        mae = mean_absolute_error(y_true, y_pred)
        r2 = r2_score(y_true, y_pred)

        metrics = {
            'RMSE': rmse,
            'MAE': mae,
            'R2_Score': r2
        }

        logger.info(f"評価完了 - RMSE: ${rmse:,.0f}, MAE: ${mae:,.0f}, R²: {r2:.4f}")

        return metrics

    def train_test_split_temporal(self, X: pd.DataFrame, y: pd.Series, test_size: float = 0.2):
        """
        時系列データの訓練/テスト分割

        Args:
            X: 特徴量DataFrame
            y: ターゲットSeries
            test_size: テストデータの割合（デフォルト20%）

        Returns:
            tuple: (X_train, X_test, y_train, y_test)
        """
        split_index = int(len(X) * (1 - test_size))

        X_train = X.iloc[:split_index]
        X_test = X.iloc[split_index:]
        y_train = y.iloc[:split_index]
        y_test = y.iloc[split_index:]

        logger.info(f"訓練データ: {len(X_train)}日, テストデータ: {len(X_test)}日")

        return X_train, X_test, y_train, y_test
