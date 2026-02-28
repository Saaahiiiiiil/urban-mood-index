import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime
import psycopg2
import warnings
warnings.filterwarnings("ignore")

st.set_page_config(
    page_title="Urban Mood Index",
    page_icon="🌆",
    layout="wide",
    initial_sidebar_state="collapsed"
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Instrument+Serif:ital@0;1&family=Geist:wght@200;300;400;500;600&display=swap');

*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

:root {
    --bg:          #0e0e10;
    --bg-raised:   #161618;
    --bg-elevated: #1c1c1e;
    --bg-float:    #242426;
    --border:      rgba(255,255,255,0.07);
    --border-mid:  rgba(255,255,255,0.12);
    --text-1:      #f2f2f7;
    --text-2:      #8e8e93;
    --text-3:      #48484a;
    --blue:        #3b82f6;
    --blue-dim:    rgba(59,130,246,0.12);
    --green:       #34d399;
    --green-dim:   rgba(52,211,153,0.10);
    --red:         #f87171;
    --red-dim:     rgba(248,113,113,0.10);
    --amber:       #fbbf24;
    --amber-dim:   rgba(251,191,36,0.10);
    --radius-sm:   10px;
    --radius-md:   14px;
    --radius-lg:   20px;
    --radius-xl:   26px;
}

html, body, [class*="css"] {
    font-family: 'Geist', -apple-system, BlinkMacSystemFont, sans-serif !important;
    background: var(--bg) !important;
    color: var(--text-1) !important;
    -webkit-font-smoothing: antialiased;
}
.stApp { background: var(--bg) !important; }
#MainMenu, footer, header,
[data-testid="stToolbar"],
[data-testid="stDecoration"],
.stDeployButton { display: none !important; }
.block-container { padding: 0 !important; max-width: 100% !important; }
section[data-testid="stSidebar"] { display: none; }
div[data-testid="column"] { padding: 0 !important; }
.stPlotlyChart > div { border-radius: var(--radius-md) !important; }

/* ─── SCROLLBAR ─── */
::-webkit-scrollbar { width: 5px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: var(--bg-float); border-radius: 4px; }

/* ─── HERO ─── */
.hero {
    padding: 56px 60px 48px;
    border-bottom: 1px solid var(--border);
    display: flex;
    align-items: flex-end;
    justify-content: space-between;
    gap: 40px;
    background: linear-gradient(160deg, #131316 0%, #0e0e10 60%);
}
.hero-eyebrow {
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 11px;
    font-weight: 500;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    color: var(--text-2);
    margin-bottom: 14px;
}
.live-pip {
    width: 6px; height: 6px;
    background: var(--green);
    border-radius: 50%;
    animation: pip 2.8s ease-in-out infinite;
    box-shadow: 0 0 0 0 rgba(52,211,153,0.5);
}
@keyframes pip {
    0%   { box-shadow: 0 0 0 0 rgba(52,211,153,0.5); }
    60%  { box-shadow: 0 0 0 6px rgba(52,211,153,0); }
    100% { box-shadow: 0 0 0 0 rgba(52,211,153,0); }
}
.hero-title {
    font-family: 'Instrument Serif', Georgia, serif;
    font-size: 54px;
    font-weight: 400;
    line-height: 1.04;
    letter-spacing: -0.025em;
    color: var(--text-1);
}
.hero-title em {
    font-style: italic;
    color: var(--blue);
}
.hero-desc {
    margin-top: 16px;
    font-size: 15px;
    font-weight: 300;
    color: var(--text-2);
    line-height: 1.65;
    max-width: 500px;
}
.hero-right { text-align: right; flex-shrink: 0; }
.hero-kpi-label {
    font-size: 11px;
    font-weight: 500;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    color: var(--text-3);
    margin-bottom: 8px;
}
.hero-kpi {
    font-family: 'Instrument Serif', serif;
    font-size: 80px;
    font-weight: 400;
    line-height: 1;
    letter-spacing: -0.04em;
}
.hero-kpi.positive { color: var(--green); }
.hero-kpi.negative { color: var(--red);   }
.hero-kpi.neutral  { color: var(--amber); }
.hero-kpi-sub {
    margin-top: 8px;
    font-size: 12px;
    color: var(--text-3);
    font-weight: 300;
}

/* ─── BODY ─── */
.body { padding: 48px 60px 64px; display: flex; flex-direction: column; gap: 48px; }

/* ─── SECTION ─── */
.section-head {
    display: flex;
    align-items: baseline;
    justify-content: space-between;
    margin-bottom: 22px;
}
.section-title {
    font-size: 20px;
    font-weight: 500;
    letter-spacing: -0.02em;
    color: var(--text-1);
}
.section-meta {
    font-size: 12px;
    font-weight: 400;
    color: var(--text-3);
    letter-spacing: 0.04em;
    text-transform: uppercase;
}

/* ─── STAT ROW ─── */
.stat-row {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 14px;
}
.stat-tile {
    background: var(--bg-raised);
    border: 1px solid var(--border);
    border-radius: var(--radius-lg);
    padding: 24px 24px 20px;
    transition: background 0.25s, border-color 0.25s;
    position: relative;
    overflow: hidden;
}
.stat-tile:hover {
    background: var(--bg-elevated);
    border-color: var(--border-mid);
}
.stat-tile-glow {
    position: absolute;
    top: -30px; right: -30px;
    width: 100px; height: 100px;
    border-radius: 50%;
    opacity: 0.15;
    filter: blur(30px);
    pointer-events: none;
}
.stat-tile-icon {
    font-size: 15px;
    margin-bottom: 18px;
    opacity: 0.6;
}
.stat-num {
    font-family: 'Instrument Serif', serif;
    font-size: 40px;
    font-weight: 400;
    letter-spacing: -0.03em;
    line-height: 1;
    color: var(--text-1);
}
.stat-num.positive { color: var(--green); }
.stat-num.negative { color: var(--red);   }
.stat-num.neutral  { color: var(--amber); }
.stat-lbl {
    font-size: 13px;
    font-weight: 300;
    color: var(--text-2);
    margin-top: 8px;
}
.stat-badge {
    display: inline-block;
    font-size: 10px;
    font-weight: 500;
    letter-spacing: 0.06em;
    text-transform: uppercase;
    padding: 3px 9px;
    border-radius: 20px;
    margin-top: 12px;
}
.stat-badge.positive { background: var(--green-dim); color: var(--green); }
.stat-badge.negative { background: var(--red-dim);   color: var(--red);   }
.stat-badge.neutral  { background: var(--amber-dim); color: var(--amber); }

/* ─── CITY GRID ─── */
.city-row {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 16px;
}
.city-tile {
    background: var(--bg-raised);
    border: 1px solid var(--border);
    border-radius: var(--radius-xl);
    padding: 32px 28px 28px;
    transition: all 0.3s cubic-bezier(.4,0,.2,1);
    position: relative;
    overflow: hidden;
}
.city-tile:hover {
    background: var(--bg-elevated);
    transform: translateY(-3px);
    border-color: var(--border-mid);
    box-shadow: 0 20px 48px rgba(0,0,0,0.4);
}
.city-tile-stripe {
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 2px;
    border-radius: var(--radius-xl) var(--radius-xl) 0 0;
}
.city-tile-stripe.positive { background: linear-gradient(90deg, var(--green), rgba(52,211,153,0)); }
.city-tile-stripe.negative { background: linear-gradient(90deg, var(--red),   rgba(248,113,113,0)); }
.city-tile-stripe.neutral  { background: linear-gradient(90deg, var(--amber), rgba(251,191,36,0));  }
.city-tile-top {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    margin-bottom: 24px;
}
.city-tile-name {
    font-size: 13px;
    font-weight: 500;
    letter-spacing: 0.04em;
    text-transform: uppercase;
    color: var(--text-2);
}
.city-chip {
    font-size: 10px;
    font-weight: 500;
    letter-spacing: 0.06em;
    text-transform: uppercase;
    padding: 3px 10px;
    border-radius: 20px;
}
.city-chip.positive { background: var(--green-dim); color: var(--green); }
.city-chip.negative { background: var(--red-dim);   color: var(--red);   }
.city-chip.neutral  { background: var(--amber-dim); color: var(--amber); }
.city-score-num {
    font-family: 'Instrument Serif', serif;
    font-size: 68px;
    font-weight: 400;
    letter-spacing: -0.04em;
    line-height: 1;
    margin-bottom: 6px;
}
.city-score-num.positive { color: var(--green); }
.city-score-num.negative { color: var(--red);   }
.city-score-num.neutral  { color: var(--amber); }
.city-score-ts {
    font-size: 12px;
    font-weight: 300;
    color: var(--text-3);
}

/* ─── CARD ─── */
.card {
    background: var(--bg-raised);
    border: 1px solid var(--border);
    border-radius: var(--radius-lg);
    padding: 28px;
    height: 100%;
}
.card-title {
    font-size: 16px;
    font-weight: 500;
    letter-spacing: -0.01em;
    color: var(--text-1);
    margin-bottom: 6px;
}
.card-sub {
    font-size: 12px;
    font-weight: 300;
    color: var(--text-3);
    display: block;
    margin-bottom: 24px;
}

/* ─── DIVIDER ─── */
.divider {
    height: 1px;
    background: var(--border);
    margin: 4px 0;
}

/* ─── RANK ─── */
.rank-item {
    display: flex;
    align-items: center;
    gap: 16px;
    padding: 14px 0;
    border-bottom: 1px solid var(--border);
    transition: padding-left 0.2s;
}
.rank-item:last-child { border-bottom: none; padding-bottom: 0; }
.rank-item:hover { padding-left: 4px; }
.rank-n {
    font-size: 11px;
    font-weight: 500;
    color: var(--text-3);
    width: 18px;
    text-align: center;
}
.rank-name {
    flex: 1;
    font-size: 14px;
    font-weight: 400;
    color: var(--text-1);
}
.rank-track {
    flex: 2;
    height: 3px;
    background: var(--bg-float);
    border-radius: 2px;
    overflow: hidden;
}
.rank-fill { height: 100%; border-radius: 2px; }
.rank-val {
    width: 44px;
    text-align: right;
    font-size: 13px;
    font-weight: 500;
    letter-spacing: -0.01em;
}

/* ─── ALERTS ─── */
.alert-row {
    display: flex;
    align-items: flex-start;
    gap: 13px;
    padding: 14px 16px;
    border-radius: var(--radius-sm);
    margin-bottom: 10px;
}
.alert-row:last-child { margin-bottom: 0; }
.alert-row.high     { background: var(--red-dim);   }
.alert-row.moderate { background: var(--amber-dim); }
.alert-row.stable   { background: var(--green-dim); }
.alert-dot {
    width: 7px; height: 7px;
    border-radius: 50%;
    margin-top: 4px;
    flex-shrink: 0;
}
.alert-row.high     .alert-dot { background: var(--red);   }
.alert-row.moderate .alert-dot { background: var(--amber); }
.alert-row.stable   .alert-dot { background: var(--green); }
.alert-main {
    font-size: 13px;
    font-weight: 500;
    line-height: 1.4;
}
.alert-row.high     .alert-main { color: var(--red);   }
.alert-row.moderate .alert-main { color: var(--amber); }
.alert-row.stable   .alert-main { color: var(--green); }
.alert-detail {
    font-size: 11px;
    font-weight: 300;
    color: var(--text-2);
    margin-top: 3px;
}

/* ─── FORECAST ─── */
.fc-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 16px 0;
    border-bottom: 1px solid var(--border);
}
.fc-row:last-child { border-bottom: none; }
.fc-name {
    font-size: 14px;
    font-weight: 400;
    color: var(--text-1);
}
.fc-dir {
    font-size: 11px;
    font-weight: 300;
    color: var(--text-3);
    margin-top: 3px;
}
.fc-val {
    font-family: 'Instrument Serif', serif;
    font-size: 26px;
    font-weight: 400;
    letter-spacing: -0.02em;
    display: flex;
    align-items: center;
    gap: 4px;
}
.fc-val.up     { color: var(--red);   }
.fc-val.down   { color: var(--green); }
.fc-val.stable { color: var(--amber); }
.fc-arrow { font-size: 16px; }

/* ─── FOOTER ─── */
.footer {
    border-top: 1px solid var(--border);
    padding: 20px 60px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    background: var(--bg);
}
.footer-text {
    font-size: 11px;
    font-weight: 300;
    color: var(--text-3);
    letter-spacing: 0.04em;
}
</style>
""", unsafe_allow_html=True)

# ── CONSTANTS ──────────────────────────────────────────────────────
CITY_COORDS = {
    "Chennai":   {"lat": 13.0827, "lon": 80.2707},
    "Mumbai":    {"lat": 19.0760, "lon": 72.8777},
    "Bangalore": {"lat": 12.9716, "lon": 77.5946},
}
CITY_COLORS = {
    "Chennai":   "#3b82f6",
    "Mumbai":    "#34d399",
    "Bangalore": "#f87171",
}

def base_layout(h=400):
    return dict(
        height=h,
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(family='Geist, sans-serif', color='#8e8e93', size=12),
        margin=dict(l=4, r=4, t=8, b=4),
        xaxis=dict(
            showgrid=False, zeroline=False,
            tickfont=dict(color='#48484a', size=11),
            linecolor='rgba(255,255,255,0.06)',
        ),
        yaxis=dict(
            gridcolor='rgba(255,255,255,0.04)',
            zeroline=True, zerolinecolor='rgba(255,255,255,0.08)', zerolinewidth=1,
            tickfont=dict(color='#48484a', size=11),
        ),
        hoverlabel=dict(
            bgcolor='#1c1c1e',
            bordercolor='rgba(255,255,255,0.12)',
            font=dict(size=13, color='#f2f2f7', family='Geist'),
        ),
        legend=dict(
            bgcolor='rgba(0,0,0,0)',
            font=dict(size=12, color='#8e8e93'),
        ),
    )

# ── DATA ───────────────────────────────────────────────────────────
@st.cache_data(ttl=30)
def load_mood():
    try:
        conn = psycopg2.connect(
            host="localhost", database="urban_mood", user="Sahil", password="1234"
        )
        df = pd.read_sql("SELECT window_start, city, mood_score FROM mood_data", conn)
        conn.close()
        if df.empty:
            return pd.DataFrame()
        df["window_start"] = pd.to_datetime(df["window_start"], errors="coerce")
        df = df.dropna(subset=["window_start","mood_score"])
        df = df[(df["mood_score"] >= -1) & (df["mood_score"] <= 1)]
        df = df.drop_duplicates(subset=["window_start","city"])
        return df.sort_values("window_start")
    except Exception as e:
        st.error(f"Database error: {e}")
        return pd.DataFrame()

def compute_stress(df):
    if df.empty: return pd.DataFrame()
    latest = df.sort_values("window_start").groupby("city").tail(1).copy()
    latest["negative_component"] = ((1 - latest["mood_score"]) / 2).clip(0, 1)
    latest["stress_score"] = (
        0.4 * latest["negative_component"] + 0.3*0.5 + 0.2*0.3 + 0.1*0.4
    ).clip(0, 1)
    return latest

def forecast_stress(mood_df, city):
    cd = mood_df[mood_df["city"] == city].sort_values("window_start").tail(10)
    if len(cd) < 3: return None
    y = (1 - cd["mood_score"]) / 2
    x = np.arange(len(y))
    fv = np.poly1d(np.polyfit(x, y, 1))(len(y))
    return float(np.clip(fv, 0, 1))

def mc(score):
    return "positive" if score > 0.2 else "negative" if score < -0.2 else "neutral"

def color_for(cls):
    return {"positive": "#34d399", "negative": "#f87171", "neutral": "#fbbf24"}[cls]

# ── LOAD ───────────────────────────────────────────────────────────
mood_df = load_mood()

if mood_df.empty:
    st.markdown("""
    <div style="height:100vh;display:flex;align-items:center;justify-content:center;
         font-family:'Geist',sans-serif;font-size:14px;color:#48484a;letter-spacing:0.06em;">
        Waiting for stream data
    </div>""", unsafe_allow_html=True)
    st.stop()

latest_window = mood_df["window_start"].max()
latest_mood   = mood_df[mood_df["window_start"] == latest_window].copy()
stress_df     = compute_stress(mood_df)
avg_mood      = latest_mood["mood_score"].mean()
avg_cls       = mc(avg_mood)

# ── HERO ───────────────────────────────────────────────────────────
st.markdown(f"""
<div class="hero">
  <div>
    <div class="hero-eyebrow">
      <span class="live-pip"></span>
      Live · Refreshes every 30s · {latest_window.strftime('%d %b %Y')}
    </div>
    <div class="hero-title">Urban <em>Mood</em> Index</div>
    <div class="hero-desc">
      Real-time sentiment across Chennai, Mumbai &amp; Bangalore —
      aggregated from social signals, news, weather and traffic.
    </div>
  </div>
  <div class="hero-right">
    <div class="hero-kpi-label">Average Mood Score</div>
    <div class="hero-kpi {avg_cls}">{avg_mood:+.3f}</div>
    <div class="hero-kpi-sub">Last window · {latest_window.strftime('%H:%M:%S')}</div>
  </div>
</div>
<div class="body">
""", unsafe_allow_html=True)

# ── STAT TILES ─────────────────────────────────────────────────────
glow = color_for(avg_cls)
st.markdown(f"""
<div>
  <div class="section-head">
    <span class="section-title">Overview</span>
    <span class="section-meta">Live snapshot</span>
  </div>
  <div class="stat-row">
    <div class="stat-tile">
      <div class="stat-tile-glow" style="background:#3b82f6;"></div>
      <div class="stat-tile-icon">🏙</div>
      <div class="stat-num">{len(latest_mood)}</div>
      <div class="stat-lbl">Cities monitored</div>
    </div>
    <div class="stat-tile">
      <div class="stat-tile-glow" style="background:{glow};"></div>
      <div class="stat-tile-icon">{'🟢' if avg_cls=='positive' else '🔴' if avg_cls=='negative' else '🟡'}</div>
      <div class="stat-num {avg_cls}">{avg_mood:+.3f}</div>
      <div class="stat-lbl">Average mood score</div>
      <span class="stat-badge {avg_cls}">{avg_cls}</span>
    </div>
    <div class="stat-tile">
      <div class="stat-tile-glow" style="background:#3b82f6;"></div>
      <div class="stat-tile-icon">📊</div>
      <div class="stat-num">{len(mood_df)}</div>
      <div class="stat-lbl">Total data points</div>
    </div>
    <div class="stat-tile">
      <div class="stat-tile-glow" style="background:#34d399;"></div>
      <div class="stat-tile-icon">🕐</div>
      <div class="stat-num" style="font-size:32px;letter-spacing:-0.02em;">{latest_window.strftime('%H:%M')}</div>
      <div class="stat-lbl">Last updated today</div>
    </div>
  </div>
</div>
""", unsafe_allow_html=True)

# ── CITY TILES ─────────────────────────────────────────────────────
city_tiles_html = """
<div>
  <div class="section-head">
    <span class="section-title">City Readings</span>
    <span class="section-meta">Current window</span>
  </div>
  <div class="city-row">
"""
for _, row in latest_mood.iterrows():
    s   = float(row["mood_score"])
    cls = mc(s)
    lbl = cls.capitalize()
    city_tiles_html += f"""
    <div class="city-tile">
      <div class="city-tile-stripe {cls}"></div>
      <div class="city-tile-top">
        <div class="city-tile-name">{row['city']}</div>
        <div class="city-chip {cls}">{lbl}</div>
      </div>
      <div class="city-score-num {cls}">{s:+.3f}</div>
      <div class="city-score-ts">Updated {latest_window.strftime('%H:%M:%S')}</div>
    </div>"""
city_tiles_html += "</div></div>"
st.markdown(city_tiles_html, unsafe_allow_html=True)

# ── MAP + TREND ─────────────────────────────────────────────────────
st.markdown("""
<div>
  <div class="section-head">
    <span class="section-title">Geographic &amp; Temporal Analysis</span>
    <span class="section-meta">Map · Trend</span>
  </div>
</div>
""", unsafe_allow_html=True)

c_map, c_trend = st.columns(2, gap="large")

with c_map:
    map_df = latest_mood.copy()
    map_df["lat"]  = map_df["city"].map(lambda x: CITY_COORDS.get(x,{}).get("lat"))
    map_df["lon"]  = map_df["city"].map(lambda x: CITY_COORDS.get(x,{}).get("lon"))
    map_df["size"] = (abs(map_df["mood_score"]) * 80 + 30).clip(20, 120)
    map_df = map_df.dropna(subset=["lat","lon"])

    fig_map = px.scatter_mapbox(
        map_df, lat="lat", lon="lon",
        color="mood_score", size="size",
        hover_name="city",
        hover_data={"mood_score":":.3f","size":False,"lat":False,"lon":False},
        color_continuous_scale=[[0,"#f87171"],[0.5,"#fbbf24"],[1,"#34d399"]],
        color_continuous_midpoint=0,
        zoom=4.6, center={"lat":15,"lon":78.5},
        mapbox_style="dark",
    )
    fig_map.update_layout(
        height=420,
        margin=dict(l=0,r=0,t=0,b=0),
        paper_bgcolor='rgba(0,0,0,0)',
        coloraxis_showscale=False,
    )
    fig_map.update_traces(marker=dict(opacity=0.88, sizemin=14))

    st.markdown('<div class="card" style="padding:4px 4px 2px;">', unsafe_allow_html=True)
    st.plotly_chart(fig_map, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

with c_trend:
    fig_t = go.Figure()
    for city in mood_df["city"].unique():
        cd    = mood_df[mood_df["city"] == city].sort_values("window_start")
        color = CITY_COLORS.get(city, "#8e8e93")
        r,g,b = int(color[1:3],16), int(color[3:5],16), int(color[5:7],16)
        fig_t.add_trace(go.Scatter(
            x=cd["window_start"], y=cd["mood_score"],
            mode="none", fill="tozeroy",
            fillcolor=f"rgba({r},{g},{b},0.06)",
            showlegend=False, hoverinfo="skip",
        ))
        fig_t.add_trace(go.Scatter(
            x=cd["window_start"], y=cd["mood_score"],
            name=city, mode="lines+markers",
            line=dict(color=color, width=2, shape='spline', smoothing=0.7),
            marker=dict(size=5, color=color, line=dict(width=1.5, color='#0e0e10')),
            hovertemplate=f"<b>{city}</b><br>%{{x|%H:%M:%S}}<br>%{{y:+.3f}}<extra></extra>",
        ))
    fig_t.add_hline(y=0, line=dict(color='rgba(255,255,255,0.08)', dash='dot', width=1.5))
    layout = base_layout(420)
    layout["legend"] = dict(
        bgcolor='rgba(0,0,0,0)', font=dict(size=12, color='#8e8e93'),
        x=0.02, y=0.98, xanchor='left', yanchor='top',
    )
    fig_t.update_layout(**layout, showlegend=True)

    st.markdown('<div class="card" style="padding:22px 22px 8px;">', unsafe_allow_html=True)
    st.markdown('<div class="card-title">Mood Over Time</div>', unsafe_allow_html=True)
    st.markdown('<span class="card-sub">30-second streaming windows</span>', unsafe_allow_html=True)
    st.plotly_chart(fig_t, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

# ── RANKING · ALERTS · FORECAST ─────────────────────────────────────
st.markdown("""
<div>
  <div class="section-head">
    <span class="section-title">Stress Intelligence</span>
    <span class="section-meta">Ranking · Alerts · Forecast</span>
  </div>
</div>
""", unsafe_allow_html=True)

c1, c2, c3 = st.columns(3, gap="large")
rank_colors = ["#f87171","#fbbf24","#34d399"]

with c1:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown('<div class="card-title">Stress Ranking</div>', unsafe_allow_html=True)
    st.markdown('<span class="card-sub">Highest to lowest stress index</span>', unsafe_allow_html=True)
    if not stress_df.empty:
        for i, (_, row) in enumerate(stress_df.sort_values("stress_score", ascending=False).iterrows()):
            s     = row["stress_score"]
            color = rank_colors[i] if i < 3 else "#48484a"
            st.markdown(f"""
            <div class="rank-item">
              <div class="rank-n">{i+1}</div>
              <div class="rank-name">{row['city']}</div>
              <div class="rank-track">
                <div class="rank-fill" style="width:{int(s*100)}%;background:{color};"></div>
              </div>
              <div class="rank-val" style="color:{color};">{s:.3f}</div>
            </div>""", unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

with c2:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown('<div class="card-title">Real-Time Alerts</div>', unsafe_allow_html=True)
    st.markdown('<span class="card-sub">Threshold-based monitoring</span>', unsafe_allow_html=True)
    if not stress_df.empty:
        for _, row in stress_df.sort_values("stress_score", ascending=False).iterrows():
            s = row["stress_score"]
            if s >= 0.7:
                cls, main, detail = "high",     "High stress detected",   f"Index {s:.3f} — attention recommended"
            elif s >= 0.5:
                cls, main, detail = "moderate", "Moderate stress levels", f"Index {s:.3f} — monitor closely"
            else:
                cls, main, detail = "stable",   "Levels are stable",       f"Index {s:.3f} — all clear"
            st.markdown(f"""
            <div class="alert-row {cls}">
              <div class="alert-dot"></div>
              <div>
                <div class="alert-main"><strong>{row['city']}</strong> · {main}</div>
                <div class="alert-detail">{detail}</div>
              </div>
            </div>""", unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

with c3:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown('<div class="card-title">Stress Forecast</div>', unsafe_allow_html=True)
    st.markdown('<span class="card-sub">Predicted next window</span>', unsafe_allow_html=True)
    for city in latest_mood["city"].tolist():
        fv  = forecast_stress(mood_df, city)
        cvs = stress_df[stress_df["city"]==city]["stress_score"].values
        if fv is None or len(cvs) == 0:
            st.markdown(f"""
            <div class="fc-row">
              <div><div class="fc-name">{city}</div><div class="fc-dir">Not enough data</div></div>
              <div class="fc-val stable">—</div>
            </div>""", unsafe_allow_html=True)
            continue
        delta = fv - cvs[0]
        css, arrow, direction = (
            ("up","↑","Rising")      if delta > 0.05 else
            ("down","↓","Easing")    if delta < -0.05 else
            ("stable","→","Steady")
        )
        st.markdown(f"""
        <div class="fc-row">
          <div>
            <div class="fc-name">{city}</div>
            <div class="fc-dir">{direction}</div>
          </div>
          <div class="fc-val {css}">
            <span class="fc-arrow">{arrow}</span>{fv:.3f}
          </div>
        </div>""", unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

# ── GAUGES ─────────────────────────────────────────────────────────
st.markdown("""
<div>
  <div class="section-head">
    <span class="section-title">Stress Gauges</span>
    <span class="section-meta">Per-city index</span>
  </div>
</div>
""", unsafe_allow_html=True)

if not stress_df.empty:
    gcols = st.columns(len(stress_df), gap="large")
    for col, (_, row) in zip(gcols, stress_df.iterrows()):
        s     = row["stress_score"]
        color = "#f87171" if s >= 0.7 else "#fbbf24" if s >= 0.5 else "#34d399"
        r_,g_,b_ = int(color[1:3],16), int(color[3:5],16), int(color[5:7],16)

        fig_g = go.Figure(go.Indicator(
            mode="gauge+number",
            value=s,
            number=dict(
                font=dict(family="Instrument Serif", color=color, size=28),
                valueformat=".3f"
            ),
            title=dict(
                text=row["city"],
                font=dict(family="Geist", color="#8e8e93", size=13)
            ),
            gauge=dict(
                axis=dict(
                    range=[0,1], nticks=5,
                    tickcolor="#48484a",
                    tickfont=dict(color="#48484a", size=9),
                ),
                bar=dict(color=color, thickness=0.45),
                bgcolor="rgba(0,0,0,0)",
                borderwidth=0,
                steps=[
                    dict(range=[0,0.5],   color=f"rgba({r_},{g_},{b_},0.04)"),
                    dict(range=[0.5,0.7], color=f"rgba({r_},{g_},{b_},0.07)"),
                    dict(range=[0.7,1],   color=f"rgba({r_},{g_},{b_},0.10)"),
                ],
                threshold=dict(
                    line=dict(color=color, width=2),
                    thickness=0.85, value=s,
                ),
            )
        ))
        fig_g.update_layout(
            height=220,
            margin=dict(l=24, r=24, t=40, b=16),
            paper_bgcolor='rgba(0,0,0,0)',
        )
        with col:
            st.markdown('<div class="card" style="padding:16px;">', unsafe_allow_html=True)
            st.plotly_chart(fig_g, use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)

# ── CLOSE BODY + FOOTER ─────────────────────────────────────────────
st.markdown(f"""
</div>
<div class="footer">
  <div class="footer-text">Urban Mood Index — Real-time city sentiment platform</div>
  <div class="footer-text">Auto-refreshes every 30 seconds · Last update {latest_window.strftime('%H:%M:%S')}</div>
</div>
""", unsafe_allow_html=True)