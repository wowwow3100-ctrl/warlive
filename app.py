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
    }
    a:hover {
        text-decoration: underline !important;
    }
    @keyframes blinker {
        50% { opacity: 0; }
    }
    </style>
""", unsafe_allow_html=True)

st.title("🔴 全球戰情即時監控面板 (伊朗戰區特化版)")
st.markdown(f"<span class='live-status'>● LIVE </span> 即時連線中 | 台灣時間: {current_datetime_str} (數據每分鐘同步更新)", unsafe_allow_html=True)
st.markdown("---")

# --- 2. 實時抓取真實全球新聞 (加入連結抓取) ---
@st.cache_data(ttl=60)
def fetch_real_news():
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
            
            for item in root.findall('.//item')[:5]: 
                title = item.find('title').text
                pub_date = item.find('pubDate').text
                
                # 新增：抓取新聞超連結
                link_node = item.find('link')
                news_link = link_node.text if link_node is not None else "#"
                
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
                    "link": news_link, # 儲存連結
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
    'Intensity': [100, 95, 80, 85, 75, 85 if taiwan_is_hot else 30, 80 if taiwan_is_hot else 20] 
}
df_countries = pd.DataFrame(country_data)

# --- 4. 核心版面規劃：左邊滾動事件，右邊聚焦地圖 ---
col_left, col_right = st.columns([1.3, 2.7])

# 【左側版面】：實時戰報與歷史回顧
with col_left:
    st.subheader("📰 真實國際戰報") # 移除了「滾動」兩個字
    
    with st.container(height=450, border=True):
        if not real_events:
            st.warning("目前無法連線至情報伺服器。")
        else:
            for ev in real_events:
                # 新增：將文字轉化為 Markdown 超連結格式 [標題](網址)
                msg_with_link = f"[{ev['msg']}]({ev['link']})"
                
                content = f"📅 **{ev['time']}** | 📡 {ev['src']}\n\n**{msg_with_link}**"
                if "印太" in ev['src']:
                    if "解放軍" in ev['msg'] or "軍演" in ev['msg']:
                        st.error(content, icon="🚨")
                    else:
                        st.warning(content, icon="🟠")
                else:
                    st.error(content, icon="💥")
    
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

# --- 4. 底部 Live 影像區塊 (四種嵌入技術測試) ---
st.subheader("🎥 戰區 24H 現場監視畫面 (多訊號源語法測試區)")
st.info("💡 阿吉幫你準備了 4 種不同的影像嵌入底層技術，請確認一下「第幾個」畫面有成功出現（就算要按播放鍵也沒關係），確認後跟我說，我們就把壞掉的刪掉！")

v_col1, v_col2 = st.columns(2)
v_col3, v_col4 = st.columns(2)

with v_col1:
    st.markdown("##### 測試 1. 純 HTML Iframe (NASA)")
    st.caption("使用最底層的 HTML 標籤強制嵌入。")
    components.html(
        """<iframe width="100%" height="250" src="https://www.youtube.com/embed/xRPjKQtRXR8?autoplay=1&mute=1" frameborder="0" allowfullscreen></iframe>""",
        height=260
    )

with v_col2:
    st.markdown("##### 測試 2. Streamlit 原生 Iframe (TVBS)")
    st.caption("呼叫 Streamlit 內建的 components.iframe 函數。")
    components.iframe("https://www.youtube.com/embed/2mCSYvcfhtc?autoplay=1&mute=1", height=250)

with v_col3:
    st.markdown("##### 測試 3. Streamlit 原生 st.video (半島台)")
    st.caption("也就是上次失敗的方法，當作對照組。")
    st.video("https://www.youtube.com/watch?v=bByGQxsKWps")

with v_col4:
    st.markdown("##### 測試 4. Twitch 官方語法 (Agenda-Free TV)")
    st.caption("針對 Twitch 設計的專屬網域解除限制語法。")
    components.html(
        """<iframe src="https://player.twitch.tv/?channel=agenda_free_tv&parent=share.streamlit.io&parent=localhost&muted=true" frameborder="0" allowfullscreen="true" scrolling="no" height="250" width="100%"></iframe>""",
        height=260
    )
