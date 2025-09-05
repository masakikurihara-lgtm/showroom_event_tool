import streamlit as st
import requests
import pandas as pd

st.title("SHOWROOM イベント確認ツール")

# ページ数を指定
page_num = st.number_input("取得するページ数", min_value=1, max_value=20, value=5)

all_events = []

for page in range(1, page_num+1):
    url = f"https://www.showroom-live.com/api/event/search?onlive=1&p={page}"
    res = requests.get(url)
    if res.status_code == 200:
        data = res.json()
        events = data.get("events", [])
        st.write(f"ページ {page} 取得件数: {len(events)}")
        all_events.extend(events)
    else:
        st.write(f"ページ {page} の取得に失敗しました")

if all_events:
    df_events = pd.DataFrame(all_events)

    # 取得できたカラム一覧を表示
    st.write("取得したデータのカラム一覧:", df_events.columns.tolist())

    # 存在するカラムだけを選択する
    expected_cols = ['event_id','event_name','start_at','end_at','type_name']
    available_cols = [col for col in expected_cols if col in df_events.columns]
    df_events = df_events[available_cols]

    st.dataframe(df_events)
else:
    st.write("取得できるイベントがありませんでした。")
