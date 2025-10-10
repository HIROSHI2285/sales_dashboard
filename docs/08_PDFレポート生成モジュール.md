# 08_PDFレポート生成モジュール

**Phase**: Phase 4 (Week 3)

## 概要
モダンなPDFレポートを生成する `src/pdf_generator.py` モジュールを実装します。fpdf2を使い、グラフの埋め込み、日本語対応、テーブル表示を含みます。

## タスク
- [×] `src/pdf_generator.py` 作成
- [×] 日本語フォント準備
  - [×] IPAゴシックフォントダウンロード（`ipaexg.ttf`）
  - [×] `assets/fonts/` に配置
  - [×] フォント読み込み処理実装
- [×] `ModernPDFReport` クラス実装（FPDFを継承）
  - [×] `__init__` メソッド
    - [×] PDF初期化
    - [×] 日本語フォント登録
    - [×] カラースキーム定義
  - [×] `header()` メソッド
    - [×] ロゴ画像配置（オプション、ファイル存在時のみ）
    - [×] レポートタイトル
    - [×] 生成日時
    - [×] 水平線で区切り
  - [×] `footer()` メソッド
    - [×] ページ番号表示（"Page X"形式）
  - [×] `add_summary_section(data)` メソッド
    - [×] セクションタイトル（"エグゼクティブサマリー"）
    - [×] KPIボックス配置（4つ: 総売上、利益、利益率、注文数）
    - [×] カラフルなボックスデザイン（青、オレンジ、緑、紫）
  - [×] `add_chart_section(fig, title)` メソッド
    - [×] Plotlyグラフ→PNG変換（`plotly.io.to_image`、kaleidoエンジン使用）
    - [×] BytesIOで処理
    - [×] PDF中央に画像配置
    - [×] グラフタイトル表示
  - [×] `add_table_section(df, title)` メソッド
    - [×] セクションタイトル
    - [×] テーブルヘッダー（背景色付き）
    - [×] データ行（交互に色を変える）
    - [×] 数値フォーマット（カンマ区切り）
  - [×] `add_insights_section(insights)` メソッド
    - [×] 自動所見セクション
    - [×] 箇条書きでポイント表示
  - [×] `generate_report(output_path, data)` メソッド
    - [×] 全セクション統合
    - [×] PDF保存
    - [×] 成功メッセージ返却

## 実装メモ
- Plotly→PNG変換例:
  ```python
  import plotly.io as pio
  img_bytes = pio.to_image(fig, format='png', width=800, height=400, engine='kaleido')
  ```
- fpdf2でのフォント登録:
  ```python
  pdf = FPDF()
  pdf.add_font('IPAGothic', '', 'assets/fonts/ipaexg.ttf', uni=True)
  pdf.set_font('IPAGothic', size=12)
  ```
