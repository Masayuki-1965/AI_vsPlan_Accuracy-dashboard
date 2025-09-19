import streamlit as st
from pages import upload, matrix, scatter, monthly_trend
from config.ui_styles import CUSTOM_CSS, FOOTER_HTML
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

# ヘッダータイトル（統一デザイン）
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
        text-align: left;
    ">AI予測値と現行計画値を多角的に比較・評価し、計画精度を可視化。改善余地を明らかにする実務特化型ダッシュボード。誰でも同じ基準で簡単に分析できます。</p>
</div>
""", unsafe_allow_html=True)

# セッション状態の初期化
session_defaults = {
    'data': None,
    'mapping': {}
}

for key, default_value in session_defaults.items():
    if key not in st.session_state:
        st.session_state[key] = default_value

# サイドバーナビゲーション
st.sidebar.markdown("""
<div style="
    font-size: 1.4em;
    font-weight: bold;
    color: #1976d2;
    border-left: 4px solid #1976d2;
    padding-left: 12px;
    margin-bottom: 1em;
    margin-top: 0;
">ナビゲーション</div>
""", unsafe_allow_html=True)

# ナビゲーション用カスタムCSS（改善前方式ベース）
st.markdown("""
<style>
/* サイドバーのラジオボタンスタイル */
.stSidebar .stRadio > div {
    gap: 0.2rem;
}

.stSidebar .stRadio > div > label {
    background: transparent;
    border-radius: 8px;
    padding: 0.6rem 0.8rem;
    margin: 0.1rem 0;
    transition: all 0.2s ease;
    cursor: pointer;
    display: flex;
    align-items: center;
    border: 1px solid #e0e0e0;
}

.stSidebar .stRadio > div > label:hover {
    background: #f5f7fa;
    border: 1px solid #d0d7de;
}

.stSidebar .stRadio > div > label[data-checked="true"] {
    background: #e3f2fd;
    border: 2px solid #1976d2;
}

/* フォント調整 */
.stSidebar .stRadio > div > label > div:last-child {
    font-size: 1.05rem;
    font-weight: 600;
    color: #333333;
}

.stSidebar .stRadio > div > label[data-checked="true"] > div:last-child {
    font-weight: 700;
    color: #1976d2;
}

/* ラジオボタンの円形アイコンスタイル */
.stSidebar .stRadio > div > label > div:first-child {
    margin-right: 0.5rem;
}
</style>
""", unsafe_allow_html=True)

pages = {
    "データセット作成": upload,
    "誤差率マトリクス分析": matrix,
    "誤差率散布図分析": scatter,
    "月次推移比較": monthly_trend
}

# 4つのセクションを縦並びリストで表示（Streamlit標準機能使用）
selected_page = st.sidebar.radio(
    "セクション選択:",
    list(pages.keys()),
    key="page_navigation"
)

# データ状態表示
if st.session_state.data is not None:
    st.sidebar.success(f"✅ データ読み込み済み ({len(st.session_state.data)}件)")
else:
    st.sidebar.markdown("""
    <div style="
        background: #e8f4fd;
        color: #1976d2;
        padding: 0.8rem;
        border-radius: 8px;
        margin-bottom: 1rem;
        font-size: 0.9rem;
        line-height: 1.6;
    ">
        データセット作成後、「セクション選択」から必要なメニューを選び、分析を進めてください。
    </div>
    """, unsafe_allow_html=True)

# 操作ガイド
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
st.markdown(FOOTER_HTML, unsafe_allow_html=True) 