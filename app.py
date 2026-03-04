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
import json

# 💡 匯入必要的元件庫
import streamlit.components.v1 as components 

# --- 1. 頁面與全域設定 ---
st.set_page_config(
    page_title="全球戰情即時監控-旺來",
    page_icon="🌍",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# 建立台灣時區 (UTC+8)
tz_tw = timezone(timedelta(hours=8))
now = datetime.now(tz_tw)
current_datetime_str = now.strftime("%Y-%m-%d %H:%M:%S")

# 隱藏預設選單，強制暗黑風格，加入 60 秒自動刷新
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
    /* 讓超連結在暗色背景下更清楚，且沒有底線 */
    a {
        color: #58a6ff !important;
        text-decoration: none !important;
        font-size: 16px;
        font-weight: bold;
    }
    a:hover {
        text-decoration: underline !important;
    }
    .original-text {
        font-size: 12px;
        color: #8b949e;
        margin-top: -10px;
        margin-bottom: 10px;
    }
    @keyframes blinker {
        50% { opacity: 0; }
    }
    </style>
""", unsafe_allow_html=True)

st.title("🔴 全球戰情即時監控-旺來")
st.markdown(f"<span class='live-status'>● LIVE </span> 即時連線中 | 台灣時間: {current_datetime_str} (數據每分鐘同步更新)", unsafe_allow_html=True)
st.markdown("---")

# --- 2. 實時抓取國外新聞與即時翻譯 ---

# 輕量級即時翻譯函數 (使用 Google Translate 免費介面)
def translate_to_tw(text):
    try:
        encoded_text = urllib.parse.quote(text)
        url = f"https://translate.googleapis.com/translate_a/single?client=gtx&sl=auto&tl=zh-TW&dt=t&q={encoded_text}"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        response = urllib.request.urlopen(req, timeout=3)
        data = json.loads(response.read().decode('utf-8'))
        translated_text = "".join([sentence[0] for sentence in data[0]])
        return translated_text
    except:
        return text # 若翻譯失敗則回傳原文

@st.cache_data(ttl=60)
def fetch_real_news():
    # 改為抓取純國外權威媒體的英文 RSS 戰報
    urls = [
        ("半島電視台 (Al Jazeera)", "https://www.aljazeera.com/xml/rss/all.xml"),
        ("BBC 國際新聞 (BBC World)", "http://feeds.bbci.co.uk/news/world/rss.xml")
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
            
            for item in root.findall('.//item')[:4]: # 每個外媒抓取最新 4 條
                title_en = item.find('title').text
                pub_date = item.find('pubDate').text
                
                link_node = item.find('link')
                news_link = link_node.text if link_node is not None else "#"
                
                # 呼叫翻譯函數，將英文標題轉為繁體中文
                title_tw = translate_to_tw(title_en)

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
                    "msg_tw": title_tw, 
                    "msg_en": title_en,
                    "link": news_link,
                    "dt": dt_tw
                })
        except Exception as e:
            continue
            
    news_list.sort(key=lambda x: x.get('dt', datetime.now(tz_tw)), reverse=True)
    return news_list

real_events = fetch_real_news()

# 根據新聞內容，動態計算台海緊張程度 (檢查中英文關鍵字)
taiwan_tension_score = sum(1 for ev in real_events if "台灣" in ev['msg_tw'] or "中國" in ev['msg_tw'] or "Taiwan" in ev['msg_en'] or "China" in ev['msg_en'])
taiwan_is_hot = taiwan_tension_score > 0

# --- 3. 國家衝突熱度資料庫 ---
country_data = {
    'Country': ['伊朗', '以色列', '敘利亞', '烏克蘭', '俄羅斯', '中國', '台灣'],
    'ISO': ['IRN', 'ISR', 'SYR', 'UKR', 'RUS', 'CHN', 'TWN'],
    'Status': ['高度戰爭警戒', '全面衝突', '區域衝突', '全面戰爭', '戰爭', '軍事演習' if taiwan_is_hot else '常態警戒', '防空攔截' if taiwan_is_hot else '常態防禦'],
    'Intensity': [100, 95, 80, 85, 75, 85 if taiwan_is_hot else 30, 80 if taiwan_is_hot else 20] 
}
df_countries = pd.DataFrame(country_data)

# --- 4. 核心版面規劃：左邊事件，右邊聚焦地圖 ---
col_left, col_right = st.columns([1.4, 2.6])

# 【左側版面】：實時戰報與歷史回顧
with col_left:
    st.subheader("📰 真實國際戰報 (外電即時翻譯)") 
    
    with st.container(height=450, border=True):
        if not real_events:
            st.warning("目前無法連線至外電情報伺服器。")
        else:
            for ev in real_events:
                # 建立可點擊的中文超連結
                msg_with_link = f"[{ev['msg_tw']}]({ev['link']})"
                
                # 排版：時間 + 來源 + 翻譯標籤 -> 中文超連結 -> 英文原文
                content = f"📅 **{ev['time']}** | 📡 {ev['src']} `[🤖 翻譯]`\n\n{msg_with_link}\n\n<div class='original-text'>原文: {ev['msg_en']}</div>"
                
                # 簡單以來源顏色區分
                if "半島" in ev['src']:
                    st.warning(content, icon="🟠")
                else:
                    st.info(content, icon="🔵")
    
    st.markdown("---")
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

    hotspots = [
        {"lon": 51.38, "lat": 35.68, "icon": "💥", "loc": "伊朗 (德黑蘭)", "msg": "革命衛隊指揮中心警戒"},
        {"lon": 51.66, "lat": 32.65, "icon": "🚀", "loc": "伊朗 (伊斯法罕)", "msg": "核設施/飛彈基地防空啟動"},
        {"lon": 34.78, "lat": 32.08, "icon": "🛡️", "loc": "以色列 (特拉維夫)", "msg": "鐵穹系統全面攔截準備"},
        {"lon": 43.00, "lat": 13.00, "icon": "🚢", "loc": "紅海海域", "msg": "美軍航母戰鬥群部署"}
    ]
    
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

    fig.update_geos(
        center=dict(lon=53.68, lat=32.42),
        projection_scale=2.8,
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

# --- 4. 底部 Live 影像區塊 ---
st.subheader("🎥 戰區 24H 現場監視畫面 (Ganjing World 串流)")
st.info("💡 系統已切換至無阻擋的 Ganjing World 串流源，若有其他頻道的來源，請貼入下方欄位！")

v_col1, v_col2 = st.columns(2)

with v_col1:
    st.markdown("##### 📍 全球戰情觀測頻道 1")
    url1 = st.text_input("更換頻道 1 (Embed 網址)：", value="https://www.ganjingworld.com/embed/SH048456380000", key="vid1")
    if url1:
        components.html(
            f'<iframe width="100%" height="280" src="{url1}" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope;" allowfullscreen></iframe>',
            height=290
        )

with v_col2:
    st.markdown("##### 📍 全球戰情觀測頻道 2")
    url2 = st.text_input("更換頻道 2 (Embed 網址)：", value="https://www.ganjingworld.com/embed/SH048456380000", key="vid2")
    if url2:
        components.html(
            f'<iframe width="100%" height="280" src="{url2}" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope;" allowfullscreen></iframe>',
            height=290
        )
