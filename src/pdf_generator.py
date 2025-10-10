"""
PDFレポート生成モジュール

fpdf2を使ったモダンなPDFレポート生成機能を提供します。
"""

from fpdf import FPDF
import pandas as pd
import plotly.graph_objects as go
import plotly.io as pio
from datetime import datetime
from io import BytesIO
import os

# カラースキーム（デザインサンプル準拠）
COLORS = {
    'primary': (59, 130, 246),      # モダンブルー #3B82F6
    'secondary': (139, 92, 246),    # パープル #8B5CF6
    'success': (16, 185, 129),      # グリーン #10B981
    'danger': (239, 68, 68),        # レッド #EF4444
    'info': (99, 102, 241),         # インディゴ #6366F1
    'light_gray': (249, 249, 249),  # 薄いグレー #F9F9F9
    'dark_gray': (43, 61, 79)       # ダークグレー #2B3D4F
}


class ModernPDFReport(FPDF):
    """
    モダンなPDFレポートクラス

    日本語対応、グラフ埋め込み、カラフルなKPIボックスを含む
    売上レポートを生成します。
    """

    def __init__(self):
        """初期化"""
        super().__init__()

        # 日本語フォント登録
        font_path = os.path.join('assets', 'fonts', 'ipaexg.ttf')
        if os.path.exists(font_path):
            try:
                self.add_font('IPAGothic', '', font_path, uni=True)
                self.font_name = 'IPAGothic'
                self.font_loaded = True
            except Exception as e:
                import logging
                logging.warning(f"フォント読み込みエラー: {e}. Helveticaを使用します。")
                self.font_name = 'Helvetica'
                self.font_loaded = False
        else:
            # フォントがない場合はHelveticaを使用
            import logging
            logging.info("日本語フォントが見つかりません。Helveticaを使用します。")
            self.font_name = 'Helvetica'
            self.font_loaded = False

        # レポートメタデータ
        self.report_title = "売上分析レポート"
        self.generation_date = datetime.now().strftime('%Y年%m月%d日')

    def header(self):
        """ページヘッダー"""
        # タイトル
        self.set_font(self.font_name, '', 20)
        self.set_text_color(*COLORS['primary'])
        self.cell(0, 10, self.report_title, 0, 1, 'C')

        # 生成日時
        self.set_font(self.font_name, '', 10)
        self.set_text_color(100, 100, 100)
        self.cell(0, 5, f'生成日: {self.generation_date}', 0, 1, 'C')

        # 水平線
        self.set_draw_color(*COLORS['primary'])
        self.set_line_width(0.5)
        self.line(10, self.get_y() + 2, 200, self.get_y() + 2)
        self.ln(5)

    def footer(self):
        """ページフッター"""
        self.set_y(-15)
        self.set_font(self.font_name, '', 8)
        self.set_text_color(100, 100, 100)

        # ページ番号
        self.cell(0, 10, f'Page {self.page_no()}', 0, 0, 'C')

    def add_summary_section(self, summary_data: dict):
        """
        エグゼクティブサマリーセクション

        Args:
            summary_data: {
                'total_sales': 1000000,
                'total_profit': 200000,
                'profit_margin': 20.0,
                'total_orders': 500
            }
        """
        self.set_font(self.font_name, '', 16)
        self.set_text_color(*COLORS['dark_gray'])
        self.cell(0, 10, 'エグゼクティブサマリー', 0, 1)
        self.ln(5)

        # KPIボックス（2x2レイアウト）
        box_width = 90
        box_height = 25

        kpis = [
            ('総売上', f"${summary_data.get('total_sales', 0):,.0f}", COLORS['primary']),
            ('総利益', f"${summary_data.get('total_profit', 0):,.0f}", COLORS['success']),
            ('平均利益率', f"{summary_data.get('profit_margin', 0):.1f}%", COLORS['info']),
            ('総注文数', f"{summary_data.get('total_orders', 0):,}", COLORS['secondary'])
        ]

        x_start = 10
        y_start = self.get_y()

        for i, (label, value, color) in enumerate(kpis):
            row = i // 2
            col = i % 2

            x = x_start + col * (box_width + 10)
            y = y_start + row * (box_height + 5)

            # ボックス背景
            self.set_fill_color(color[0], color[1], color[2])
            self.set_xy(x, y)
            self.rect(x, y, box_width, box_height, 'F')

            # ラベル
            self.set_xy(x + 5, y + 5)
            self.set_font(self.font_name, '', 10)
            self.set_text_color(255, 255, 255)
            self.cell(box_width - 10, 5, label, 0, 1)

            # 値
            self.set_xy(x + 5, y + 12)
            self.set_font(self.font_name, '', 14)
            self.cell(box_width - 10, 8, value, 0, 0)

        self.set_y(y_start + 2 * (box_height + 5) + 10)

    def add_chart_section(self, fig, title: str):
        """
        グラフセクション

        Args:
            fig: Plotly figure オブジェクト
            title: セクションタイトル
        """
        # セクションタイトル
        self.set_font(self.font_name, '', 14)
        self.set_text_color(*COLORS['dark_gray'])
        self.cell(0, 10, title, 0, 1)
        self.ln(2)

        # Plotly → PNG変換
        try:
            import uuid

            # グラフデータの検証
            if fig is None:
                raise ValueError("グラフオブジェクトがNullです")

            img_bytes = pio.to_image(
                fig,
                format='png',
                width=800,
                height=400,
                engine='kaleido'
            )

            if not img_bytes or len(img_bytes) == 0:
                raise ValueError("グラフ画像の生成に失敗しました（空の画像データ）")

            # BytesIOに保存
            img_buffer = BytesIO(img_bytes)

            # PDF中央に配置
            img_width = 180
            x_centered = (210 - img_width) / 2

            # 一時ファイルに保存（ユニークな名前を使用）
            temp_path = f'temp_chart_{uuid.uuid4().hex}.png'

            try:
                with open(temp_path, 'wb') as f:
                    f.write(img_bytes)
            except PermissionError:
                raise PermissionError(f"ファイル '{temp_path}' の書き込み権限がありません。")
            except OSError as e:
                if "No space left on device" in str(e):
                    raise OSError("ディスク容量が不足しています。")
                raise

            self.image(temp_path, x=x_centered, w=img_width)

            # 一時ファイル削除
            try:
                os.remove(temp_path)
            except Exception as cleanup_error:
                import logging
                logging.warning(f"一時ファイル削除エラー: {cleanup_error}")

        except ImportError as e:
            self.set_font(self.font_name, '', 10)
            self.set_text_color(200, 0, 0)
            self.cell(0, 10, 'kaleidoパッケージがインストールされていません', 0, 1)
            import logging
            logging.error(f"Kaleido import error: {e}")

        except Exception as e:
            self.set_font(self.font_name, '', 10)
            self.set_text_color(200, 0, 0)
            self.cell(0, 10, f'グラフ生成エラー: {str(e)}', 0, 1)
            import logging
            logging.error(f"Chart generation error: {e}")

        self.ln(5)

    def add_table_section(self, df: pd.DataFrame, title: str, max_rows: int = 10):
        """
        テーブルセクション

        Args:
            df: 表示するDataFrame
            title: セクションタイトル
            max_rows: 最大表示行数
        """
        # セクションタイトル
        self.set_font(self.font_name, '', 14)
        self.set_text_color(*COLORS['dark_gray'])
        self.cell(0, 10, title, 0, 1)
        self.ln(2)

        # データ制限
        display_df = df.head(max_rows)

        # カラム幅計算
        num_cols = len(display_df.columns)
        col_width = 180 / num_cols
        row_height = 8

        # ヘッダー
        self.set_font(self.font_name, '', 9)
        self.set_fill_color(*COLORS['primary'])
        self.set_text_color(255, 255, 255)

        for col in display_df.columns:
            self.cell(col_width, row_height, str(col)[:20], 1, 0, 'C', True)
        self.ln()

        # データ行
        self.set_text_color(*COLORS['dark_gray'])

        for i, row in display_df.iterrows():
            # 交互に色を変える
            if i % 2 == 0:
                self.set_fill_color(*COLORS['light_gray'])
                fill = True
            else:
                fill = False

            for value in row:
                # 数値フォーマット
                if isinstance(value, (int, float)):
                    text = f"{value:,.0f}" if isinstance(value, int) else f"{value:,.2f}"
                else:
                    text = str(value)[:20]

                self.cell(col_width, row_height, text, 1, 0, 'C', fill)
            self.ln()

        self.ln(5)

    def add_insights_section(self, insights: list):
        """
        所見セクション

        Args:
            insights: 所見テキストのリスト
        """
        # セクションタイトル
        self.set_font(self.font_name, '', 14)
        self.set_text_color(*COLORS['dark_gray'])
        self.cell(0, 10, '分析所見', 0, 1)
        self.ln(2)

        # 箇条書き
        self.set_font(self.font_name, '', 10)
        self.set_text_color(*COLORS['dark_gray'])

        for insight in insights:
            self.cell(5, 6, '•', 0, 0)
            self.multi_cell(0, 6, insight)
            self.ln(1)

        self.ln(5)

    def generate_report(
        self,
        output_path: str,
        summary_data: dict,
        charts: list = None,
        tables: list = None,
        insights: list = None
    ) -> str:
        """
        レポート生成

        Args:
            output_path: 出力ファイルパス
            summary_data: サマリーデータ
            charts: [(fig, title), ...] のリスト
            tables: [(df, title), ...] のリスト
            insights: 所見のリスト

        Returns:
            生成されたファイルパス

        Raises:
            PermissionError: ファイル書き込み権限がない場合
            OSError: ディスク容量不足の場合
            ValueError: データが不正な場合
        """
        import logging

        # 出力ディレクトリの存在確認
        output_dir = os.path.dirname(output_path)
        if output_dir and not os.path.exists(output_dir):
            try:
                os.makedirs(output_dir, exist_ok=True)
            except PermissionError:
                raise PermissionError(f"ディレクトリ '{output_dir}' の作成権限がありません。")

        # データの検証
        if not summary_data:
            raise ValueError("サマリーデータが提供されていません。")

        try:
            # ページ追加
            self.add_page()

            # サマリーセクション
            self.add_summary_section(summary_data)

            # グラフセクション
            if charts:
                for fig, title in charts:
                    # ページが足りない場合は新規ページ
                    if self.get_y() > 200:
                        self.add_page()
                    self.add_chart_section(fig, title)

            # テーブルセクション
            if tables:
                for df, title in tables:
                    if self.get_y() > 200:
                        self.add_page()
                    self.add_table_section(df, title)

            # 所見セクション
            if insights:
                if self.get_y() > 220:
                    self.add_page()
                self.add_insights_section(insights)

            # PDF保存
            try:
                self.output(output_path)
            except PermissionError:
                raise PermissionError(f"ファイル '{output_path}' の書き込み権限がありません。")
            except OSError as e:
                if "No space left on device" in str(e):
                    raise OSError("ディスク容量が不足しています。")
                raise

            logging.info(f"PDFレポート生成完了: {output_path}")

            return output_path

        except Exception as e:
            logging.error(f"PDFレポート生成エラー: {e}")
            raise
