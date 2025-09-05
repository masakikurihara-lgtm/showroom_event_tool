import streamlit as st
import requests
import pandas as pd
from datetime import datetime
import altair as alt
import time

st.set_page_config(page_title="SHOWROOM イベント確認ツール", layout="wide")
st.title("SHOWROOM イベント確認ツール")

# セッションステート初期化
if 'ranking_df' not in st.session_state:
    st.session_state.ranking_df = pd.DataFrame()

# ページ数選択
page_count = st.number_input("取得するページ数", min_value=1, max_value=50, value=5, step=1)

# イベント種類選択
event_type_map = {
    "終了含む": 0,
    "開催中": 1
}
event_type_choice = st.selectbox("イベント種類を選択", list(event_type_map.items()))
event_type_value = event_type_choice[1]

# ---------- イベント取得 ----------
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

        # DataFrame化
        df_events = pd.DataFrame(all_events)
        st.write("取得したデータのカラム一覧:")
        st.json(list(df_events.columns))

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
            if not success:
                return None
            return pd.DataFrame(all_data)

        # ---------- ランキング取得 ----------
        st.info("ランキング取得中...")
        ranking_df = fetch_ranking(selected_event['event_id'], selected_event['event_url_key'])
        if ranking_df is None or ranking_df.empty:
            st.error("ランキングの取得に失敗しました。")
        else:
            st.session_state.ranking_df = ranking_df
            st.success(f"ランキング取得成功：{len(ranking_df)} 件")

            # 列名整形
            display_cols = []
            df_copy = ranking_df.copy()
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

            # ---------- ポイント推移グラフ ----------
            st.subheader("ポイント推移グラフ")
            df_chart = df_copy.copy()
            df_chart['取得日時'] = datetime.now()
            if 'ユーザー名' in df_chart.columns and '獲得ポイント' in df_chart.columns:
                chart = alt.Chart(df_chart).mark_line(point=True).encode(
                    x='取得日時:T',
                    y='獲得ポイント:Q',
                    color='ユーザー名:N',
                    tooltip=['ユーザー名','獲得ポイント','取得日時']
                ).interactive()
                st.altair_chart(chart, use_container_width=True)
            else:
                st.warning("グラフにする列がありません。")
