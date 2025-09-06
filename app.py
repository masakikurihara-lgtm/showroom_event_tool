import streamlit as st
import pandas as pd
import plotly.express as px
import requests
from datetime import datetime
from streamlit_autorefresh import st_autorefresh

st.set_page_config(page_title="SHOWROOM イベント確認ツール", layout="wide")
st.title("SHOWROOM イベント確認ツール")

# 自動更新（5秒ごと）
st_autorefresh(interval=5 * 1000, key="refresh")

# --- イベント一覧取得 ---
try:
    res = requests.get("https://www.showroom-live.com/api/event/search?page=1")
    res.raise_for_status()
    ev_data = res.json().get("event_list", [])
    events = {e["event_name"]: e["event_id"] for e in ev_data if "event_id" in e}
except Exception as e:
    st.error(f"イベント一覧の取得に失敗しました: {e}")
    events = {}

if not events:
    st.warning("取得できるイベントがありません。もう一度お試しください。")
    st.stop()

# --- イベント選択 ---
selected_name = st.selectbox("表示対象のイベントを選択", list(events.keys()))
selected_id = events[selected_name]
st.write(f"選択されたイベントID: {selected_id}")

# --- ランキング取得 ---
try:
    ranking_url = f"https://www.showroom-live.com/api/event/ranking?event_id={selected_id}"
    r = requests.get(ranking_url)
    r.raise_for_status()
    rank_json = r.json()
    ranking = rank_json.get("ranking", [])
except Exception as e:
    st.error(f"ランキング取得に失敗しました: {e}")
    st.stop()

# DataFrameに整形
now = datetime.now()
df = pd.DataFrame([{
    "time": now,
    "user": r.get("name", f"ID:{r.get('user_id')}"),
    "points": r.get("point", 0),
    "rank": r.get("rank", None)
} for r in ranking])

# --- 表示 ---
if df.empty:
    st.warning("ランキングデータが取得できませんでした。")
else:
    st.subheader("最新ランキング（棒グラフ）")
    fig = px.bar(df, x="user", y="points", color="user", text="points")
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("順位表")
    st.table(df.sort_values("rank")[["rank", "user", "points"]])
