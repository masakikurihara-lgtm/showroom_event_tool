import streamlit as st
import pandas as pd
import plotly.express as px
import requests
from datetime import datetime

st.set_page_config(page_title="Showroom Event Tracker", layout="wide")
st.title("Showroom Event Tracker（リアルタイム版）")

# --- イベントID入力 ---
event_id = st.text_input("イベントIDを入力してください", "40198")

if event_id:
    API_URL = f"https://www.showroom-live.com/api/event/ranking?event_id={event_id}"

    try:
        response = requests.get(API_URL)
        response.raise_for_status()
        json_data = response.json()

        # --- DataFrame へ変換 ---
        ranking_data = []
        now = datetime.now()

        for r in json_data.get("ranking", []):
            ranking_data.append({
                "time": now,
                "user": r.get("name", f"ID:{r.get('user_id')}"),
                "points": r.get("point", 0),
                "rank": r.get("rank", None)
            })

        df = pd.DataFrame(ranking_data)

        if df.empty:
            st.warning("ランキングデータが取得できませんでした。")
        else:
            # --- ライバー選択 ---
            participants = df["user"].tolist()
            selected = st.multiselect("表示するライバーを選択", participants, default=participants)
            df = df[df["user"].isin(selected)]

            # --- グラフ表示 ---
            st.subheader("ポイント（取得時点）")
            fig_point = px.bar(df, x="user", y="points", color="user", text="points",
                               title="ポイントランキング", height=500)
            st.plotly_chart(fig_point, use_container_width=True)

            # --- ランキング表 ---
            st.subheader("最新ランキング")
            st.table(df.sort_values("rank")[["rank", "user", "points"]])

    except Exception as e:
        st.error(f"データ取得に失敗しました: {e}")
