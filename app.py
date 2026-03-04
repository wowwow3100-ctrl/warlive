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

# 隱藏預設選單，強制暗黑風格，加入自動刷新
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
    .hp-bar-container {
        width: 100%;
        background-color: #30363d;
        border-radius: 8px;
        height: 20px;
        margin-top: 5px;
        overflow: hidden;
    }
    .hp-bar-fill {
        height: 100%;
        transition: width 0.5s ease-in-out;
    }
    @keyframes blinker {
        50% { opacity: 0; }
    }
    </style>
""", unsafe_allow_html=True)

# --- 版面模式切換 (頂部) ---
col_title, col_toggle = st.columns([3, 1])
with col_title:
    st.title("🔴 全球戰情即時監控-旺來")
with col_toggle:
    # 新增手機模式/電腦模式切換按鈕
    mode = st.radio("版面檢視模式", ["💻 電腦模式 (詳細)", "📱 手機模式 (精簡)"], horizontal=True)
    is_mobile = "手機" in mode

st.markdown(f"<span class='live-status'>● LIVE </span> 即時連線中 | 台灣時間: {current_datetime_str}", unsafe_allow_html=True)
st.markdown("---")

# --- 2. 實時抓取國外新聞與即時翻譯 ---
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
        return text 

@st.cache_data(ttl=60)
def fetch_real_news():
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
            
            for item in root.findall('.//item')[:4]:
                title_en = item.find('title').text
                pub_date = item.find('pubDate').text
                link_node = item.find('link')
                news_link = link_node.text if link_node is not None else "#"
                title_tw = translate_to_tw(title_en)

                try:
                    dt = parsedate_to_datetime(pub_date)
                    dt_tw = dt.astimezone(tz_tw)
                    time_str = dt_tw.strftime("%Y-%m-%d %H:%M:%S")
                except:
                    dt_tw = datetime.now(tz_tw)
                    time_str = pub_date
                    
                news_list.append({
                    "time": time_str, "src": src_name, 
                    "msg_tw": title_tw, "msg_en": title_en,
                    "link": news_link, "dt": dt_tw
                })
        except Exception as e:
            continue
            
    news_list.sort(key=lambda x: x.get('dt', datetime.now(tz_tw)), reverse=True)
    return news_list

real_events = fetch_real_news()

# --- 動態情報分析 (智能圖示判斷) ---
taiwan_tension_score = 0
iran_damage = 0
dynamic_map_hotspots = []

# 建立智能圖示判斷邏輯
def get_event_icon(msg, en_msg):
    msg_lower = msg.lower() + en_msg.lower()
    if any(k in msg_lower for k in ["攻擊", "爆炸", "飛彈", "轟炸", "死", "擊落", "戰火", "attack", "strike", "missile", "blast", "bomb"]):
        return "💥"
    if any(k in msg_lower for k in ["軍演", "警告", "制裁", "越界", "緊張", "攔截", "warn", "sanction", "drill", "tension"]):
        return "🚨"
    return "📍" # 一般新聞用定位點

for ev in real_events:
    msg = ev['msg_tw']
    en_msg = ev['msg_en']
    icon_to_use = get_event_icon(msg, en_msg)
    
    # 判斷台海熱度
    if any(k in msg for k in ["台灣", "中國"]) or any(k in en_msg for k in ["Taiwan", "China"]):
        taiwan_tension_score += 1
        # 手機版縮小座標散佈範圍，避免擠在一起
        scatter = 0.5 if is_mobile else 1.5 
        dynamic_map_hotspots.append({"lon": 119.5 + random.uniform(-scatter, scatter), "lat": 23.5 + random.uniform(-scatter, scatter), "icon": icon_to_use, "loc": "新聞連動：台海", "msg": msg})
    
    # 判斷伊朗受損/警戒熱度
    if any(k in msg for k in ["伊朗", "德黑蘭", "Iran", "Tehran"]):
        if icon_to_use == "💥":
            iran_damage += 800
        else:
            iran_damage += 200
        scatter = 1.0 if is_mobile else 3.0
        dynamic_map_hotspots.append({"lon": 53.68 + random.uniform(-scatter, scatter), "lat": 32.42 + random.uniform(-scatter, scatter), "icon": icon_to_use, "loc": "新聞連動：伊朗", "msg": msg})

    # 判斷以色列/中東
    elif any(k in msg for k in ["以色列", "加薩", "黎巴嫩", "Israel", "Gaza", "Lebanon"]):
        dynamic_map_hotspots.append({"lon": 34.78 + random.uniform(-0.5, 0.5), "lat": 31.5 + random.uniform(-0.5, 0.5), "icon": icon_to_use, "loc": "新聞連動：中東", "msg": msg})
        
    # 判斷俄烏
    elif any(k in msg for k in ["烏克蘭", "俄羅斯", "基輔", "Ukraine", "Russia"]):
        scatter = 1.5 if is_mobile else 4.0
        dynamic_map_hotspots.append({"lon": 34.0 + random.uniform(-scatter, scatter), "lat": 49.0 + random.uniform(-scatter, scatter), "icon": icon_to_use, "loc": "新聞連動：俄烏", "msg": msg})

taiwan_is_hot = taiwan_tension_score > 0

# 計算伊朗 HP
iran_max_hp = 10000
iran_current_hp = max(0, iran_max_hp - 1500 - iran_damage - random.randint(10, 150))
hp_percentage = (iran_current_hp / iran_max_hp) * 100
hp_color = "#2ea043" if hp_percentage > 60 else ("#d29922" if hp_percentage > 30 else "#f85149")

# --- 3. 國家衝突熱度資料庫 ---
country_data = {
    'Country': ['伊朗', '以色列', '敘利亞', '烏克蘭', '俄羅斯', '中國', '台灣'],
    'ISO': ['IRN', 'ISR', 'SYR', 'UKR', 'RUS', 'CHN', 'TWN'],
    'Status': ['高度戰爭警戒', '全面衝突', '區域衝突', '全面戰爭', '戰爭', '軍事演習' if taiwan_is_hot else '常態警戒', '防空攔截' if taiwan_is_hot else '常態防禦'],
    'Intensity': [100, 95, 80, 85, 75, 85 if taiwan_is_hot else 30, 80 if taiwan_is_hot else 20] 
}
df_countries = pd.DataFrame(country_data)

# --- 4. 模組化渲染函數 (支援手機與電腦版不同佈局) ---
def render_news_and_stats():
    st.subheader("📰 真實國際戰報") 
    
    # 手機版高度降低，避免佔用全螢幕
    news_height = 250 if is_mobile else 400
    with st.container(height=news_height, border=True):
        if not real_events:
            st.warning("目前無法連線至外電情報伺服器。")
        else:
            for ev in real_events:
                msg_with_link = f"[{ev['msg_tw']}]({ev['link']})"
                
                if is_mobile:
                    # 手機版：極度精簡，只留時間與標題
                    st.markdown(f"**{ev['time'][5:16]}** | {msg_with_link}")
                    st.divider()
                else:
                    # 電腦版：詳細資訊與原文
                    content = f"📅 **{ev['time']}** | 📡 {ev['src']} `[🤖 翻譯]`\n\n{msg_with_link}\n\n<div class='original-text'>原文: {ev['msg_en']}</div>"
                    if "半島" in ev['src']:
                        st.warning(content, icon="🟠")
                    else:
                        st.info(content, icon="🔵")
    
    st.markdown("---")
    
    st.subheader("📈 恐慌與戰略物資指數")
    i1, i2, i3 = st.columns(3)
    with i1: st.metric("VIX 指數", f"{22.5 + random.uniform(-0.5, 1.8):.2f}", f"+{random.uniform(0.1, 1.5):.2f}%", delta_color="inverse")
    with i2: st.metric("布蘭特原油", f"${88.4 + random.uniform(-0.5, 1.2):.2f}", f"+{random.uniform(0.1, 0.8):.2f}%")
    with i3: st.metric("黃金 (盎司)", f"${2150.5 + random.uniform(-5, 15):.1f}", f"+{random.uniform(2.0, 8.0):.1f}")
        
    st.markdown("---")

    st.subheader("🛡️ 伊朗政權穩定值 (HP)")
    st.markdown(f"**當前數值: {iran_current_hp} / {iran_max_hp}** ({hp_percentage:.1f}%)")
    st.markdown(f"""
        <div class="hp-bar-container">
            <div class="hp-bar-fill" style="width: {hp_percentage}%; background-color: {hp_color};"></div>
        </div>
        <span style="font-size:12px; color:#8b949e;">*依新聞負面關鍵字(攻擊、制裁等)動態扣減</span>
    """, unsafe_allow_html=True)

def render_map():
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

    base_hotspots = [
        {"lon": 51.38, "lat": 35.68, "icon": "🎯", "loc": "伊朗 (德黑蘭)", "msg": "高價值戰略目標區"},
        {"lon": 34.78, "lat": 32.08, "icon": "🛡️", "loc": "以色列 (特拉維夫)", "msg": "鐵穹系統全面攔截準備"},
        {"lon": 43.00, "lat": 13.00, "icon": "🚢", "loc": "紅海海域", "msg": "美軍航母戰鬥群常態部署"}
    ]
    
    all_hotspots = base_hotspots + dynamic_map_hotspots

    lats = [h["lat"] for h in all_hotspots]
    lons = [h["lon"] for h in all_hotspots]
    icons = [h["icon"] for h in all_hotspots]
    hover_texts = [f"<b>{h['loc']}</b><br>⚠️ {h['msg']}" for h in all_hotspots]

    # 手機版縮小圖示，避免擠在一起
    base_icon_size = 18 if is_mobile else 26
    pulse_icon_size = 24 if is_mobile else 38

    is_pulse = (now.second % 10) < 5 
    sizes = [pulse_icon_size if (h["icon"] in ["💥", "🚨", "🚀"] and is_pulse) else base_icon_size for h in all_hotspots]

    fig.add_trace(go.Scattergeo(
        lon=lons, lat=lats,
        text=icons, mode='text',
        textfont=dict(size=sizes),
        hoverinfo='text', hovertext=hover_texts
    ))

    # 手機版地圖高度調低
    map_height = 400 if is_mobile else 730

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
        height=map_height, showlegend=False
    )

    st.plotly_chart(fig, use_container_width=True)

# 依據模式渲染版面
if is_mobile:
    # 手機版：強制上下垂直排列
    render_map() # 手機版通常地圖在上方比較直觀
    st.markdown("---")
    render_news_and_stats()
else:
    # 電腦版：左右分欄排列
    col_left, col_right = st.columns([1.5, 2.5])
    with col_left:
        render_news_and_stats()
    with col_right:
        render_map()

st.markdown("---")

# --- 5. 底部 Live 影像區塊 ---
# 修復 Ganjing 網址，自動轉換 /s/ 為 /embed/
def clean_ganjing_url(url):
    if "/s/" in url:
        base = url.split("?")[0] # 移除 ?t=... 等不必要的參數
        return base.replace("/s/", "/embed/")
    return url

st.subheader("🎥 戰區 24H 現場監視畫面 (Ganjing World)")

# 手機版畫面也採用單欄排列
if is_mobile:
    v_col1, v_col2 = st.container(), st.container()
else:
    v_col1, v_col2 = st.columns(2)

with v_col1:
    st.markdown("##### 📍 核心戰情觀測頻道 1")
    # 預設帶入你提供的影片 (已經自動轉換處理)
    url1 = st.text_input("頻道 1 (支援 Ganjing 連結)：", value="https://www.ganjingworld.com/embed/SH048456380000", key="vid1")
    if url1:
        embed_url = clean_ganjing_url(url1)
        components.html(
            f'<iframe width="100%" height="280" src="{embed_url}" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope;" allowfullscreen></iframe>',
            height=290
        )

with v_col2:
    st.markdown("##### 📍 輔助戰情觀測頻道 2")
    # 帶入你指定的分享連結 /s/oZkE9Q1V1N (系統會自動洗成 embed 格式)
    url2 = st.text_input("頻道 2 (支援 Ganjing 連結)：", value="https://www.ganjingworld.com/s/oZkE9Q1V1N", key="vid2")
    if url2:
        embed_url2 = clean_ganjing_url(url2)
        components.html(
            f'<iframe width="100%" height="280" src="{embed_url2}" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope;" allowfullscreen></iframe>',
            height=290
        )
