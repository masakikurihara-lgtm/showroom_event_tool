import streamlit as st
import pandas as pd
import plotly.express as px
import requests
from datetime import datetime

st.set_page_config(page_title="Showroom Event Tracker", layout="wide")
st.title("Showroom Event Tracker（リアルタイム版）")

# --- イベント一覧取得 ---
EVENT_LIST_URL = "https://www.showroom-live.com/api/event/ongoing"

try:
    res = requests.get(EVENT_LIST_URL)
    res.raise_for_status()
    event_list = res.json()

    # イベントを {タイトル: ID} で辞書化
    events = {e["event_name"]: e["event_id"] for e in event_list}

    # --- ユーザーに選択させる ---
    event_name = st.selectbox("イベントを選択してください", list(events.keys()))
    event_id = events[event_name]

    st.write(f"選択したイベントID：{event_id}")

    # --- ランキング取得 ---
    RANKING_URL = f"https://www.showroom-live.com/api/event/ranking?event_id={event_id}"
    r = requests.get(RANKING_URL)
    r.raise_for_status()
    ranking_json = r.json()

    ranking_data = []
    now = datetime.now()
    for r in ranking_json.get("ranking", []):
        ranking_data.append({
            "time": now,
            "user": r.get("name", f"ID:{r.get('user_id')}"),
            "points": r.get("point", 0),
            "rank": r.get("rank", None)
        })

    df = pd.DataFrame(ranking_data)

    if not df.empty:
        # --- グラフ ---
        st.subheader("ポイント棒グラフ")
        fig_point = px.bar(df, x="user", y="points", color="user", text="points")
        st.plotly_chart(fig_point, use_container_width=True)

        # --- テーブル ---
        st.subheader("最新ランキング")
        st.table(df.sort_values("rank")[["rank", "user", "points"]])

    else:
        st.warning("ランキングデータが取得できませんでした。")

except Exception as e:
    st.error(f"イベント一覧またはランキング取得に失敗しました: {e}")
