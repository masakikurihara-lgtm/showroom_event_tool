import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np
from datetime import datetime, timedelta
import time

st.set_page_config(page_title="Showroom Event Tracker", layout="wide")
st.title("Showroom Event Tracker（サンプル版）")

# --- ユーザー選択 ---
participants = ["ライバーA", "ライバーB", "ライバーC"]
selected = st.multiselect("表示するライバーを選択", participants, default=participants)

# --- サンプルデータ生成関数 ---
def generate_sample_data():
    times = [datetime.now() - timedelta(minutes=5*i) for i in reversed(range(24))]
    data_list = []
    for t in times:
        for user in participants:
            points = np.random.randint(500, 2000)
            data_list.append({"time": t, "user": user, "points": points})
    return pd.DataFrame(data_list)

# --- リアルタイム更新 ---
st.subheader("順位推移")
st.subheader("ポイント推移")
st.subheader("最新ランキング")

placeholder_rank = st.empty()
placeholder_point = st.empty()
placeholder_table = st.empty()
placeholder_alert = st.empty()

# 簡易的に5秒ごとに更新（サンプル）
for _ in range(10):  # デモでは10回更新
    df = generate_sample_data()
    df = df[df["user"].isin(selected)]
    df["rank"] = df.groupby("time")["points"].rank(ascending=False, method="min")

    # グラフ
    fig_rank = px.line(df, x="time", y="rank", color="user", markers=True, title="順位推移（低いほど上位）")
    fig_rank.update_yaxes(autorange="reversed")
    fig_point = px.line(df, x="time", y="points", color="user", markers=True, title="ポイント推移")

    # 最新ランキング
    latest = df[df["time"] == df["time"].max()].sort_values("rank")

    # アラート例：順位が3位以下のライバーがいたら表示
    alert_users = latest[latest["rank"] > 3]["user"].tolist()
    if alert_users:
        alert_text = "⚠️ 順位が下がっています: " + ", ".join(alert_users)
    else:
        alert_text = "順位は安定しています。"

    # 表示更新
    placeholder_rank.plotly_chart(fig_rank, use_container_width=True)
    placeholder_point.plotly_chart(fig_point, use_container_width=True)
    placeholder_table.table(latest[["user", "points", "rank"]])
    placeholder_alert.info(alert_text)

    time.sleep(5)
