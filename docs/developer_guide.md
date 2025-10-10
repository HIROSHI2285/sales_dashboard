# 開発者ガイド

営業ダッシュボード＋分析レポート自動生成ツールの開発者向けドキュメント

---

## 目次

1. [アーキテクチャ概要](#アーキテクチャ概要)
2. [技術スタック](#技術スタック)
3. [プロジェクト構造](#プロジェクト構造)
4. [モジュール詳細](#モジュール詳細)
5. [開発環境セットアップ](#開発環境セットアップ)
6. [コーディング規約](#コーディング規約)
7. [テスト](#テスト)
8. [デプロイ](#デプロイ)
9. [拡張方法](#拡張方法)

---

## アーキテクチャ概要

### システム構成図

```
┌─────────────────────────────────────────────────────────┐
│                     Streamlit UI (app.py)                │
│  ┌─────────┬──────────────┬─────────────┬─────────────┐│
│  │Dashboard│ Data Preview │ Prediction  │ PDF Report  ││
│  └─────────┴──────────────┴─────────────┴─────────────┘│
└─────────────────────────────────────────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        │                     │                     │
┌───────▼────────┐  ┌────────▼────────┐  ┌────────▼────────┐
│ data_processor │  │   visualizer    │  │    predictor    │
├────────────────┤  ├─────────────────┤  ├─────────────────┤
│ - load_csv()   │  │ - plot_sales_   │  │ - prepare_data()│
│ - merge_df()   │  │   trend()       │  │ - train()       │
│ - clean_data() │  │ - plot_product_ │  │ - predict()     │
│ - apply_        │  │   ranking()     │  │ - evaluate()    │
│   filters()    │  │ - plot_         │  │                 │
│ - export_to_   │  │   customer_     │  │                 │
│   excel()      │  │   analysis()    │  │                 │
└────────────────┘  │ - etc (7 types) │  └─────────────────┘
                    └─────────────────┘
                              │
                    ┌─────────▼─────────┐
                    │  pdf_generator    │
                    ├───────────────────┤
                    │ - add_summary_    │
                    │   section()       │
                    │ - add_chart_      │
                    │   section()       │
                    │ - generate_       │
                    │   report()        │
                    └───────────────────┘
```

### データフロー

```
1. CSV Upload → load_csv() → pd.DataFrame
                     ↓
2. Validation → validate_required_columns()
                     ↓
3. Cleaning → clean_data() → Cleaned DataFrame
                     ↓
4. ┌─────────────┬─────────────┬─────────────┐
   │             │             │             │
   ▼             ▼             ▼             ▼
Visualize    Predict     Export PDF   Export Excel
```

### セッション管理

Streamlitの`st.session_state`でデータを永続化：

```python
if 'data' not in st.session_state:
    st.session_state.data = None

# データ保存
st.session_state.data = df

# データ取得
df = st.session_state.data
```

---

## 技術スタック

### コアライブラリ

| ライブラリ | バージョン | 用途 |
|-----------|-----------|------|
| **streamlit** | 1.28.0 | Webアプリケーションフレームワーク |
| **pandas** | 2.1.1 | データ処理・分析 |
| **plotly** | 5.17.0 | インタラクティブグラフ生成 |
| **scikit-learn** | 1.3.1 | 機械学習（線形回帰） |
| **fpdf2** | 2.7.6 | PDFレポート生成 |
| **openpyxl** | 3.1.2 | Excelファイル出力 |
| **kaleido** | 0.2.1 | Plotlyグラフの画像変換 |
| **Pillow** | 10.0.1 | 画像処理 |

### 選定理由

**Streamlit:**
- Pythonのみで完結するWebアプリ開発
- ホットリロード対応で開発効率が高い
- データサイエンス向けのコンポーネントが豊富

**Plotly:**
- インタラクティブグラフ（ズーム・フィルター・ホバー）
- Streamlitとの相性が良い
- PNG画像としてエクスポート可能

**scikit-learn:**
- シンプルなAPI
- 線形回帰モデルが簡単に実装できる
- 予測精度評価メトリクスが充実

**fpdf2:**
- Python 3対応（fpdfの後継）
- 日本語フォント対応
- 画像埋め込みが簡単

---

## プロジェクト構造

```
sales_dashboard/
├── app.py                       # メインアプリケーション
├── requirements.txt             # 依存パッケージ
├── README.md                    # プロジェクト説明
├── CLAUDE.md                    # プロジェクト設計書
├── .gitignore                   # Git除外設定
│
├── src/                         # ソースコード
│   ├── __init__.py
│   ├── data_processor.py        # データ処理モジュール
│   ├── visualizer.py            # グラフ生成モジュール
│   ├── predictor.py             # 売上予測モジュール
│   └── pdf_generator.py         # PDFレポート生成モジュール
│
├── data/                        # データフォルダ
│   ├── sample/                  # サンプルデータ
│   │   └── Sample - Superstore.csv
│   └── uploads/                 # アップロードデータ（.gitignore）
│
├── assets/                      # 静的ファイル
│   ├── logo.png                 # ロゴ画像
│   └── styles.css               # カスタムCSS（オプション）
│
├── outputs/                     # 出力フォルダ
│   └── reports/                 # PDFレポート（.gitignore）
│
└── docs/                        # ドキュメント
    ├── images/                  # スクリーンショット
    ├── user_guide.md            # ユーザーガイド
    ├── developer_guide.md       # 開発者ガイド（このファイル）
    ├── test_results.md          # テスト結果
    └── 01_～13_.md              # 実装チケット
```

---

## モジュール詳細

### 1. `app.py` - メインアプリケーション

**責務:**
- Streamlitレイアウト定義
- ファイルアップロードUI
- 各モジュールの呼び出し
- セッションステート管理

**主要コンポーネント:**

```python
# ページ設定
st.set_page_config(page_title="売上ダッシュボード", layout="wide")

# サイドバー
with st.sidebar:
    uploaded_files = st.file_uploader("CSV Upload", accept_multiple_files=True)

# メインエリア（タブ）
tab1, tab2, tab3, tab4 = st.tabs(["📈 ダッシュボード", "📊 データ確認", "🔮 売上予測", "📄 レポート生成"])

with tab1:
    # ダッシュボード実装

with tab2:
    # データ確認実装

# ...
```

**キーポイント:**
- `st.session_state` でデータを永続化
- `@st.cache_data` でグラフ生成を高速化
- `st.spinner()` でローディング表示

---

### 2. `src/data_processor.py` - データ処理

**責務:**
- CSV読み込み（複数エンコーディング対応）
- 複数ファイル統合
- データクリーニング
- フィルター適用
- Excel出力

**主要関数:**

#### `load_csv(file) -> pd.DataFrame`

```python
def load_csv(file) -> pd.DataFrame:
    """CSVファイルを読み込みDataFrameを返す

    - エンコーディング自動検出（UTF-8/Shift-JIS/ISO-8859-1）
    - ファイルサイズチェック
    - 必須カラムチェック
    """
```

**実装詳細:**
- 複数エンコーディングを順番に試行
- `DataValidationError` でバリデーションエラーを捕捉
- ロガーで詳細ログを出力

#### `clean_data(df) -> pd.DataFrame`

```python
def clean_data(df: pd.DataFrame) -> pd.DataFrame:
    """データクリーニングを実行

    - 日付カラムのパース
    - 数値カラムの型変換
    - 欠損値チェック
    - 重複行削除
    """
```

**データクリーニングフロー:**
1. 日付カラム: `pd.to_datetime(errors='coerce')`
2. 数値カラム: `pd.to_numeric(errors='coerce')`
3. 欠損値: ログに警告出力（削除はしない）
4. 重複行: `df.drop_duplicates()`

---

### 3. `src/visualizer.py` - グラフ生成

**責務:**
- 7種類のPlotlyグラフ生成
- 共通レイアウト適用
- データバリデーション

**主要関数:**

#### `plot_sales_trend(df, period='daily')`

```python
def plot_sales_trend(df: pd.DataFrame, period: Literal['daily', 'monthly', 'yearly'] = 'daily'):
    """日次/月次/年次売上推移を折れ線グラフで表示"""
```

**グラフ一覧:**

| 関数名 | グラフ種類 | 必須カラム |
|--------|-----------|-----------|
| `plot_sales_trend()` | 折れ線グラフ | Order Date, Sales |
| `plot_product_ranking()` | 横棒グラフ | Product Name, Sales |
| `plot_customer_analysis()` | 散布図 | Customer Name, Sales, Profit, Segment |
| `plot_yoy_comparison()` | グループ化棒グラフ | Order Date, Sales |
| `plot_regional_sales()` | 円グラフ | Region, Sales |
| `plot_category_breakdown()` | 積み上げ棒グラフ | Order Date, Category, Sales |
| `plot_profit_margin()` | 散布図 | Product Name, Sales, Profit |

**共通レイアウト設定:**

```python
def apply_common_layout(fig, title: str):
    fig.update_layout(
        template='plotly_white',
        hovermode='x unified',
        showlegend=True,
        height=400,
        title_font_size=14,
        plot_bgcolor='#FAFBFC',
        # ...
    )
```

---

### 4. `src/predictor.py` - 売上予測

**責務:**
- データ前処理
- モデル訓練
- 将来予測
- 精度評価

**クラス構造:**

```python
class SalesPredictor:
    def __init__(self):
        self.model = LinearRegression()
        self.is_trained = False
        self.date_origin = None
        self.last_training_date = None

    def prepare_data(self, df, date_col, sales_col) -> Tuple[X, y, daily_df]:
        """データ前処理"""

    def train(self, X, y):
        """モデル訓練"""

    def predict(self, periods=30) -> pd.DataFrame:
        """将来予測"""

    def evaluate(self, y_true, y_pred) -> dict:
        """精度評価"""
```

**特徴量:**
- `DaysFromOrigin`: 起点日からの経過日数
- `DayOfWeek`: 曜日（0=月曜, 6=日曜）
- `Month`: 月（1-12）
- `Quarter`: 四半期（1-4）
- `DayOfMonth`: 月の日（1-31）
- `IsWeekend`: 週末フラグ（0/1）

**予測フロー:**
1. 日次売上に集計
2. 欠損日を0で補完
3. 特徴量作成
4. 線形回帰モデル訓練
5. 将来日付を生成
6. 予測実行（負の値は0にクリップ）

---

### 5. `src/pdf_generator.py` - PDFレポート生成

**責務:**
- PDFレポート生成
- グラフのPNG変換
- 日本語フォント対応

**クラス構造:**

```python
class ModernPDFReport(FPDF):
    def __init__(self):
        super().__init__()
        self.font_name = 'Helvetica'  # デフォルトフォント
        self.font_loaded = False

    def header(self):
        """ヘッダー（ロゴ、タイトル）"""

    def footer(self):
        """フッター（ページ番号）"""

    def add_summary_section(self, data):
        """サマリーセクション"""

    def add_chart_section(self, fig, title):
        """グラフセクション"""

    def generate_report(self, output_path):
        """レポート生成"""
```

**Plotly → PNG変換:**

```python
import plotly.io as pio

img_bytes = pio.to_image(fig, format='png', width=800, height=400, engine='kaleido')
```

**日本語フォント対応:**

```python
try:
    self.add_font('IPAGothic', '', 'ipaexg.ttf', uni=True)
    self.font_name = 'IPAGothic'
except Exception as e:
    logger.warning(f"フォント読み込みエラー: {e}. Helveticaを使用します。")
    self.font_name = 'Helvetica'
```

---

## 開発環境セットアップ

### 1. リポジトリのクローン

```bash
git clone <repository-url>
cd sales_dashboard
```

### 2. 仮想環境の作成

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

### 3. 依存パッケージのインストール

```bash
pip install -r requirements.txt
```

### 4. 開発用パッケージのインストール（オプション）

```bash
pip install black flake8 pytest
```

### 5. アプリケーション起動

```bash
streamlit run app.py
```

---

## コーディング規約

### Python スタイルガイド

**PEP 8準拠** + Google Docstring形式

#### docstring

```python
def function_name(arg1: type, arg2: type) -> return_type:
    """関数の簡潔な説明（1行）

    詳細な説明（必要な場合）

    Args:
        arg1: 引数1の説明
        arg2: 引数2の説明

    Returns:
        戻り値の説明

    Raises:
        ValueError: エラーの説明
    """
```

#### 命名規則

- **関数・変数**: スネークケース (`load_csv`, `sales_data`)
- **クラス**: パスカルケース (`SalesPredictor`, `ModernPDFReport`)
- **定数**: 大文字スネークケース (`MAX_FILE_SIZE_MB`, `REQUIRED_COLUMNS`)

#### インポート順序

```python
# 1. 標準ライブラリ
import os
import logging
from datetime import datetime

# 2. サードパーティライブラリ
import pandas as pd
import numpy as np
import streamlit as st

# 3. ローカルモジュール
from src.data_processor import load_csv
from src.visualizer import plot_sales_trend
```

### エラーハンドリング

```python
try:
    df = load_csv(file)
except DataValidationError as e:
    st.error(f"❌ {e}")
    return
except Exception as e:
    logger.error(f"予期しないエラー: {e}")
    st.error("エラーが発生しました")
    return
```

### ロギング

```python
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

logger.info("処理開始")
logger.warning("警告メッセージ")
logger.error("エラーメッセージ")
```

---

## テスト

### 手動テスト

**テスト項目**: `docs/12_テスト_動作確認.md` 参照

### ユニットテスト（推奨）

```python
# tests/test_data_processor.py
import pytest
import pandas as pd
from src.data_processor import load_csv, clean_data

def test_load_csv_valid_file():
    df = load_csv('data/sample/Sample - Superstore.csv')
    assert len(df) > 0
    assert 'Sales' in df.columns

def test_clean_data():
    df = pd.DataFrame({
        'Order Date': ['2024-01-01', '2024-01-02'],
        'Sales': ['100', '200']
    })
    cleaned_df = clean_data(df)
    assert cleaned_df['Sales'].dtype == 'float64'
```

**テスト実行:**

```bash
pytest tests/
```

---

## デプロイ

### Streamlit Cloud

1. **GitHubリポジトリにpush**

```bash
git add .
git commit -m "Initial commit"
git push origin main
```

2. **Streamlit Cloudにログイン**

https://streamlit.io/cloud

3. **アプリをデプロイ**

- 「New app」をクリック
- リポジトリ、ブランチ、`app.py` を選択
- 「Deploy!」をクリック

### Heroku

```bash
# Procfile
web: sh setup.sh && streamlit run app.py
```

```bash
# setup.sh
mkdir -p ~/.streamlit/

echo "\
[server]\n\
headless = true\n\
port = $PORT\n\
enableCORS = false\n\
\n\
" > ~/.streamlit/config.toml
```

### Docker

```dockerfile
FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

EXPOSE 8501

CMD ["streamlit", "run", "app.py"]
```

---

## 拡張方法

### 新しいグラフを追加する

#### 1. `src/visualizer.py` に関数を追加

```python
def plot_new_graph(df: pd.DataFrame):
    """新しいグラフの説明

    Args:
        df: データフレーム（'Column1', 'Column2'カラム必須）

    Returns:
        fig: Plotly figure オブジェクト
    """
    # バリデーション
    validate_dataframe_for_plot(df, required_columns=['Column1', 'Column2'])

    # グラフ作成
    fig = px.bar(df, x='Column1', y='Column2')

    # レイアウト適用
    fig = apply_common_layout(fig, "新しいグラフ")

    return fig
```

#### 2. `app.py` のダッシュボードタブに追加

```python
# ダッシュボードタブ
with tab1:
    # 既存のグラフ...

    # 新しいグラフ
    st.subheader("新しいグラフ")
    fig_new = plot_new_graph(df)
    st.plotly_chart(fig_new, use_container_width=True)
```

### 新しい予測モデルを追加する

#### 1. `src/predictor.py` に新しいクラスを追加

```python
from prophet import Prophet  # Facebook Prophet

class ProphetPredictor:
    def __init__(self):
        self.model = Prophet()

    def train(self, df):
        # Prophet用のデータフォーマット変換
        prophet_df = df.rename(columns={'Order Date': 'ds', 'Sales': 'y'})
        self.model.fit(prophet_df)

    def predict(self, periods=30):
        future = self.model.make_future_dataframe(periods=periods)
        forecast = self.model.predict(future)
        return forecast
```

#### 2. `app.py` で予測モデルを選択できるようにする

```python
model_type = st.selectbox("予測モデル", ["線形回帰", "Prophet"])

if model_type == "線形回帰":
    predictor = SalesPredictor()
else:
    predictor = ProphetPredictor()
```

### フィルター機能を追加する

#### 1. サイドバーにフィルターUIを追加

```python
with st.sidebar:
    st.subheader("フィルター")

    # 日付範囲
    date_range = st.date_input(
        "日付範囲",
        value=(df['Order Date'].min(), df['Order Date'].max())
    )

    # カテゴリ
    categories = st.multiselect(
        "カテゴリ",
        options=df['Category'].unique(),
        default=df['Category'].unique()
    )
```

#### 2. `apply_filters()` を呼び出す

```python
filters = {
    'date_range': date_range,
    'categories': categories
}

filtered_df = apply_filters(df, filters)
```

---

## API仕様

### data_processor.py

| 関数名 | 引数 | 戻り値 | 説明 |
|--------|------|--------|------|
| `load_csv(file)` | file: ファイルオブジェクトまたはパス | pd.DataFrame | CSVファイルを読み込み |
| `merge_dataframes(dfs)` | dfs: DataFrameのリスト | pd.DataFrame | 複数DataFrameを統合 |
| `clean_data(df)` | df: DataFrame | pd.DataFrame | データクリーニング |
| `apply_filters(df, filters)` | df: DataFrame, filters: dict | pd.DataFrame | フィルタリング |
| `export_to_excel(df)` | df: DataFrame | bytes | Excel出力 |

### visualizer.py

すべてのグラフ関数は `fig: plotly.graph_objects.Figure` を返す

| 関数名 | 引数 | 説明 |
|--------|------|------|
| `plot_sales_trend(df, period)` | df, period='daily'/'monthly'/'yearly' | 売上推移 |
| `plot_product_ranking(df, top_n)` | df, top_n=10 | 商品ランキング |
| `plot_customer_analysis(df)` | df | 顧客分析 |
| `plot_yoy_comparison(df)` | df | 前年同月比較 |
| `plot_regional_sales(df)` | df | 地域別売上 |
| `plot_category_breakdown(df)` | df | カテゴリ別推移 |
| `plot_profit_margin(df)` | df | 利益率分析 |

### predictor.py

| メソッド名 | 引数 | 戻り値 | 説明 |
|-----------|------|--------|------|
| `prepare_data(df, date_col, sales_col)` | df, date_col, sales_col | (X, y, daily_df) | データ前処理 |
| `train(X, y)` | X: DataFrame, y: Series | None | モデル訓練 |
| `predict(periods)` | periods: int | DataFrame | 将来予測 |
| `evaluate(y_true, y_pred)` | y_true, y_pred | dict | 精度評価 |

### pdf_generator.py

| メソッド名 | 引数 | 説明 |
|-----------|------|------|
| `add_summary_section(data)` | data: dict | サマリー追加 |
| `add_chart_section(fig, title)` | fig, title: str | グラフ追加 |
| `generate_report(output_path)` | output_path: str | レポート生成 |

---

## パフォーマンス最適化

### キャッシュの活用

```python
@st.cache_data
def load_and_clean_data(file):
    df = load_csv(file)
    df = clean_data(df)
    return df
```

### データ量の制限

大容量データ（10万行以上）は処理が遅くなるため：
- サンプリング: `df.sample(n=10000)`
- 集計: 日次→月次に集計してから表示

### グラフ描画の最適化

Plotlyのサンプリング機能を使用：

```python
fig.update_traces(marker=dict(maxdisplayed=1000))
```

---

**開発者ガイドの最終更新日**: 2025-10-10
