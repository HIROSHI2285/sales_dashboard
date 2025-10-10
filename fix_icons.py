#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
すべての空のmaterial-iconsスパンにアイコン名を追加するスクリプト
"""

with open('app.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 各セクションのアイコンを直接置換
replacements = [
    # サイドバータイトル
    ('</span>\n            <div>\n                <div style="font-size: 1rem; font-weight: 400; color: #ECF0F1; line-height: 1.4;">売上分析</div>',
     'dashboard</span>\n            <div>\n                <div style="font-size: 1rem; font-weight: 400; color: #ECF0F1; line-height: 1.4;">売上分析</div>'),

    # CSVアップロード
    ('></span>\n            <h3 style="margin: 0; color: #2B3D4F; font-weight: 400; font-size: 1.3rem;">CSVファイルのアップロード</h3>',
     '>upload_file</span>\n            <h3 style="margin: 0; color: #2B3D4F; font-weight: 400; font-size: 1.3rem;">CSVファイルのアップロード</h3>'),

    # データエクスポート
    ('></span>\n                <h3 style="margin: 0; color: #2B3D4F; font-weight: 400; font-size: 1.3rem;">データのエクスポート</h3>',
     '>file_download</span>\n                <h3 style="margin: 0; color: #2B3D4F; font-weight: 400; font-size: 1.3rem;">データのエクスポート</h3>'),

    # KPI
    ('></span>\n                <h3 style="margin: 0; color: #2B3D4F; font-weight: 400; font-size: 1.5rem;">主要業績指標（KPI）</h3>',
     '>insights</span>\n                <h3 style="margin: 0; color: #2B3D4F; font-weight: 400; font-size: 1.5rem;">主要業績指標（KPI）</h3>'),

    # 売上推移
    ('></span>\n                <h3 style="margin: 0; color: #2B3D4F; font-weight: 400; font-size: 1.5rem;">売上推移</h3>',
     '>show_chart</span>\n                <h3 style="margin: 0; color: #2B3D4F; font-weight: 400; font-size: 1.5rem;">売上推移</h3>'),

    # 顧客分析
    ('></span>\n                    <h3 style="margin: 0; color: #2B3D4F; font-weight: 400; font-size: 1.3rem;">顧客分析</h3>',
     '>people</span>\n                    <h3 style="margin: 0; color: #2B3D4F; font-weight: 400; font-size: 1.3rem;">顧客分析</h3>'),

    # 地域別売上
    ('></span>\n                    <h3 style="margin: 0; color: #2B3D4F; font-weight: 400; font-size: 1.3rem;">地域別売上</h3>',
     '>place</span>\n                    <h3 style="margin: 0; color: #2B3D4F; font-weight: 400; font-size: 1.3rem;">地域別売上</h3>'),

    # 売上上位商品
    ('></span>\n                <h3 style="margin: 0; color: #2B3D4F; font-weight: 400; font-size: 1.3rem;">売上上位商品</h3>',
     '>shopping_cart</span>\n                <h3 style="margin: 0; color: #2B3D4F; font-weight: 400; font-size: 1.3rem;">売上上位商品</h3>'),

    # 前年同期比較
    ('></span>\n                <h3 style="margin: 0; color: #2B3D4F; font-weight: 400; font-size: 1.3rem;">前年同期比較</h3>',
     '>trending_up</span>\n                <h3 style="margin: 0; color: #2B3D4F; font-weight: 400; font-size: 1.3rem;">前年同期比較</h3>'),

    # 予測設定
    ('></span>\n                <h3 style="margin: 0; color: #2B3D4F; font-weight: 400; font-size: 1.3rem;">予測設定</h3>',
     '>settings</span>\n                <h3 style="margin: 0; color: #2B3D4F; font-weight: 400; font-size: 1.3rem;">予測設定</h3>'),

    # 予測精度
    ('></span>\n                    <h3 style="margin: 0; color: #2B3D4F; font-weight: 400; font-size: 1.3rem;">予測精度</h3>',
     '>speed</span>\n                    <h3 style="margin: 0; color: #2B3D4F; font-weight: 400; font-size: 1.3rem;">予測精度</h3>'),

    # 予測グラフ
    ('></span>\n                    <h3 style="margin: 0; color: #2B3D4F; font-weight: 400; font-size: 1.3rem;">予測グラフ</h3>',
     '>timeline</span>\n                    <h3 style="margin: 0; color: #2B3D4F; font-weight: 400; font-size: 1.3rem;">予測グラフ</h3>'),

    # レポート設定
    ('></span>\n                <h3 style="margin: 0; color: #2B3D4F; font-weight: 400; font-size: 1.3rem;">レポート設定</h3>',
     '>description</span>\n                <h3 style="margin: 0; color: #2B3D4F; font-weight: 400; font-size: 1.3rem;">レポート設定</h3>'),

    # データ概要
    ('></span>\n                <h3 style="margin: 0; color: #2B3D4F; font-weight: 400; font-size: 1.3rem;">データ概要</h3>',
     '>info</span>\n                <h3 style="margin: 0; color: #2B3D4F; font-weight: 400; font-size: 1.3rem;">データ概要</h3>'),

    # 統計情報
    ('></span>\n                <h3 style="margin: 0; color: #2B3D4F; font-weight: 400; font-size: 1.3rem;">統計情報</h3>',
     '>bar_chart</span>\n                <h3 style="margin: 0; color: #2B3D4F; font-weight: 400; font-size: 1.3rem;">統計情報</h3>'),
]

for old, new in replacements:
    content = content.replace(old, new)

with open('app.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("✅ All icons fixed successfully!")
