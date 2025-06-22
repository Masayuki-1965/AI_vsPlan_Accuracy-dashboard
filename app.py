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

# タイトル
st.title(f"{APP_INFO['icon']} {APP_INFO['title']}")
st.markdown("---")

# セッション状態の初期化
if 'data' not in st.session_state:
    st.session_state.data = None
if 'mapping' not in st.session_state:
    st.session_state.mapping = {}

# サイドバーナビゲーション
st.sidebar.title("📋 ナビゲーション")
pages = {
    "データアップロード": upload,
    "誤差率評価マトリクス": matrix,
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

# 選択されたページを表示
if selected_page in pages:
    pages[selected_page].show()
else:
    st.error("ページが見つかりません")

# フッター
st.markdown("---")
from config.ui_styles import FOOTER_HTML
st.markdown(FOOTER_HTML, unsafe_allow_html=True) 