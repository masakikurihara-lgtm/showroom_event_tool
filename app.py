import streamlit as st
import pandas as pd
import requests

st.set_page_config(page_title="Showroom Event Tracker", layout="wide")
st.title("SHOWROOM イベント確認ツール")

# --- イベント一覧取得 ---
try:
    events = requests.get("https://www.showroom-live.com/api/event/ongoing").json()
    # レスポンスがリスト形式
    event_options = {e.get("event_name"): (e.get("event_id"), e.get("event_url_key")) for e in events}
except Exception as e:
    st.error(f"イベント一覧の取得に失敗しました: {e}")
    events = []
    event_options = {}

if events:
    # --- イベント選択 ---
    event_name = st.selectbox("表示対象のイベントを選択", list(event_options.keys()))

    if event_name:
        selected_event_id, selected_event_key = event_options[event_name]
        st.write(f"選択されたイベントID: {selected_event_id}")
        st.write(f"event_url_key: {selected_event_key}")

        # --- ランキング取得 ---
        ranking_url = f"https://www.showroom-live.com/api/event/{selected_event_key}/ranking?page=1"

        try:
            ranking_data = requests.get(ranking_url).json()

            # レスポンスの中に "ranking" キーがあるか確認
            if isinstance(ranking_data, dict) and "ranking" in ranking_data:
                df = pd.DataFrame([
                    {
                        "順位": r.get("rank"),
                        "ユーザー名": r.get("room_name"),
                        "獲得ポイント": r.get("point"),
                        "room_id": r.get("room_id"),
                    }
                    for r in ranking_data["ranking"]
                ])
                st.success(f"ランキング取得成功：{len(df)} 件")
                st.dataframe(df)
            else:
                st.error("ランキングデータが見つかりません")
                st.json(ranking_data)  # デバッグ用にAPIレスポンスを確認
        except Exception as e:
            st.error(f"ランキング取得に失敗しました: {e}")
