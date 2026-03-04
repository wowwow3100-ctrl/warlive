import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta, timezone
import random
import urllib.request
import urllib.parse
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

# 隱藏預設選單，強制暗黑風格，加入 60 秒自動刷新 (避免影片一直中斷)
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
    .history-card {
        background-color: #1c2128;
        border-left: 4px solid #444c56;
        padding: 10px;
        margin-bottom: 10px;
        border-radius: 4px;
        font-size: 14px;
    }
    @keyframes blinker {
        50% { opacity: 0; }
    }
    </style>
""", unsafe_allow_html=True)

st.title("🔴 全球戰情即時監控面板 (伊朗戰區特化版)")
st.markdown(f"<span class='live-status'>● LIVE </span> 即時連線中 | 台灣時間: {current_datetime_str} (數據每分鐘同步更新)", unsafe_allow_html=True)
st.markdown("---")

# --- 2. 實時抓取真實全球新聞 (聚焦伊朗與台海) ---
@st.cache_data(ttl=60)
def fetch_real_news():
    # 關鍵字特化：聚焦伊朗、中東，以及大陸的特殊動作
    q_iran = urllib.parse.quote("伊朗 OR 以色列 OR 飛彈 OR 中東")
    q_taiwan = urllib.parse.quote("台海 OR 解放軍 OR 中共軍演 OR 越界")
    
    urls = [
        ("中東/伊朗戰報", f"https://news.google.com/rss/search?q={q_iran}&hl=zh-TW&gl=TW&ceid=TW:zh-Hant"),
        ("印太/台海動態", f"https://news.google.com/rss/search?q={q_taiwan}&hl=zh-TW&gl=TW&ceid=TW:zh-Hant")
    ]
    news_list = []
    
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE

    for src_name, url in urls:
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            response = urllib.request.urlopen(req, context=ctx, timeout=5)
            root = ET.fromstring(response.read())
            
            for item in root.findall('.//item')[:5]: # 每個來源取最新的 5 條
                title = item.find('title').text
                pub_date = item.find('pubDate').text
                clean_title = title.split(' - ')[0] if ' - ' in title else title

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
                    "msg": clean_title, 
                    "dt": dt_tw
                })
        except Exception as e:
            continue
            
    news_list.sort(key=lambda x: x.get('dt', datetime.now(tz_tw)), reverse=True)
    return news_list

real_events = fetch_real_news()

# 根據新聞內容，動態計算台海緊張程度
taiwan_tension_score = sum(1 for ev in real_events if "解放軍" in ev['msg'] or "軍演" in ev['msg'] or "越界" in ev['msg'])
taiwan_is_hot = taiwan_tension_score > 0

# --- 3. 國家衝突熱度資料庫 ---
country_data = {
    'Country': ['伊朗', '以色列', '敘利亞', '烏克蘭', '俄羅斯', '中國', '台灣'],
    'ISO': ['IRN', 'ISR', 'SYR', 'UKR', 'RUS', 'CHN', 'TWN'],
    'Status': ['高度戰爭警戒', '全面衝突', '區域衝突', '全面戰爭', '戰爭', '軍事演習' if taiwan_is_hot else '常態警戒', '防空攔截' if taiwan_is_hot else '常態防禦'],
    # 伊朗設定為最高熱度，台灣與中國的熱度由新聞動態決定
    'Intensity': [100, 95, 80, 85, 75, 85 if taiwan_is_hot else 30, 80 if taiwan_is_hot else 20] 
}
df_countries = pd.DataFrame(country_data)

# --- 4. 核心版面規劃：左邊滾動事件，右邊聚焦地圖 ---
col_left, col_right = st.columns([1.3, 2.7])

# 【左側版面】：實時戰報與歷史回顧
with col_left:
    st.subheader("📰 真實國際滾動戰報")
    
    # 新增：使用 Streamlit 的卷軸容器 (Scrollable Container)，限制高度並可滾動
    with st.container(height=450, border=True):
        if not real_events:
            st.warning("目前無法連線至情報伺服器。")
        else:
            for ev in real_events:
                content = f"📅 **{ev['time']}** | 📡 {ev['src']}\n\n**{ev['msg']}**"
                if "印太" in ev['src']:
                    # 台海新聞若有敏感字眼，改用紅色警告
                    if "解放軍" in ev['msg'] or "軍演" in ev['msg']:
                        st.error(content, icon="🚨")
                    else:
                        st.warning(content, icon="🟠")
                else:
                    st.error(content, icon="💥")
    
    st.markdown("---")
    # 歷史回顧區塊
    st.subheader("📜 過去 30 天重大戰情回顧")
    with st.container(height=250, border=True):
        history_data = [
            {"date": "2026-03-01", "loc": "伊朗/以色列", "desc": "伊朗革命衛隊宣布進入最高戰備狀態，多處地下飛彈基地啟動。"},
            {"date": "2026-02-24", "loc": "紅海海域", "desc": "胡塞武裝發射反艦彈道飛彈，美英聯軍實施聯合防空攔截。"},
            {"date": "2026-02-18", "loc": "台海周邊", "desc": "中共解放軍進行海空聯合戰備警巡，數十架次軍機越過海峽中線。"},
            {"date": "2026-02-10", "loc": "烏克蘭", "desc": "俄烏戰爭屆滿四週年，雙方於烏東防線爆發新一波激烈砲擊。"}
        ]
        for h in history_data:
            st.markdown(f"""
            <div class="history-card">
                <span style="color:#ff7b72; font-weight:bold;">{h['date']} | 📍 {h['loc']}</span><br>
                {h['desc']}
            </div>
            """, unsafe_allow_html=True)

# 【右側版面】：動態戰情地圖 (聚焦伊朗)
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

    # 第三層：熱點圖示 (伊朗主戰場)
    hotspots = [
        {"lon": 51.38, "lat": 35.68, "icon": "💥", "loc": "伊朗 (德 শতকরা倫)", "msg": "革命衛隊指揮中心警戒"},
        {"lon": 51.66, "lat": 32.65, "icon": "🚀", "loc": "伊朗 (伊斯法罕)", "msg": "核設施/飛彈基地防空啟動"},
        {"lon": 34.78, "lat": 32.08, "icon": "🛡️", "loc": "以色列 (特拉維夫)", "msg": "鐵穹系統全面攔截準備"},
        {"lon": 43.00, "lat": 13.00, "icon": "🚢", "loc": "紅海海域", "msg": "美軍航母戰鬥群部署"}
    ]
    
    # 動態新增：如果新聞抓到大陸有動作，地圖上馬上新增台海熱點！
    if taiwan_is_hot:
        hotspots.append({"lon": 119.5, "lat": 23.5, "icon": "🚨", "loc": "台灣海峽", "msg": "偵測到異常活動：解放軍越界/演習新聞暴增"})

    lats = [h["lat"] for h in hotspots]
    lons = [h["lon"] for h in hotspots]
    icons = [h["icon"] for h in hotspots]
    hover_texts = [f"<b>{h['loc']}</b><br>⚠️ {h['msg']}" for h in hotspots]

    fig.add_trace(go.Scattergeo(
        lon=lons, lat=lats,
        text=icons, mode='text',
        textfont=dict(size=30),
        hoverinfo='text', hovertext=hover_texts
    ))

    # 調整地圖外觀，並將視角「強制聚焦」在伊朗與中東地區
    fig.update_geos(
        center=dict(lon=53.68, lat=32.42), # 經緯度中心點設定在伊朗
        projection_scale=2.8,              # 放大地圖倍率 (數值越大越近)
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
        height=730, showlegend=False
    )

    st.plotly_chart(fig, use_container_width=True)

st.markdown("---")

# --- 4. 底部 Live 影像區塊 (無阻擋 Twitch 串流) ---
st.subheader("🎥 戰區 24H 現場監視畫面 (Twitch 穩定串流)")
st.info("💡 提示：除了 YouTube，系統也支援 **Twitch** 實況台、**Vimeo** 或直連的 **.mp4** 網址。Twitch 通常不會阻擋外部網頁嵌入，強烈建議作為戰情室的主要訊號源！")

vid_col1, vid_col2 = st.columns(2)

with vid_col1:
    st.markdown("##### 📍 國際突發新聞戰情台 (Agenda-Free TV)")
    # 使用知名的 Twitch OSINT/突發新聞分析台
    custom_url_1 = st.text_input("更換頻道 1 網址：", value="https://www.twitch.tv/agenda_free_tv", key="vid1")
    if custom_url_1:
        st.video(custom_url_1)

with vid_col2:
    st.markdown("##### 📍 全球即時新聞聯播網 (LiveNowGlobal)")
    # 使用 Twitch 全球新聞實況台
    custom_url_2 = st.text_input("更換頻道 2 網址：", value="https://www.twitch.tv/livenowglobal", key="vid2")
    if custom_url_2:
        st.video(custom_url_2)
