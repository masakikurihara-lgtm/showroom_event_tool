import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np
from datetime import datetime, timedelta
from streamlit_autorefresh import st_autorefresh

# --- ページ設定 ---
st.set_page_config(page_title="Showroom Event Tracker", layout="wide")
st.title("Showroom Event Tracker（リアルタイムサンプル）")

# --- 自動更新設定（5秒ごと） ---
st_autorefresh(interval=5*1000, key="refresh")

# --- ユーザー選択 ---
participants = ["ライバーA", "ライバーB", "ライバーC"]
selected = st.multiselect("表示するライバーを選択", participants, default=participants)

# --- サンプルJSONデータ作成 ---
# 初期データ作成（過去2時間分、5分間隔）
times = [datetime.now() - timedelta(minutes=5*i) for i in reversed(range(24))]
event_data = []
for t in times:
    for user in participants:
        points = np.random.randint(500, 2000)
        event_data.append({"time": t, "user": user, "points": points})

# --- データ更新（リアルタイム感） ---
# 各ライバーの最新ポイントをランダムに増減
for entry in event_data:
    if entry["user"] in selected:
        entry["points"] += np.random.randint(-50, 100)

# DataFrame化
df = pd.DataFrame(event_data)
df["time"] = pd.to_datetime(df["time"])
df = df[df["user"].isin(selected)]

# --- 順位計算 ---
df["rank"] = df.groupby("time")["points"].rank(ascending=False, method="min")

# --- グラフ表示 ---
st.subheader("順位推移")
fig_rank = px.line(df, x="time", y="rank", color="user", markers=True,
                   title="順位推移（低いほど上位）")
fig_rank.update_yaxes(autorange="reversed")
st.plotly_chart(fig_rank, use_container_width=True)

st.subheader("ポイント推移")
fig_point = px.line(df, x="time", y="points", color="user", markers=True,
                    title="ポイント推移")
st.plotly_chart(fig_point, use_container_width=True)

# --- 最新ランキング表 ---
st.subheader("最新ランキング")
latest = df[df["time"] == df["time"].max()].sort_values("rank")
st.table(latest[["user", "points", "rank"]])
