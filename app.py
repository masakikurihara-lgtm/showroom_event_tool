import streamlit as st
import requests
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="SHOWROOM イベント確認ツール", layout="wide")
st.title("SHOWROOM イベント確認ツール")

# セッションステート初期化
if 'all_events' not in st.session_state:
    st.session_state.all_events = []
if 'selected_event_id' not in st.session_state:
    st.session_state.selected_event_id = None
if 'ranking_df' not in st.session_state:
    st.session_state.ranking_df = pd.DataFrame()

# ページ数選択
page_count = st.number_input("取得するページ数", min_value=1, max_value=50, value=5, step=1)

# イベント種類選択
event_type_map = {"終了含む": 0, "開催中": 1}
event_type_choice = st.selectbox("イベント種類を選択", list(event_type_map.items()))
event_type_value = event_type_choice[1]

# データ取得ボタン
if st.button("イベント取得"):
    st.info("イベント取得中...")
    all_events = []
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
        st.session_state.all_events = []
    else:
        st.success(f"合計 {len(all_events)} 件のイベントを取得しました！")
        st.session_state.all_events = all_events

# イベントが取得済みの場合
if st.session_state.all_events:
    df_events = pd.DataFrame(st.session_state.all_events)

    # 表示用 DataFrame
    df_display = df_events[['event_id','event_name','started_at','ended_at','type_name','event_url_key']].copy()
    df_display['開始日時'] = pd.to_datetime(df_display['started_at'], unit='s')
    df_display['終了日時'] = pd.to_datetime(df_display['ended_at'], unit='s')

    st.dataframe(df_display[['event_name','開始日時','終了日時','type_name']])

    # イベント選択
    selected_event_idx = st.selectbox("詳細を表示するイベントを選択してください", df_display.index, index=0)
    selected_event = df_display.loc[selected_event_idx]

    # 選択イベントIDをセッションステートに保持
    if st.session_state.selected_event_id != selected_event['event_id']:
        st.session_state.selected_event_id = selected_event['event_id']
        st.session_state.ranking_df = pd.DataFrame()  # 新しいイベントを選んだらランキングを初期化

    st.write(f"選択したイベントID：{selected_event['event_id']}")
    st.write(f"event_url_key：{selected_event['event_url_key']}")

    # ---------- ランキング取得関数 ----------
    def fetch_ranking(event_id, event_url_key, max_pages=5):
        all_data = []
        base_candidates = [
            f"https://www.showroom-live.com/api/event/ranking?event_id={event_id}&page={{page}}",
            f"https://www.showroom-live.com/api/event/rank_list?event_id={event_id}&page={{page}}",
            f"https://www.showroom-live.com/api/event/room_ranking?event_id={event_id}&page={{page}}",
        ]
        if event_url_key:
            base_candidates.append(
                f"https://www.showroom-live.com/api/event/{event_url_key}/ranking?page={{page}}"
            )

        success = False
        for base_url in base_candidates:
            for page in range(1, max_pages + 1):
                url = base_url.format(page=page)
                try:
                    res = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
                    if res.status_code != 200:
                        break
                    data = res.json()
                    if "ranking" in data:
                        page_data = data["ranking"]
                    elif "list" in data:
                        page_data = data["list"]
                    else:
                        break
                    if not page_data:
                        break
                    all_data.extend(page_data)
                    success = True
                except:
                    continue
            if success:
                break
        if not success or not all_data:
            return None
        return pd.DataFrame(all_data)

    # ---------- ランキング取得ボタン ----------
    if st.button("ランキング取得") or not st.session_state.ranking_df.empty:
        if st.session_state.ranking_df.empty:
            ranking_df = fetch_ranking(selected_event['event_id'], selected_event['event_url_key'])
            if ranking_df is not None:
                st.session_state.ranking_df = ranking_df
            else:
                st.warning("ランキングの取得に失敗しました。")
        else:
            ranking_df = st.session_state.ranking_df

        # ランキング表示
        if not st.session_state.ranking_df.empty:
            ranking_df = st.session_state.ranking_df
            df_copy = ranking_df.copy()
            display_cols = []

            if 'rank' in df_copy.columns:
                df_copy = df_copy.rename(columns={'rank':'順位'})
                display_cols.append('順位')
            if 'user_name' in df_copy.columns:
                df_copy = df_copy.rename(columns={'user_name':'ユーザー名'})
                display_cols.append('ユーザー名')
            if 'point' in df_copy.columns:
                df_copy = df_copy.rename(columns={'point':'獲得ポイント'})
                display_cols.append('獲得ポイント')

            if display_cols:
                st.dataframe(df_copy[display_cols].head(100))
            else:
                st.warning("表示できる列がありません。")
