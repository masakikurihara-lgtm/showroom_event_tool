import streamlit as st
import requests
import pandas as pd

st.set_page_config(page_title="SHOWROOM イベント確認ツール", layout="wide")
st.title("SHOWROOM イベント確認ツール")

# 取得するページ数
pages_to_fetch = st.number_input("取得するページ数", min_value=1, max_value=50, value=5)

events_list = []

for page in range(1, pages_to_fetch + 1):
    url = f"https://www.showroom-live.com/api/event/search?page={page}"
    resp = requests.get(url)
    if resp.status_code == 200:
        data = resp.json()
        events = data.get("events", [])
        events_list.extend(events)
    else:
        st.error(f"ページ {page} の取得でエラー")

if not events_list:
    st.warning("取得できるイベントがありませんでした。")
else:
    df_events = pd.DataFrame(events_list)
    # 表示する列を絞る
    df_events = df_events[['id','name','start_at','end_at','status']]
    st.dataframe(df_events)

    # 選択ボックスでイベントを選択
    selected_event = st.selectbox("確認したいイベントを選択", df_events['name'])
    event_id = df_events[df_events['name']==selected_event]['id'].values[0]

    st.write(f"選択したイベントID: {event_id}")
