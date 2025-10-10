"""
グラフ可視化モジュール

7種類のPlotlyグラフを生成する機能を提供します。
"""

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from typing import Literal
import logging

# ロガー設定
logger = logging.getLogger(__name__)

# カラースキーム定義（デザインサンプル準拠）
COLORS = {
    'primary': '#3B82F6',      # 青（売上） - モダンなブルー
    'secondary': '#8B5CF6',    # パープル（利益）
    'success': '#10B981',      # 緑（増加）
    'warning': '#EF4444',      # 赤（減少）
    'info': '#6366F1',         # インディゴ（予測）
    'background': '#F9F9F9'    # 背景グレー
}

# カラーパレット（グラフ用）- クリーンでモダンな配色
COLOR_PALETTE = ['#3B82F6', '#8B5CF6', '#10B981', '#F59E0B', '#EF4444', '#06B6D4', '#EC4899', '#6366F1']


class GraphGenerationError(Exception):
    """グラフ生成エラー"""
    pass


def validate_dataframe_for_plot(df: pd.DataFrame, required_columns: list, min_rows: int = 1) -> None:
    """
    グラフ生成前のデータフレームバリデーション

    Args:
        df: チェック対象のDataFrame
        required_columns: 必須カラムのリスト
        min_rows: 最小行数

    Raises:
        GraphGenerationError: バリデーションエラー
    """
    # 空のDataFrameチェック
    if df.empty:
        raise GraphGenerationError("データが空です。グラフを生成できません。")

    # 行数チェック
    if len(df) < min_rows:
        raise GraphGenerationError(f"データ行数が不足しています（{len(df)}行）。最低{min_rows}行必要です。")

    # カラムチェック
    missing_columns = [col for col in required_columns if col not in df.columns]
    if missing_columns:
        raise GraphGenerationError(f"必須カラムが不足しています: {', '.join(missing_columns)}")

    # 必須カラムの欠損値チェック
    for col in required_columns:
        if df[col].isnull().all():
            raise GraphGenerationError(f"カラム '{col}' のすべての値が欠損しています。")

    logger.info(f"グラフ生成前バリデーション完了: {len(df)}行, 必須カラム {required_columns}")


def apply_common_layout(fig, title: str):
    """
    共通レイアウト設定を適用（デザインサンプル準拠）

    Args:
        fig: Plotly figure オブジェクト
        title: グラフタイトル

    Returns:
        fig: レイアウト適用済みfigure
    """
    fig.update_layout(
        template='plotly_white',
        hovermode='x unified',
        showlegend=True,
        height=400,  # グラフサンプルに合わせて高さ調整
        title_font_size=14,
        title_font_family='Noto Sans CJK JP, Noto Sans JP, Hiragino Sans, Meiryo',
        title_font_color='#2B3D4F',
        title_text=title,
        plot_bgcolor='#FAFBFC',  # 薄いグレー背景
        paper_bgcolor='white',
        margin=dict(l=80, r=40, t=60, b=80),
        font=dict(
            size=11,
            family='Noto Sans CJK JP, Noto Sans JP, Hiragino Sans, Meiryo',
            color='#4B5563'
        ),
        # グリッドラインをより控えめに
        xaxis=dict(
            gridcolor='#E5E7EB',
            gridwidth=0.5,
            showline=True,
            linewidth=1,
            linecolor='#D1D5DB'
        ),
        yaxis=dict(
            gridcolor='#E5E7EB',
            gridwidth=0.5,
            showline=True,
            linewidth=1,
            linecolor='#D1D5DB'
        )
    )
    return fig


def plot_sales_trend(df: pd.DataFrame, period: Literal['daily', 'monthly', 'yearly'] = 'daily'):
    """
    日次/月次/年次売上推移を折れ線グラフで表示

    Args:
        df: データフレーム（'Order Date', 'Sales'カラム必須）
        period: 集計期間（'daily', 'monthly', 'yearly'）

    Returns:
        fig: Plotly figure オブジェクト

    Raises:
        GraphGenerationError: データが不正な場合
    """
    # バリデーション
    validate_dataframe_for_plot(df, required_columns=['Order Date', 'Sales'], min_rows=2)

    df = df.copy()

    # 期間に応じてグルーピング
    if period == 'daily':
        df['Period'] = df['Order Date'].dt.date
        title = "日次売上推移"
        x_label = "日付"
    elif period == 'monthly':
        df['Period'] = df['Order Date'].dt.to_period('M').astype(str)
        title = "月次売上推移"
        x_label = "月"
    elif period == 'yearly':
        df['Period'] = df['Order Date'].dt.year
        title = "年次売上推移"
        x_label = "年"
    else:
        raise ValueError(f"Invalid period: {period}")

    # 集計
    sales_data = df.groupby('Period')['Sales'].sum().reset_index()

    # グラフ作成
    fig = px.line(
        sales_data,
        x='Period',
        y='Sales',
        markers=True,
        color_discrete_sequence=[COLORS['primary']]
    )

    # レイアウト調整
    fig = apply_common_layout(fig, title)
    fig.update_xaxes(title_text=x_label, tickangle=-45)
    fig.update_yaxes(title_text="売上 ($)")
    fig.update_traces(
        line=dict(width=2.5, shape='spline'),  # 滑らかなライン
        marker=dict(size=6, line=dict(width=1.5, color='white')),  # マーカーに白い縁
        hovertemplate='%{x}<br>売上: $%{y:,.0f}<extra></extra>'
    )

    return fig


def plot_product_ranking(df: pd.DataFrame, top_n: int = 10):
    """
    商品別売上ランキングを横棒グラフで表示

    Args:
        df: データフレーム（'Product Name', 'Sales'カラム必須）
        top_n: 表示する上位件数

    Returns:
        fig: Plotly figure オブジェクト

    Raises:
        GraphGenerationError: データが不正な場合
    """
    # バリデーション
    validate_dataframe_for_plot(df, required_columns=['Product Name', 'Sales'], min_rows=1)

    # 商品別集計
    product_sales = df.groupby('Product Name')['Sales'].sum().reset_index()

    # 上位N件を抽出して降順ソート
    top_products = product_sales.nlargest(top_n, 'Sales').sort_values('Sales', ascending=True)

    # グラフ作成
    fig = px.bar(
        top_products,
        x='Sales',
        y='Product Name',
        orientation='h',
        color_discrete_sequence=[COLORS['primary']]
    )

    # レイアウト調整
    fig = apply_common_layout(fig, f"商品別売上ランキング TOP{top_n}")
    fig.update_xaxes(title_text="売上 ($)")
    fig.update_yaxes(title_text="商品名", tickfont=dict(size=10))
    fig.update_layout(
        margin=dict(l=200, r=40, t=60, b=60),
        height=500  # 横長表示用に高さを増やす
    )
    fig.update_traces(
        marker=dict(
            line=dict(width=0.5, color='white'),
            opacity=0.9
        ),
        hovertemplate='%{y}<br>売上: $%{x:,.0f}<extra></extra>'
    )

    return fig


def plot_customer_analysis(df: pd.DataFrame):
    """
    顧客別売上・利益分析を散布図で表示

    Args:
        df: データフレーム（'Customer Name', 'Sales', 'Profit', 'Segment'カラム必須）

    Returns:
        fig: Plotly figure オブジェクト

    Raises:
        GraphGenerationError: データが不正な場合
    """
    # バリデーション
    validate_dataframe_for_plot(df, required_columns=['Customer Name', 'Sales', 'Profit', 'Segment', 'Order ID'], min_rows=1)

    # 顧客別集計
    customer_data = df.groupby(['Customer Name', 'Segment']).agg({
        'Sales': 'sum',
        'Profit': 'sum',
        'Order ID': 'count'
    }).reset_index()

    customer_data.rename(columns={'Order ID': 'Order Count'}, inplace=True)

    # グラフ作成
    fig = px.scatter(
        customer_data,
        x='Sales',
        y='Profit',
        size='Order Count',
        color='Segment',
        hover_name='Customer Name',
        color_discrete_sequence=COLOR_PALETTE
    )

    # レイアウト調整
    fig = apply_common_layout(fig, "顧客別売上・利益分析")
    fig.update_xaxes(title_text="売上 ($)")
    fig.update_yaxes(title_text="利益 ($)")
    fig.update_traces(
        marker=dict(
            opacity=0.7,
            line=dict(width=0.5, color='white')
        ),
        hovertemplate='<b>%{hovertext}</b><br>売上: $%{x:,.0f}<br>利益: $%{y:,.0f}<br>注文数: %{marker.size}<extra></extra>'
    )

    return fig


def plot_yoy_comparison(df: pd.DataFrame):
    """
    前年同月比較をグループ化棒グラフで表示

    Args:
        df: データフレーム（'Order Date', 'Sales'カラム必須）

    Returns:
        fig: Plotly figure オブジェクト

    Raises:
        GraphGenerationError: データが不正な場合
    """
    # バリデーション
    validate_dataframe_for_plot(df, required_columns=['Order Date', 'Sales'], min_rows=2)

    df = df.copy()

    # 年・月を抽出
    df['Year'] = df['Order Date'].dt.year.astype(str)
    df['Month'] = df['Order Date'].dt.month

    # 年別・月別集計
    yoy_data = df.groupby(['Year', 'Month'])['Sales'].sum().reset_index()

    # 月名を追加
    month_names = {1: '1月', 2: '2月', 3: '3月', 4: '4月', 5: '5月', 6: '6月',
                   7: '7月', 8: '8月', 9: '9月', 10: '10月', 11: '11月', 12: '12月'}
    yoy_data['Month Name'] = yoy_data['Month'].map(month_names)

    # グラフ作成
    fig = px.bar(
        yoy_data,
        x='Month Name',
        y='Sales',
        color='Year',
        barmode='group',
        color_discrete_sequence=COLOR_PALETTE
    )

    # レイアウト調整
    fig = apply_common_layout(fig, "前年同月比較")
    fig.update_xaxes(title_text="月", tickangle=0)
    fig.update_yaxes(title_text="売上 ($)")
    fig.update_layout(height=450)  # 横長表示用に高さを増やす
    fig.update_traces(
        marker=dict(
            line=dict(width=0.5, color='white'),
            opacity=0.9
        ),
        hovertemplate='%{x}<br>%{fullData.name}<br>売上: $%{y:,.0f}<extra></extra>'
    )

    return fig


def plot_regional_sales(df: pd.DataFrame):
    """
    地域別売上を円グラフで表示

    Args:
        df: データフレーム（'Region', 'Sales'カラム必須）

    Returns:
        fig: Plotly figure オブジェクト

    Raises:
        GraphGenerationError: データが不正な場合
    """
    # バリデーション
    validate_dataframe_for_plot(df, required_columns=['Region', 'Sales'], min_rows=1)

    # 地域別集計
    regional_sales = df.groupby('Region')['Sales'].sum().reset_index()

    # グラフ作成
    fig = px.pie(
        regional_sales,
        names='Region',
        values='Sales',
        color_discrete_sequence=COLOR_PALETTE
    )

    # レイアウト調整
    fig = apply_common_layout(fig, "地域別売上構成")
    fig.update_traces(
        textposition='inside',
        textinfo='percent+label',
        textfont=dict(size=12, family='Noto Sans CJK JP, Noto Sans JP, Hiragino Sans, Meiryo'),
        marker=dict(line=dict(color='white', width=2.5)),
        hole=0.4,  # ドーナツチャート風に
        hovertemplate='<b>%{label}</b><br>売上: $%{value:,.0f}<br>割合: %{percent}<extra></extra>'
    )

    return fig


def plot_category_breakdown(df: pd.DataFrame):
    """
    カテゴリ別・期間別売上を積み上げ棒グラフで表示

    Args:
        df: データフレーム（'Order Date', 'Category', 'Sales'カラム必須）

    Returns:
        fig: Plotly figure オブジェクト

    Raises:
        GraphGenerationError: データが不正な場合
    """
    # バリデーション
    validate_dataframe_for_plot(df, required_columns=['Order Date', 'Category', 'Sales'], min_rows=2)

    df = df.copy()

    # 月次データ作成
    df['Month'] = df['Order Date'].dt.to_period('M').astype(str)

    # カテゴリ別・月別集計
    category_data = df.groupby(['Month', 'Category'])['Sales'].sum().reset_index()

    # グラフ作成
    fig = px.bar(
        category_data,
        x='Month',
        y='Sales',
        color='Category',
        barmode='stack',
        color_discrete_sequence=COLOR_PALETTE
    )

    # レイアウト調整
    fig = apply_common_layout(fig, "カテゴリ別売上推移（積み上げ）")
    fig.update_xaxes(title_text="月", tickangle=-45)
    fig.update_yaxes(title_text="売上 ($)")
    fig.update_traces(marker=dict(line=dict(width=0.5, color='white')))

    return fig


def plot_profit_margin(df: pd.DataFrame):
    """
    商品別売上・利益率分析を散布図で表示

    Args:
        df: データフレーム（'Product Name', 'Sales', 'Profit'カラム必須）

    Returns:
        fig: Plotly figure オブジェクト

    Raises:
        GraphGenerationError: データが不正な場合
    """
    # バリデーション
    validate_dataframe_for_plot(df, required_columns=['Product Name', 'Sales', 'Profit'], min_rows=1)

    # 商品別集計
    product_data = df.groupby('Product Name').agg({
        'Sales': 'sum',
        'Profit': 'sum'
    }).reset_index()

    # 利益率計算
    product_data['Profit Margin (%)'] = (product_data['Profit'] / product_data['Sales'] * 100).round(2)

    # 外れ値除去（利益率が-100%～100%の範囲）
    product_data = product_data[
        (product_data['Profit Margin (%)'] >= -100) &
        (product_data['Profit Margin (%)'] <= 100)
    ]

    # グラフ作成
    fig = px.scatter(
        product_data,
        x='Sales',
        y='Profit Margin (%)',
        color='Profit Margin (%)',
        hover_name='Product Name',
        color_continuous_scale=['red', 'yellow', 'green']
    )

    # レイアウト調整
    fig = apply_common_layout(fig, "商品別利益率分析")
    fig.update_xaxes(title_text="売上 ($)")
    fig.update_yaxes(title_text="利益率 (%)")

    return fig
