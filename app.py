import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import streamlit.components.v1 as components
from datetime import datetime, timedelta
import random

# --- 1. 頁面與全域設定 ---
st.set_page_config(
    page_title="全球戰情即時監控面板",
    page_icon="🌍",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# 取得現在時間
now = datetime.now()
current_datetime_str = now.strftime("%Y-%m-%d %H:%M:%S")

# 利用當下時間的「秒數」來做動態切換 (模擬動畫效果)
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
    .translate-tag {
        background-color: #1f6feb;
        color: white;
        padding: 2px 6px;
        border-radius: 4px;
        font-size: 12px;
        margin-left: 8px;
    }
    @keyframes blinker {
        50% { opacity: 0; }
    }
    </style>
""", unsafe_allow_html=True)

st.title("🔴 全球戰情即時監控面板 (OSINT Dashboard)")
st.markdown(f"<span class='live-status'>● LIVE </span> 即時連線中 | 系統時間: {current_datetime_str} (每 5 秒自動更新)", unsafe_allow_html=True)
st.markdown("---")

# --- 2. 準備動態事件資料 (加入獨立時間、來源) ---
events = [
    {
        "loc_en": "Ukraine", "loc_tw": "烏克蘭",
        "time": now - timedelta(minutes=2, seconds=random.randint(10, 50)),
        "src": "路透社 (Reuters)", "type": "error", "icon": "💥",
        "lat": 48.0, "lon": 37.5,
        "msg": "烏東防線發生劇烈爆炸，偵測到高強度火砲訊號。"
    },
    {
        "loc_en": "Israel", "loc_tw": "以色列 (耶路撒冷)",
        "time": now - timedelta(minutes=14, seconds=random.randint(10, 50)),
        "src": "半島電視台 (Al Jazeera)", "type": "warning", "icon": "💥",
        "lat": 31.5, "lon": 34.5,
        "msg": "防空警報大響，啟動鐵穹系統攔截多枚火箭彈。"
    },
    {
        "loc_en": "Pacific", "loc_tw": "太平洋海域",
        "time": now - timedelta(minutes=45, seconds=random.randint(10, 50)),
        "src": "美國海軍學會新聞 (USNI)", "type": "info", "icon": "🚢",
        "lat": 23.5, "lon": 119.5,
        "msg": "衛星追蹤到航母打擊群變更航向，進入警戒狀態。"
    },
    {
        "loc_en": "Sudan", "loc_tw": "蘇丹",
        "time": now - timedelta(hours=1, minutes=12),
        "src": "法新社 (AFP)", "type": "error", "icon": "✈️",
        "lat": 15.6, "lon": 32.5,
        "msg": "首都圈通訊再次全面中斷，疑似發生大規模空襲。"
    },
    {
        "loc_en": "Red Sea", "loc_tw": "紅海海域",
        "time": now - timedelta(minutes=8),
        "src": "英國海事貿易行動辦公室 (UKMTO)", "type": "warning", "icon": "🚀",
        "lat": 13.0, "lon": 43.0,
        "msg": "偵測到不明無人機群正在接近商船航道。"
    }
]

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
    st.subheader("📰 實時滾動戰報")
    
    # 根據資料動態生成戰報卡片
    for ev in events:
        time_str = ev["time"].strftime("%Y-%m-%d %H:%M:%S")
        content = f"""
        📅 **{time_str}** | 📡 來源: {ev['src']} <span class='translate-tag'>🤖 即時翻譯</span><br>
        **{ev['loc_tw']}:** {ev['msg']}
        """
        if ev["type"] == "error":
            st.error(content, icon="🔴")
        elif ev["type"] == "warning":
            st.warning(content, icon="🟠")
        else:
            st.info(content, icon="🔵")
    
    st.markdown("---")
    st.subheader("⚠️ 國家不穩定風險")
    # 模擬數值隨機微幅跳動
    st.metric(label="🇮🇷 伊朗風險指數", value=f"{85 + random.randint(-1, 2)} / 100", delta="升級中", delta_color="inverse")
    st.metric(label="🇺🇦 烏克蘭風險指數", value=f"{98 + random.randint(-1, 1)} / 100", delta="極高", delta_color="inverse")

# 【右側版面】：動態戰情地圖
with col_right:
    fig = go.Figure()

    # 第一層：國家區域上色 (中文名稱)
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

    # 第二層：【攻打動畫軌跡】模擬飛彈/攻擊路線
    # 俄羅斯(邊境) 往 烏克蘭東部 的攻擊線
    fig.add_trace(go.Scattergeo(
        lon=[40.0, 37.5], lat=[50.0, 48.0],
        mode='lines',
        line=dict(width=3, color='orange', dash='dot' if is_pulse else 'solid'),
        hoverinfo='skip'
    ))
    # 葉門 往 紅海 的無人機軌跡
    fig.add_trace(go.Scattergeo(
        lon=[44.0, 43.0], lat=[15.0, 13.0],
        mode='lines',
        line=dict(width=2, color='red', dash='dash' if is_pulse else 'solid'),
        hoverinfo='skip'
    ))

    # 第三層：部隊與戰火圖示打點 (動態大小與中文 Hover)
    lats = [e["lat"] for e in events]
    lons = [e["lon"] for e in events]
    icons = [e["icon"] for e in events]
    
    # 滑鼠移過去顯示的文字 (結合時間、來源與中文訊息)
    hover_texts = [
        f"<b>{e['loc_tw']}</b><br>🕒 {e['time'].strftime('%H:%M:%S')}<br>📡 {e['src']}<br>⚠️ {e['msg']}" 
        for e in events
    ]
    
    # 讓爆炸圖示隨時間變換大小 (產生脈衝閃爍感)
    sizes = [38 if (e["icon"] == "💥" and is_pulse) else 26 for e in events]

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
