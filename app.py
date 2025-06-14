import streamlit as st
import pandas as pd
import numpy as np
from pages import upload, matrix, scatter

# ページ設定
st.set_page_config(
    page_title="需要予測vs計画値比較分析ダッシュボード",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# タイトル
st.title("📊 需要予測vs計画値比較分析ダッシュボード")
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
st.markdown(
    """
    <div style='text-align: center; color: gray; font-size: 12px;'>
    需要予測vs計画値比較分析ダッシュボード v1.0 | Phase 1 (MVP-50%)
    </div>
    """, 
    unsafe_allow_html=True
) 