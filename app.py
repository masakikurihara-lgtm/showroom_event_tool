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
        # 修正: event_listキーを参照
        events = data.get("event_list", [])
        events_list.extend(events)
        st.write(f"ページ {page} 取得件数: {len(events)}")
    else:
        st.error(f"ページ {page} の取得でエラー")

if not events_list:
    st.warning("取得できるイベントがありませんでした。")
else:
    # 必要な列を抽出
    df_events = pd.DataFrame(events_list)
    df_events = df_events[['event_id','event_name','start_at','ended_at','type_name']]
    df_events.rename(columns={
        'event_id':'ID',
        'event_name':'イベント名',
        'start_at':'開始日時',
        'ended_at':'終了日時',
        'type_name':'種別'
    }, inplace=True)
    
    # 表示
    st.dataframe(df_events)

    # 選択ボックスでイベントを選択
    selected_event = st.selectbox("確認したいイベントを選択", df_events['イベント名'])
    event_id = df_events[df_events['イベント名']==selected_event]['ID'].values[0]

    st.write(f"選択したイベントID: {event_id}")
