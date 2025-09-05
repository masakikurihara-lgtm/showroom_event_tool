import streamlit as st
import requests
import pandas as pd
import matplotlib.pyplot as plt

st.set_page_config(page_title="SHOWROOM イベント分析ツール", layout="wide")
st.title("SHOWROOM イベント分析ツール")

# -----------------------------
# イベント一覧取得
# -----------------------------
page = 1
events_list = []

while True:
    url = f"https://www.showroom-live.com/api/event/search?page={page}"
    resp = requests.get(url)
    if resp.status_code != 200:
        st.error("イベント一覧の取得に失敗しました")
        st.stop()
    
    data = resp.json()
    events = data.get("events", [])
    if not events:
        break
    
    events_list.extend(events)
    page += 1

events_df = pd.DataFrame(events_list)
if events_df.empty:
    st.warning("取得できるイベントがありませんでした。")
    st.stop()

# 表示用ラベル
events_df['label'] = events_df['event_name'] + " (" + events_df['start_date'] + "〜" + events_df['end_date'] + ")"

# -----------------------------
# イベント選択
# -----------------------------
selected_event_id = st.selectbox(
    "分析したいイベントを選択",
    options=events_df['event_id'],
    format_func=lambda x: events_df.loc[events_df['event_id']==x, 'label'].values[0]
)

selected_event_info = events_df.loc[events_df['event_id']==selected_event_id].iloc[0]
st.markdown(f"### 選択イベント: {selected_event_info['event_name']}")

# -----------------------------
# ランキング取得例（サンプル）
# -----------------------------
# 注意: 実際のランキングAPIのURLはSHOWROOMの非公開API仕様により確認が必要です
ranking_api_url = f"https://www.showroom-live.com/api/event/ranking?event_id={selected_event_id}&page=1"
resp = requests.get(ranking_api_url)

if resp.status_code == 200:
    ranking_data = resp.json().get("ranking", [])
    if ranking_data:
        ranking_df = pd.DataFrame(ranking_data)
        st.write("ランキング（上位10名）")
        st.dataframe(ranking_df.head(10))
        
        # 獲得ポイント推移のサンプルグラフ
        # ここではランダム生成データでサンプル表示
        import numpy as np
        ranking_df['sample_points'] = np.random.randint(1000, 5000, size=len(ranking_df))
        plt.figure(figsize=(8,4))
        plt.bar(ranking_df['user_name'].head(10), ranking_df['sample_points'].head(10))
        plt.xticks(rotation=45, ha='right')
        plt.ylabel("獲得ポイント（サンプル）")
        plt.title("上位10名のポイント推移（サンプル）")
        st.pyplot(plt)
    else:
        st.warning("ランキングデータがありませんでした。")
else:
    st.error("ランキングデータの取得に失敗しました。")
