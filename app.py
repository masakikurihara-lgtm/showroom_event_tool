import requests
import pandas as pd
import streamlit as st

st.title("SHOWROOM イベント確認テスト")

max_page = st.number_input("取得するページ数", min_value=1, max_value=10, value=3)

# イベント種類選択（本来は onlive=1 / 0 で切り替える想定）
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
    events = data.get("event_list", [])  # ← 修正ポイント

    st.write(f"ページ {page} 取得件数:", len(events))
    all_events.extend(events)

if all_events:
    df_events = pd.DataFrame(all_events)
    st.write("取得したデータのカラム一覧:", df_events.columns.tolist())
    st.dataframe(df_events.head(5))
    st.json(all_events[0])  # 1件目のサンプルを表示
else:
    st.warning("取得できるイベントがありませんでした。")
