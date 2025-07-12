import streamlit as st
import pandas as pd
import numpy as np
from pages import upload, matrix, scatter
from config.ui_styles import CUSTOM_CSS
from config.settings import APP_INFO

# ページ設定
st.set_page_config(
    page_title=APP_INFO['title'],
    page_icon=APP_INFO['icon'],
    layout="wide",
    initial_sidebar_state="expanded"
)

# Streamlit Cloud環境でのページナビゲーションを無効化
if hasattr(st, '_get_session_state'):
    try:
        st.session_state._pages = {}
    except:
        pass

# カスタムCSSの適用
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

# ヘッダータイトル（Causal Impactと同様のデザイン）
st.markdown(f"""
<div style="
    background: linear-gradient(135deg, #1976d2 0%, #1565c0 100%);
    color: white;
    padding: 2rem;
    border-radius: 12px;
    text-align: center;
    margin-bottom: 2rem;
    box-shadow: 0 4px 12px rgba(25, 118, 210, 0.2);
">
    <h1 style="
        font-size: 2.8rem;
        margin: 0;
        font-weight: 700;
        text-shadow: 0 2px 4px rgba(0,0,0,0.1);
    ">{APP_INFO['icon']} {APP_INFO['title']}</h1>
    <p style="
        font-size: 1.2rem;
        margin: 0.5rem 0 0 0;
        opacity: 0.95;
        font-weight: 500;
        color: white;
        text-shadow: 1px 1px 2px rgba(0, 0, 0, 0.4);
    ">AI予測と現行計画値を多角的に比較・評価。計画精度を可視化し、改善余地を明らかにする実務特化型ダッシュボード</p>
</div>
""", unsafe_allow_html=True)

# セッション状態の初期化
if 'data' not in st.session_state:
    st.session_state.data = None
if 'mapping' not in st.session_state:
    st.session_state.mapping = {}

# サイドバーナビゲーション
st.sidebar.title("📋 ナビゲーション")
pages = {
    "データセット作成": upload,
    "誤差率帯別評価マトリクス": matrix,
    "散布図分析": scatter
}

selected_page = st.sidebar.selectbox(
    "ページを選択:",
    list(pages.keys())
)

# データ状態表示
if st.session_state.data is not None:
    st.sidebar.success(f"✅ データ読み込み済み ({len(st.session_state.data)}件)")
else:
    st.sidebar.warning("⚠️ データが読み込まれていません")

# 注釈の追加
st.sidebar.markdown("---")
st.sidebar.markdown("**最初からやり直す場合：**")
st.sidebar.markdown("画面左上の更新ボタン（⟳）をクリックするか、Ctrl + R を押して、STEP1のデータ取り込みから再実行してください。")

# 選択されたページを表示
if selected_page in pages:
    pages[selected_page].show()
else:
    st.error("ページが見つかりません")

# フッター
st.markdown("---")
from config.ui_styles import FOOTER_HTML
st.markdown(FOOTER_HTML, unsafe_allow_html=True) 