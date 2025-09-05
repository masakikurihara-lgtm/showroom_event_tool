import requests
import pandas as pd
import streamlit as st
from datetime import datetime, timezone, timedelta

st.title("SHOWROOM イベント確認テスト")

max_page = st.number_input("取得するページ数", min_value=1, max_value=10, value=3)

event_type = st.selectbox(
    "イベント種類を選択",
    [("開催中", 1), ("終了含む", 0)]
)

all_events = []

for page in range(1, max_page + 1):
    url = f"https://www.showroom-live.com/api/event/search?onlive={event_type[1]}&p={page}"
    res = requests.get(url)
    if res.status_code != 200:
        st.error(f"ページ {page} の取得に失敗しました (status={res.status_code})")
        continue

    data = res.json()
    events = data.get("event_list", [])
    st.write(f"ページ {page} 取得件数:", len(events))
    all_events.extend(events)

if all_events:
    df = pd.DataFrame(all_events)

    # 必要な列だけ抽出
    df = df[[
        "event_id", "event_name", "type_name",
        "started_at", "ended_at", "event_url_key"
    ]]

    # UNIXタイムを日本時間に変換
    def to_jst(ts):
        if pd.isna(ts): return None
        return datetime.fromtimestamp(int(ts), tz=timezone.utc) + timedelta(hours=9)

    df["開始日時"] = df["started_at"].apply(to_jst)
    df["終了日時"] = df["ended_at"].apply(to_jst)

    # 表示用に整理
    df_display = df[[
        "event_id", "event_name", "type_name", "開始日時", "終了日時", "event_url_key"
    ]]

    st.subheader("イベント一覧")
    st.dataframe(df_display)

    st.success(f"合計 {len(df_display)} 件のイベントを取得しました！")

else:
    st.warning("取得できるイベントがありませんでした。")

# -------------------------------
# イベント選択（一覧から選べるようにする）
# -------------------------------
selected_name = st.selectbox("詳細を表示するイベントを選択してください", df_display["event_name"])
selected_id = df_display[df_display["event_name"] == selected_name]["event_id"].values[0]

st.write(f"選択したイベントID：{selected_id}")

# -------------------------------
# ランキングデータを取得
# -------------------------------
ranking_url = f"https://www.showroom-live.com/api/event/ranking?event_id={selected_id}&page=1"
resp = requests.get(ranking_url)

if resp.status_code == 200:
    ranking_list = resp.json().get("ranking", [])
    if ranking_list:
        rank_df = pd.DataFrame(ranking_list)
        st.subheader("イベントランキング（上位）")
        st.dataframe(rank_df.head(10))  # 上位10人を表形式で表示

        # ポイントを棒グラフで表示
        st.bar_chart(rank_df.set_index("user_name")["point"].head(10))
    else:
        st.info("ランキング情報がありません。")
else:
    st.error("ランキングの取得に失敗しました。")
