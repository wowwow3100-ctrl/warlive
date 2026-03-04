import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta, timezone
import random
import urllib.request
import xml.etree.ElementTree as ET
import ssl
from email.utils import parsedate_to_datetime

# --- 1. 頁面與全域設定 ---
st.set_page_config(
    page_title="全球戰情即時監控面板",
    page_icon="🌍",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# 建立台灣時區 (UTC+8)
tz_tw = timezone(timedelta(hours=8))
now = datetime.now(tz_tw)
current_datetime_str = now.strftime("%Y-%m-%d %H:%M:%S")

# 利用秒數做動態切換 (模擬動畫效果)
is_pulse = (now.second % 10) < 5 

# 隱藏預設選單，強制暗黑風格，並加入「每 5 秒自動刷新」的 Meta 標籤
st.markdown("""
    <meta http-equiv="refresh" content="5">
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
        animation: blinker 1s linear infinite;
    }
    @keyframes blinker {
        50% { opacity: 0; }
    }
    </style>
""", unsafe_allow_html=True)

st.title("🔴 全球戰情即時監控面板 (OSINT Dashboard)")
st.markdown(f"<span class='live-status'>● LIVE </span> 即時連線中 | 台灣時間: {current_datetime_str} (每 5 秒更新畫面，新聞每分鐘同步)", unsafe_allow_html=True)
st.markdown("---")

# --- 2. 實時抓取真實全球新聞 (RSS Feed) ---
@st.cache_data(ttl=60) # 每 60 秒重新去抓一次真實新聞
def fetch_real_news():
    urls = [
        ("BBC World", "http://feeds.bbci.co.uk/news/world/rss.xml"),
        ("半島電視台", "https://www.aljazeera.com/xml/rss/all.xml")
    ]
    news_list = []
    
    # 忽略 SSL 憑證驗證，避免雲端環境報錯
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE

    for src_name, url in urls:
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            response = urllib.request.urlopen(req, context=ctx, timeout=5)
            root = ET.fromstring(response.read())
            
            for item in root.findall('.//item')[:4]: # 每個來源取最新的4條
                title = item.find('title').text
                pub_date = item.find('pubDate').text
                
                # 將新聞時間轉換為台灣時間
                try:
                    dt = parsedate_to_datetime(pub_date)
                    dt_tw = dt.astimezone(tz_tw)
                    time_str = dt_tw.strftime("%Y-%m-%d %H:%M:%S")
                except:
                    dt_tw = datetime.now(tz_tw)
                    time_str = pub_date
                    
                news_list.append({
                    "time": time_str, 
                    "src": src_name, 
                    "msg": title, 
                    "dt": dt_tw
                })
        except Exception as e:
            continue
            
    # 依照時間排序，確保最新新聞在最上面
    news_list.sort(key=lambda x: x.get('dt', datetime.now(tz_tw)), reverse=True)
    
    # 如果網路不通，提供備用情報
    if not news_list:
        return [{"time": current_datetime_str, "src": "系統回報", "msg": "目前無法連線至國際新聞伺服器，啟動離線監控模式。"}]
        
    return news_list[:6] # 只回傳最新的 6 條新聞

# 取得真實新聞資料
real_events = fetch_real_news()

# 國家衝突熱度 (底圖顏色)
country_data = {
    'Country': ['烏克蘭', '伊朗', '蘇丹', '緬甸', '以色列', '敘利亞', '葉門', '俄羅斯'],
    'ISO': ['UKR', 'IRN', 'SDN', 'MMR', 'ISR', 'SYR', 'YEM', 'RUS'],
    'Status': ['全面戰爭', '高度緊張', '內戰', '內戰', '區域衝突', '區域衝突', '區域衝突', '戰爭'],
    'Intensity': [100, 85, 90, 80, 95, 70, 75, 50] 
}
df_countries = pd.DataFrame(country_data)

# --- 3. 核心版面規劃：左邊事件，右邊地圖 ---
col_left, col_right = st.columns([1.5, 2.5])

# 【左側版面】：實時戰報與風險指數
with col_left:
    st.subheader("📰 真實國際滾動戰報")
    
    # 動態渲染剛剛抓回來的真實新聞
    for ev in real_events:
        content = f"""📅 **{ev['time']}** | 📡 來源: {ev['src']} `{['🤖 自動抓取']}`\n\n**頭條:** {ev['msg']}"""
        # 用不同顏色區分來源
        if "BBC" in ev['src']:
            st.error(content, icon="🔴")
        elif "半島" in ev['src']:
            st.warning(content, icon="🟠")
        else:
            st.info(content, icon="🔵")
    
    st.markdown("---")
    st.subheader("⚠️ 國家不穩定風險")
    st.metric(label="🇮🇷 伊朗風險指數", value=f"{85 + random.randint(-1, 2)} / 100", delta="升級中", delta_color="inverse")
    st.metric(label="🇺🇦 烏克蘭風險指數", value=f"{98 + random.randint(-1, 1)} / 100", delta="極高", delta_color="inverse")

# 【右側版面】：動態戰情地圖
with col_right:
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

    # 第二層：攻打動畫軌跡
    fig.add_trace(go.Scattergeo(
        lon=[40.0, 37.5], lat=[50.0, 48.0],
        mode='lines',
        line=dict(width=3, color='orange', dash='dot' if is_pulse else 'solid'),
        hoverinfo='skip'
    ))
    fig.add_trace(go.Scattergeo(
        lon=[44.0, 43.0], lat=[15.0, 13.0],
        mode='lines',
        line=dict(width=2, color='red', dash='dash' if is_pulse else 'solid'),
        hoverinfo='skip'
    ))

    # 第三層：熱點圖示 (結合閃爍特效)
    hotspots = [
        {"lon": 37.5, "lat": 48.0, "icon": "💥", "loc": "烏克蘭東部", "msg": "持續交火區域"},
        {"lon": 34.5, "lat": 31.5, "icon": "💥", "loc": "中東地區", "msg": "防空警戒熱區"},
        {"lon": 43.0, "lat": 13.0, "icon": "🚀", "loc": "紅海海域", "msg": "無人機攻擊熱區"},
        {"lon": 119.5, "lat": 23.5, "icon": "🚢", "loc": "太平洋艦隊", "msg": "常態巡航佈署"}
    ]
    
    lats = [h["lat"] for h in hotspots]
    lons = [h["lon"] for h in hotspots]
    icons = [h["icon"] for h in hotspots]
    hover_texts = [f"<b>{h['loc']}</b><br>⚠️ {h['msg']}" for h in hotspots]
    sizes = [38 if (h["icon"] == "💥" and is_pulse) else 26 for h in hotspots]

    fig.add_trace(go.Scattergeo(
        lon=lons, lat=lats,
        text=icons, mode='text',
        textfont=dict(size=sizes),
        hoverinfo='text', hovertext=hover_texts
    ))

    # 調整地圖外觀
    fig.update_geos(
        showcountries=True, countrycolor="#30363d",
        showcoastlines=True, coastlinecolor="#30363d", 
        showland=True, landcolor="#161b22",
        showocean=True, oceancolor="#0d1117",
        showlakes=True, lakecolor="#0d1117",
        bgcolor="#0d1117", projection_type="mercator"
    )

    fig.update_layout(
        margin={"r":0,"t":0,"l":0,"b":0},
        paper_bgcolor="#0d1117", plot_bgcolor="#0d1117",
        height=650, showlegend=False
    )

    st.plotly_chart(fig, use_container_width=True)

st.markdown("---")

# --- 4. 底部 Live 影像區塊 ---
st.subheader("🎥 戰區 24H 現場監視畫面 (自動連線)")
vid_col1, vid_col2 = st.columns(2)

with vid_col1:
    st.markdown("##### 📍 國際新聞戰情中心 (DW News Live)")
    # 改用 Streamlit 原生影片元件，並使用極穩定的 DW 德國之聲直播網址
    st.video("https://www.youtube.com/watch?v=V9KZGs1MtP4")

with vid_col2:
    st.markdown("##### 🛰️ 全球軌道衛星監視 (NASA ISS Live)")
    # 改用 Streamlit 原生影片元件，使用 NASA 官方直播網址
    st.video("https://www.youtube.com/watch?v=xRPjKQtRXR8")
