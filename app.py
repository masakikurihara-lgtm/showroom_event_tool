import streamlit as st
import requests
import pandas as pd

st.title("SHOWROOM イベント確認テスト")

page_num = st.number_input("取得するページ数", min_value=1, max_value=10, value=3)
onlive_flag = st.selectbox("イベント種類を選択", [("開催中",1), ("終了含む",0)], index=0)

all_events = []

for page in range(1, page_num+1):
    url = f"https://www.showroom-live.com/api/event/search?onlive={onlive_flag}&p={page}"
    res = requests.get(url)
    if res.status_code == 200:
        data = res.json()
        events = data.get("events", [])
        st.write(f"ページ {page} 取得件数: {len(events)}")
        if events:
            st.json(events[0])  # 1件目をサンプル表示
        all_events.extend(events)
    else:
        st.write(f"ページ {page} の取得に失敗しました")

if all_events:
    df_events = pd.DataFrame(all_events)
    st.write("取得したデータのカラム一覧:", df_events.columns.tolist())
    st.dataframe(df_events.head())
else:
    st.write("取得できるイベントがありませんでした。")
