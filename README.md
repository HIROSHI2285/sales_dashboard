# 売上ダッシュボード＋分析レポート自動生成ツール

営業部門の売上レポート作成を完全自動化するStreamlitアプリケーション

## 📊 主な機能

- **CSVアップロード**: 複数ファイルの統合アップロード対応
- **インタラクティブダッシュボード**: 7種類のPlotlyグラフで売上を可視化
- **売上予測**: 線形回帰による将来予測（翌月/3ヶ月/半年/1年）
- **PDFレポート自動生成**: モダンなデザインのレポートをワンクリック生成

## 🚀 セットアップ

### 必要環境
- Python 3.8以上

### インストール手順

1. **依存パッケージのインストール**
```bash
pip install -r requirements.txt
```

2. **アプリケーション起動**
```bash
streamlit run app.py
```

ブラウザが自動で開き、`http://localhost:8501` でアプリが起動します。

## 📁 プロジェクト構造

```
sales_dashboard/
├── app.py                      # メインアプリケーション
├── requirements.txt            # 依存パッケージ
├── src/                        # ソースコード
│   ├── data_processor.py       # データ処理
│   ├── visualizer.py           # グラフ生成
│   ├── predictor.py            # 売上予測
│   └── pdf_generator.py        # PDFレポート生成
├── data/
│   ├── sample/                 # サンプルデータ
│   └── uploads/                # アップロードデータ
├── assets/                     # 静的ファイル（ロゴ、CSS）
└── outputs/reports/            # 生成されたPDFレポート
```

## 📊 使い方

### 1. データアップロード
- サイドバーからCSVファイルをアップロード（複数ファイル可）
- サンプルデータ（Superstore Dataset）も利用可能

### 2. ダッシュボード
- 売上推移、商品ランキング、顧客分析など7種類のグラフ
- フィルター機能で期間・カテゴリ・地域を絞り込み
- KPI（総売上、利益率、前月比）を表示

### 3. 売上予測
- 予測期間（30日/90日/180日/365日）を選択
- 線形回帰モデルで将来の売上を予測
- 精度評価指標（RMSE、MAE、R²）を表示

### 4. PDFレポート生成
- 含めるグラフを選択
- ワンクリックでモダンなPDFレポートを生成
- 自動所見コメント付き

## 📋 データフォーマット

CSVファイルは以下のカラムを含む必要があります：

| カラム名 | データ型 | 必須 |
|---------|---------|------|
| Order Date | date | ✓ |
| Sales | float | ✓ |
| Profit | float | ✓ |
| Product Name | string | ✓ |
| Customer Name | string | - |
| Region | string | - |
| Category | string | - |

サンプルデータ: `data/sample/Sample - Superstore.csv`

## 🛠️ 技術スタック

- **フレームワーク**: Streamlit 1.28.0
- **データ処理**: pandas 2.1.1
- **可視化**: Plotly 5.17.0
- **機械学習**: scikit-learn 1.3.1
- **PDF生成**: fpdf

プル