import streamlit as st
import requests
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="SHOWROOM イベント確認ツール", layout="wide")
st.title("SHOWROOM イベント確認ツール")

# ページ数選択
page_count = st.number_input("取得するページ数", min_value=1, max_value=50, value=5, step=1)

# イベント種類選択
event_type_map = {"終了含む": 0, "開催中": 1}
event_type_choice = st.selectbox("イベント種類を選択", list(event_type_map.items()))
event_type_value = event_type_choice[1]

# データ取得ボタン
if st.button("イベント取得"):
    all_events = []
    st.info("イベント取得中...")
    for page in range(1, page_count + 1):
        url = f"https://www.showroom-live.com/api/event/search?page={page}&include_ended={event_type_value}"
        try:
            res = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
            data = res.json()
            events = data.get("event_list", [])
            st.write(f"ページ {page} 取得件数: {len(events)}")
            all_events.extend(events)
        except Exception as e:
            st.error(f"ページ {page} 取得中にエラー: {e}")
            continue

    if not all_events:
        st.warning("取得できるイベントがありませんでした。")
    else:
        st.success(f"合計 {len(all_events)} 件のイベントを取得しました！")
        df_events = pd.DataFrame(all_events)

        # 表示用 DataFrame
        df_display = df_events[['event_id','event_name','started_at','ended_at','type_name','event_url_key']].copy()
        df_display['開始日時'] = pd.to_datetime(df_display['started_at'], unit='s')
        df_display['終了日時'] = pd.to_datetime(df_display['ended_at'], unit='s')
        st.dataframe(df_display[['event_name','開始日時','終了日時','type_name']])

        # イベント選択
        selected_event_idx = st.selectbox("詳細を表示するイベントを選択してください", df_display.index)
        selected_event = df_display.loc[selected_event_idx]
        st.write(f"選択したイベントID：{selected_event['event_id']}")
        st.write(f"event_url_key：{selected_event['event_url_key']}")

        # ---------- ランキング取得関数 ----------
        def fetch_event_ranking(event_url_key, max_pages=10):
            all_data = []
            for page in range(1, max_pages+1):
                url = f"https://www.showroom-live.com/api/event/{event_url_key}/ranking?page={page}"
                try:
                    res = requests.get(url, headers={"User-Agent":"Mozilla/5.0"})
                    if res.status_code != 200:
                        break
                    data = res.json()
                    if "ranking" not in data or not data["ranking"]:
                        break
                    for item in data["ranking"]:
                        all_data.append({
                            "順位": item.get("rank"),
                            "ユーザー名": item.get("user_name"),
                            "獲得ポイント": item.get("point")
                        })
                except Exception as e:
                    st.error(f"ランキング取得中にエラー: {e}")
                    break
            if not all_data:
                return None
            return pd.DataFrame(all_data)

        # ---------- ランキング取得 ----------
        if st.button("ランキング取得"):
            ranking_df = fetch_event_ranking(selected_event["event_url_key"], max_pages=10)
            if ranking_df is None or ranking_df.empty:
                st.warning("ランキングデータが取得できませんでした。")
            else:
                st.success(f"ランキング取得成功：{len(ranking_df)} 件")
                st.dataframe(ranking_df.head(100))
