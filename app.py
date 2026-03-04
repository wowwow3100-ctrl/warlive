import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import streamlit.components.v1 as components
from datetime import datetime
import random

# --- 1. 頁面與全域設定 ---
st.set_page_config(
    page_title="全球戰情即時監控面板",
    page_icon="🌍",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# 取得現在時間與日期，模擬即時串流
current_datetime = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

# 隱藏預設選單，強制暗黑風格，並加入「每 60 秒自動刷新」的 Meta 標籤
st.markdown("""
    <meta http-equiv="refresh" content="60">
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .stApp {
        background-color: #0d1117;
        color: #c9d1d9;
    }
    .st-emotion-cache-1v0mbdj {
        border: 1px solid #30363d;
        border-radius: 8px;
        padding: 10px;
        background-color: #161b22;
    }
    .live-status {
        color: #ff4444;
        font-weight: bold;
        animation: blinker 1.5s linear infinite;
    }
    @keyframes blinker {
        50% { opacity: 0; }
    }
    </style>
""", unsafe_allow_html=True)

st.title("🔴 全球戰情即時監控面板 (OSINT Dashboard)")
st.markdown(f"<span class='live-status'>● LIVE </span> 即時連線中 | 最後更新時間: {current_datetime} (系統每 60 秒自動更新)", unsafe_allow_html=True)
st.markdown("---")

# --- 2. 準備地圖資料 ---
# 國家衝突熱度 (底圖顏色)
country_data = {
    'Country': ['Ukraine', 'Iran', 'Sudan', 'Myanmar', 'Israel', 'Syria', 'Yemen', 'Russia'],
    'ISO': ['UKR', 'IRN', 'SDN', 'MMR', 'ISR', 'SYR', 'YEM', 'RUS'],
    'Status': ['全面戰爭', '高度緊張', '內戰', '內戰', '區域衝突', '區域衝突', '區域衝突', '戰爭'],
    'Intensity': [100, 85, 90, 80, 95, 70, 75, 50] 
}
df_countries = pd.DataFrame(country_data)

# 武裝力量與突發戰火座標 (圖示打點)
poi_data = {
    'lat': [33.5, 45.0, 18.0, 31.5, 48.0, 23.5, 13.0],
    'lon': [33.0, 36.0, 62.0, 34.5, 37.5, 119.5, 43.0],
    'icon': ['🚢', '✈️', '🚢', '💥', '💥', '🚢', '✈️'],
    'desc': [
        '美軍航母打擊群 (地中海)', 
        '北約偵察機巡邏 (黑海)', 
        '不明艦隊集結 (阿拉伯海)', 
        '[警報] 耶路撒冷外圍突發砲擊', 
        '[警報] 烏東防線遭突破起火',
        '太平洋艦隊巡航 (台灣海峽)',
        '無人機群升空 (紅海)'
    ],
    'size': [26, 26, 26, 32, 32, 26, 26] # 爆炸圖示稍微放大
}
df_pois = pd.DataFrame(poi_data)

# --- 3. 核心版面規劃：左邊事件，右邊地圖 ---
col_left, col_right = st.columns([1.2, 2.8])

# 【左側版面】：實時戰報與風險指數
with col_left:
    st.subheader("📰 實時滾動戰報")
    
    # 每個事件都加上完整的日期與時間
    st.error(f"📅 **{current_datetime}**\n\n🔴 **烏克蘭 (UKR):** 烏東防線發生劇烈爆炸，偵測到高強度火砲訊號。")
    st.warning(f"📅 **{current_datetime}**\n\n🟠 **耶路撒冷 (ISR):** 防空警報大響，啟動鐵穹攔截系統。")
    st.info(f"📅 **{current_datetime}**\n\n🔵 **太平洋區:** 衛星追蹤到航母打擊群變更航向。")
    st.error(f"📅 **{current_datetime}**\n\n🔴 **蘇丹 (SDN):** 首都圈通訊再次全面中斷。")
    st.warning(f"📅 **{current_datetime}**\n\n🟠 **紅海海域:** 偵測到不明無人機群正在接近商船航道。")
    
    st.markdown("---")
    st.subheader("⚠️ 國家不穩定風險")
    # 模擬數值隨機微幅跳動
    st.metric(label="🇮🇷 伊朗風險指數", value=f"{85 + random.randint(-1, 2)} / 100", delta="升級中", delta_color="inverse")
    st.metric(label="🇺🇦 烏克蘭風險指數", value=f"{98 + random.randint(-1, 1)} / 100", delta="極高", delta_color="inverse")
    st.metric(label="🇲🇲 緬甸風險指數", value=f"{80 + random.randint(-2, 2)} / 100", delta="波動中", delta_color="off")

# 【右側版面】：動態戰情地圖
with col_right:
    # 繪製多圖層互動式地圖 (Plotly Graph Objects)
    fig = go.Figure()

    # 第一層：國家區域上色
    fig.add_trace(go.Choropleth(
        locations=df_countries['ISO'],
        z=df_countries['Intensity'],
        colorscale=[(0, "#2c0000"), (1, "#ff0000")],
        showscale=False,
        hovertext=df_countries['Country'] + ": " + df_countries['Status'],
        hoverinfo="text",
        marker_line_color="#30363d",
        marker_line_width=0.5
    ))

    # 第二層：部隊與戰火圖示打點
    fig.add_trace(go.Scattergeo(
        lon=df_pois['lon'],
        lat=df_pois['lat'],
        text=df_pois['icon'],
        mode='text',
        textfont=dict(size=df_pois['size']),
        hoverinfo='text',
        hovertext=df_pois['desc']
    ))

    # 調整地圖外觀，打造「暗黑科技軍事風」
    fig.update_geos(
        showcountries=True, countrycolor="#30363d",
        showcoastlines=True, coastlinecolor="#30363d", 
        showland=True, landcolor="#161b22",
        showocean=True, oceancolor="#0d1117",
        showlakes=True, lakecolor="#0d1117",
        bgcolor="#0d1117",
        projection_type="mercator"
    )

    fig.update_layout(
        margin={"r":0,"t":0,"l":0,"b":0},
        paper_bgcolor="#0d1117",
        plot_bgcolor="#0d1117",
        height=750, # 配合左側戰報，將地圖高度拉高
        showlegend=False
    )

    st.plotly_chart(fig, use_container_width=True)

st.markdown("---")

# --- 4. 底部 Live 影像區塊 ---
st.subheader("🎥 戰區 24H 現場監視畫面")
vid_col1, vid_col2 = st.columns(2)

with vid_col1:
    st.markdown("##### 📍 中東戰區 (半島電視台)")
    components.html(
        """<iframe width="100%" height="280" src="https://www.youtube.com/embed/live_stream?channel=UCNye-wNBqGLPEZ4yYcgZ1Gg&autoplay=1&mute=1" frameborder="0" allowfullscreen></iframe>""",
        height=290
    )

with vid_col2:
    st.markdown("##### 📍 歐洲戰區 (天空新聞)")
    components.html(
        """<iframe width="100%" height="280" src="https://www.youtube.com/embed/live_stream?channel=UCoMdktPbSTixAyNGr4S4A&autoplay=1&mute=1" frameborder="0" allowfullscreen></iframe>""",
        height=290
    )
