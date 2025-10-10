"""
売上ダッシュボード - メインアプリケーション (Modern UI)

Netflix風のモダンなUIで営業部門の売上レポート作成を完全自動化
"""

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from src.data_processor import (
    load_csv,
    merge_dataframes,
    clean_data,
    apply_filters,
    export_to_excel,
    DataValidationError,
    validate_data_types,
    validate_missing_values
)
from src.visualizer import (
    plot_sales_trend,
    plot_product_ranking,
    plot_customer_analysis,
    plot_yoy_comparison,
    plot_regional_sales,
    plot_category_breakdown,
    plot_profit_margin,
    GraphGenerationError
)
from src.predictor import SalesPredictor
from src.pdf_generator import ModernPDFReport
import plotly.graph_objects as go
import os

# ページ設定
st.set_page_config(
    page_title="Sales Analytics Dashboard",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Material Icons読み込み（不要なためコメントアウト）
# st.markdown("""
#     <link href="https://fonts.googleapis.com/icon?family=Material+Icons" rel="stylesheet">
# """, unsafe_allow_html=True)

# カスタムCSS読み込み
try:
    with open('assets/styles.css', 'r', encoding='utf-8') as f:
        st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)
except FileNotFoundError:
    pass

# セッションステート初期化
if 'data' not in st.session_state:
    st.session_state.data = None
if 'original_data' not in st.session_state:
    st.session_state.original_data = None
if 'uploaded_files_count' not in st.session_state:
    st.session_state.uploaded_files_count = 0
if 'page' not in st.session_state:
    st.session_state.page = "データアップロード"

# ============================================================================
# サイドバーナビゲーション
# ============================================================================

with st.sidebar:
    # タイトル
    st.markdown("""
        <div style="margin-bottom: 2rem; padding: 0 1rem;">
            <div style="font-size: 1.5rem; font-weight: 600; color: #ECF0F1; line-height: 1.3; margin-bottom: 0.3rem;">売上分析</div>
            <div style="font-size: 1.5rem; font-weight: 600; color: #ECF0F1; line-height: 1.3;">ダッシュボード</div>
        </div>
    """, unsafe_allow_html=True)
    st.markdown("---")

    # ナビゲーションメニュー
    menu_items = [
        ("データアップロード", "upload"),
        ("ダッシュボード", "apps"),
        ("売上予測", "insert_chart"),
        ("レポート生成", "description"),
        ("データ確認", "list_alt")
    ]

    # 現在のページを取得
    if 'current_page' not in st.session_state:
        st.session_state.current_page = "データアップロード"

    # ラジオボタンで表示
    page_names = [item[0] for item in menu_items]
    selected_index = page_names.index(st.session_state.current_page) if st.session_state.current_page in page_names else 0

    selected_page = st.radio(
        "メニュー",
        page_names,
        index=selected_index,
        label_visibility="collapsed",
        key="navigation_menu"
    )

    if selected_page != st.session_state.current_page:
        st.session_state.current_page = selected_page
        st.rerun()

    page = st.session_state.current_page
    st.session_state.page = page

    st.markdown("---")

    # データステータス表示
    if st.session_state.data is not None:
        st.success("データ読み込み済み")
        col1, col2 = st.columns(2)
        with col1:
            st.metric("データ行数", f"{len(st.session_state.data):,}")
        with col2:
            st.metric("カラム数", len(st.session_state.data.columns))

# ============================================================================
# ページルーティング
# ============================================================================

# メインタイトル
st.markdown(f"# {page}")
st.markdown("---")

# ----------------------------------------------------------------------------
# データアップロードページ
# ----------------------------------------------------------------------------
if page == "データアップロード":
    st.subheader("CSVファイルのアップロード")

    col1, col2 = st.columns(2)

    with col1:
        uploaded_files = st.file_uploader(
            "CSVファイルを選択",
            type=['csv'],
            accept_multiple_files=True,
            help="複数のCSVファイルを選択すると自動で統合されます",
            key="file_uploader"
        )

    with col1:
        if st.button("サンプルデータを読み込む", use_container_width=True, type="primary"):
            try:
                sample_path = "data/sample/Sample - Superstore.csv"
                if not os.path.exists(sample_path):
                    st.error(f"サンプルデータが見つかりません: {sample_path}")
                else:
                    with st.spinner("サンプルデータを読み込み中..."):
                        df = load_csv(sample_path)
                        df = clean_data(df)
                        st.session_state.data = df
                        st.session_state.original_data = df.copy()
                        st.session_state.uploaded_files_count = 1
                        st.rerun()
            except DataValidationError as e:
                st.error(f"データ検証エラー: {e}")
            except Exception as e:
                st.error(f"失敗: {e}")
                import traceback
                st.code(traceback.format_exc())

    if uploaded_files:
        try:
            with st.spinner("ファイルを読み込み中..."):
                dfs = []
                for uploaded_file in uploaded_files:
                    df = load_csv(uploaded_file)
                    dfs.append(df)

                merged_df = merge_dataframes(dfs) if len(dfs) > 1 else dfs[0]
                cleaned_df = clean_data(merged_df)

                st.session_state.data = cleaned_df
                st.session_state.original_data = cleaned_df.copy()
                st.session_state.uploaded_files_count = len(uploaded_files)

                st.success(f"読み込み完了: {len(cleaned_df):,} 行 × {len(cleaned_df.columns)} 列")
        except Exception as e:
            st.error(f"エラー: {e}")

    # Excelダウンロードボタン
    if st.session_state.data is not None:
        st.markdown("---")
        st.subheader("データのエクスポート")

        col1, col2 = st.columns(2)
        with col1:
            try:
                excel_data = export_to_excel(st.session_state.data)
                st.download_button(
                    label="Excelファイルをダウンロード",
                    data=excel_data,
                    file_name=f"sales_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True
                )
            except Exception as e:
                st.error(f"Excel生成エラー: {e}")

# ----------------------------------------------------------------------------
# ダッシュボードページ
# ----------------------------------------------------------------------------
elif page == "ダッシュボード":
    if st.session_state.data is None:
        st.info("「データアップロード」ページからデータをアップロードしてください")
    else:
        df = st.session_state.data

        # KPI表示
        st.subheader("主要業績指標（KPI）")
        kpi1, kpi2, kpi3, kpi4 = st.columns(4)

        with kpi1:
            total_sales = df['Sales'].sum() if 'Sales' in df.columns else 0
            st.metric("総売上", f"${total_sales:,.0f}")

        with kpi2:
            total_profit = df['Profit'].sum() if 'Profit' in df.columns else 0
            st.metric("総利益", f"${total_profit:,.0f}")

        with kpi3:
            avg_margin = (total_profit / total_sales * 100) if total_sales > 0 else 0
            st.metric("平均利益率", f"{avg_margin:.1f}%")

        with kpi4:
            total_orders = df['Order ID'].nunique() if 'Order ID' in df.columns else len(df)
            st.metric("総注文数", f"{total_orders:,}")

        st.markdown("---")

        # グラフ表示
        st.subheader("売上推移")
        try:
            fig_trend = plot_sales_trend(df, period='monthly')
            st.plotly_chart(fig_trend, use_container_width=True)
        except GraphGenerationError as e:
            st.error(f"{e}")

        st.markdown("---")

        # 顧客分析と地域別売上を横並び
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("顧客分析")
            try:
                fig_customer = plot_customer_analysis(df)
                st.plotly_chart(fig_customer, use_container_width=True)
            except GraphGenerationError as e:
                st.error(f"{e}")

        with col2:
            st.subheader("地域別売上")
            try:
                fig_region = plot_regional_sales(df)
                st.plotly_chart(fig_region, use_container_width=True)
            except GraphGenerationError as e:
                st.error(f"{e}")

        st.markdown("---")

        # 売上上位商品を横長表示
        st.subheader("売上上位商品")
        try:
            fig_product = plot_product_ranking(df, top_n=10)
            st.plotly_chart(fig_product, use_container_width=True)
        except GraphGenerationError as e:
            st.error(f"{e}")

        st.markdown("---")

        # 前年同期比較を横長表示
        st.subheader("前年同期比較")
        try:
            fig_yoy = plot_yoy_comparison(df)
            st.plotly_chart(fig_yoy, use_container_width=True)
        except GraphGenerationError as e:
            st.error(f"{e}")

# ----------------------------------------------------------------------------
# 売上予測ページ
# ----------------------------------------------------------------------------
elif page == "売上予測":
    if st.session_state.data is None:
        st.info("まずデータをアップロードしてください")
    else:
        st.subheader("予測設定")

        col1, col2 = st.columns(2)
        with col1:
            selected_periods = st.selectbox(
                "予測期間",
                options=[30, 90, 180, 365],
                format_func=lambda x: {30: "翌月（30日）", 90: "3ヶ月", 180: "6ヶ月", 365: "1年"}[x]
            )

            if st.button("予測を実行", type="primary", use_container_width=True):
                with st.spinner("モデルを学習中..."):
                    try:
                        predictor = SalesPredictor()
                        X, y, daily_df = predictor.prepare_data(st.session_state.data)
                        X_train, X_test, y_train, y_test = predictor.train_test_split_temporal(X, y, test_size=0.2)
                        predictor.train(X_train, y_train)
                        y_test_pred = predictor.model.predict(X_test)
                        metrics = predictor.evaluate(y_test, y_test_pred)
                        future_df = predictor.predict(periods=selected_periods)

                        st.session_state.prediction_results = {
                            'predictor': predictor,
                            'daily_df': daily_df,
                            'X_train': X_train,
                            'X_test': X_test,
                            'y_test': y_test,
                            'y_test_pred': y_test_pred,
                            'metrics': metrics,
                            'future_df': future_df,
                            'periods': selected_periods
                        }
                        st.success("予測が完了しました！")
                    except Exception as e:
                        st.error(f"予測エラー: {e}")

        if 'prediction_results' in st.session_state:
            results = st.session_state.prediction_results
            metrics = results['metrics']

            st.subheader("予測精度")
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("RMSE（二乗平均平方根誤差）", f"${metrics['RMSE']:,.0f}")
            with col2:
                st.metric("MAE（平均絶対誤差）", f"${metrics['MAE']:,.0f}")
            with col3:
                st.metric("R²スコア", f"{metrics['R2_Score']:.3f}")

            st.subheader("予測グラフ")
            daily_df = results['daily_df']
            future_df = results['future_df']

            fig = go.Figure()
            train_size = len(results['X_train'])
            train_df = daily_df.iloc[:train_size]
            test_df = daily_df.iloc[train_size:]

            fig.add_trace(go.Scatter(x=train_df['Date'], y=train_df['Sales'], mode='lines', name='学習データ'))
            fig.add_trace(go.Scatter(x=test_df['Date'], y=test_df['Sales'], mode='lines', name='テストデータ'))
            fig.add_trace(go.Scatter(x=test_df['Date'], y=results['y_test_pred'], mode='lines', name='テスト予測', line=dict(dash='dot')))
            fig.add_trace(go.Scatter(x=future_df['Date'], y=future_df['Predicted_Sales'], mode='lines', name='将来予測', line=dict(dash='dash')))

            fig.update_layout(template='plotly_dark', height=500)
            st.plotly_chart(fig, use_container_width=True)

# ----------------------------------------------------------------------------
# レポート生成ページ
# ----------------------------------------------------------------------------
elif page == "レポート生成":
    if st.session_state.data is None:
        st.info("先にデータをアップロードしてください")
    else:
        st.subheader("レポート設定")

        col1, col2 = st.columns(2)
        with col1:
            report_title = st.text_input("レポートタイトル", value="売上分析レポート")

            if st.button("レポート生成", type="primary", use_container_width=True):
                with st.spinner("PDFレポートを生成中..."):
                    try:
                        df = st.session_state.data

                        # サマリーデータ作成
                        summary_data = {
                            'total_sales': df['Sales'].sum() if 'Sales' in df.columns else 0,
                            'total_profit': df['Profit'].sum() if 'Profit' in df.columns else 0,
                            'profit_margin': (df['Profit'].sum() / df['Sales'].sum() * 100) if 'Sales' in df.columns and df['Sales'].sum() > 0 else 0,
                            'total_orders': df['Order ID'].nunique() if 'Order ID' in df.columns else len(df)
                        }

                        # グラフ生成（個別に生成して配列に追加）
                        from src.visualizer import plot_sales_trend, plot_product_ranking, plot_regional_sales

                        # 月次売上推移
                        st.info("月次売上推移グラフを生成中...")
                        fig_sales_trend = plot_sales_trend(df, period='monthly')
                        st.success(f"月次売上推移グラフ生成完了: {fig_sales_trend.layout.title.text}")

                        # 売上上位商品
                        st.info("売上上位商品グラフを生成中...")
                        fig_product_ranking = plot_product_ranking(df, top_n=10)
                        st.success(f"売上上位商品グラフ生成完了: {fig_product_ranking.layout.title.text}")

                        # 地域別売上構成
                        st.info("地域別売上構成グラフを生成中...")
                        fig_regional_sales = plot_regional_sales(df)
                        st.success(f"地域別売上構成グラフ生成完了: {fig_regional_sales.layout.title.text}")

                        charts = [
                            (fig_sales_trend, "月次売上推移"),
                            (fig_product_ranking, "売上上位商品"),
                            (fig_regional_sales, "地域別売上構成")
                        ]

                        # テーブルデータ
                        product_sales = df.groupby('Product Name')['Sales'].sum().reset_index()
                        top_products = product_sales.nlargest(10, 'Sales')

                        tables = [
                            (top_products, "売上上位10商品")
                        ]

                        # 所見生成
                        total_sales = summary_data['total_sales']
                        profit_margin = summary_data['profit_margin']

                        insights = [
                            f"総売上は ${total_sales:,.0f} で、利益率は {profit_margin:.1f}% です。",
                            f"総注文数は {summary_data['total_orders']:,} 件でした。",
                            "売上上位商品に注力することで、さらなる収益向上が見込めます。"
                        ]

                        # PDFレポート生成
                        pdf = ModernPDFReport()
                        pdf.report_title = report_title

                        # 出力ディレクトリ作成
                        os.makedirs("outputs/reports", exist_ok=True)

                        output_path = f"outputs/reports/sales_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
                        pdf.generate_report(
                            output_path=output_path,
                            summary_data=summary_data,
                            charts=charts,
                            tables=tables,
                            insights=insights
                        )

                        # ダウンロードボタン表示
                        with open(output_path, "rb") as f:
                            pdf_data = f.read()

                        st.success("PDFレポートを生成しました！")
                        st.download_button(
                            label="PDFレポートをダウンロード",
                            data=pdf_data,
                            file_name=f"{report_title}_{datetime.now().strftime('%Y%m%d')}.pdf",
                            mime="application/pdf",
                            use_container_width=True
                        )

                    except Exception as e:
                        st.error(f"レポート生成エラー: {e}")
                        import traceback
                        st.code(traceback.format_exc())

# ----------------------------------------------------------------------------
# データ確認ページ
# ----------------------------------------------------------------------------
elif page == "データ確認":
    if st.session_state.data is None:
        st.info("先にデータをアップロードしてください")
    else:
        df = st.session_state.data

        st.subheader("データ概要")
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("総行数", f"{len(df):,}")
        with col2:
            st.metric("カラム数", len(df.columns))
        with col3:
            if 'Order Date' in df.columns:
                date_range = (df['Order Date'].max() - df['Order Date'].min()).days
                st.metric("期間（日数）", f"{date_range:,}")
        with col4:
            if 'Sales' in df.columns:
                st.metric("総売上", f"${df['Sales'].sum():,.0f}")

        st.markdown("---")

        st.subheader("データプレビュー")
        st.dataframe(df.head(20), use_container_width=True)

        st.markdown("---")

        st.subheader("統計情報")
        st.dataframe(df.describe(), use_container_width=True)
