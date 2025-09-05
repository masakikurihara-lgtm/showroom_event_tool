import streamlit as st
import requests
import pandas as pd

st.set_page_config(page_title="SHOWROOM イベント取得テスト", layout="wide")

st.title("SHOWROOM イベント取得テスト")

# 取得ページ数を指定
max_pages = st.number_input("取得するページ数", min_value=1, max_value=10, value=3)

all_events = []

headers = {
    "User-Agent": "Mozilla/5.0"
}

for page in range(1, max_pages + 1):
    url = f"https://www.showroom-live.com/api/event/search?page={page}"
    resp = requests.get(url, headers=headers)
    if resp.status_code == 200:
        data = resp.json()
        events = data.get("events", [])
        all_events.extend(events)
        st.write(f"ページ {page} 取得件数: {len(events)}")
    else:
        st.error(f"ページ {page} の取得でエラー: {resp.status_code}")

if all_events:
    st.success(f"合計取得イベント数: {len(all_events)}")
    # デバッグ表示：最初の数件だけ表示
    st.write(all_events[:10])
else:
    st.warning("取得できるイベントがありませんでした。")
