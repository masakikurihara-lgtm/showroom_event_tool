import streamlit as st
import requests
import pandas as pd

st.set_page_config(page_title="SHOWROOM イベント確認ツール", layout="wide")
st.title("SHOWROOM イベント確認ツール")

# イベントID と event_url_key を入力（例として手動入力も可能）
event_id = st.text_input("イベントIDを入力", value="40198")
event_url_key = st.text_input("event_url_key を入力", value="kyotokimonoyuzen2025")

if st.button("ランキング取得・レスポンス確認"):
    max_pages = 5
    all_data = []

    st.info("ランキング取得中...")

    for page in range(1, max_pages + 1):
        url = f"https://www.showroom-live.com/api/event/{event_url_key}/ranking?page={page}"
        try:
            res = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
            if res.status_code != 200:
                st.warning(f"ページ {page} はステータス {res.status_code}")
                continue

            data = res.json()

            # ここで丸ごと表示して、どのキーにポイントやユーザー名があるか確認
            st.write(f"--- ページ {page} レスポンス JSON ---")
            st.json(data)

            # 実際のランキングリストを取得
            page_data = data.get("ranking") or data.get("list") or []
            if not page_data:
                st.info(f"ページ {page} はランキングデータなし")
                break

            all_data.extend(page_data)

        except Exception as e:
            st.error(f"ページ {page} 取得中にエラー: {e}")
            continue

    st.success(f"合計 {len(all_data)} 件のランキングデータを取得しました")
