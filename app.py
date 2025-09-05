import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np
from datetime import datetime, timedelta

st.set_page_config(page_title="Showroom Event Tracker", layout="wide")
st.title("Showroom Event Tracker（サンプル版）")

# --- ユーザー選択 ---
participants = ["ライバーA", "ライバーB", "ライバーC"]
selected = st.multiselect("表示するライバーを選択", participants, default=participants)

# --- データ生成 ---
# サンプルとして過去2時間分を5分間隔で作成
times = [datetime.now() - timedelta(minutes=5*i) for i in reversed(range(24))]
data_list = []

for t in times:
    for user in participants:
        points = np.random.randint(500, 2000)
        data_list.append({"time": t, "user": user, "points": points})

df = pd.DataFrame(data_list)

# 選択ライバーだけに絞る
df = df[df["user"].isin(selected)]

# --- 順位計算 ---
df["rank"] = df.groupby("time")["points"].rank(ascending=False, method="min")

# --- グラフ表示 ---
st.subheader("順位推移")
fig_rank = px.line(df, x="time", y="rank", color="user", markers=True, title="順位推移（低いほど上位）")
fig_rank.update_yaxes(autorange="reversed")  # 1位が上に来るよう反転
st.plotly_chart(fig_rank, use_container_width=True)

st.subheader("ポイント推移")
fig_point = px.line(df, x="time", y="points", color="user", markers=True, title="ポイント推移")
st.plotly_chart(fig_point, use_container_width=True)

# --- ランキング表 ---
st.subheader("最新ランキング")
latest = df[df["time"] == df["time"].max()].sort_values("rank")
st.table(latest[["user", "points", "rank"]])
