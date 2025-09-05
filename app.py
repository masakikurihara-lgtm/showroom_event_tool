import streamlit as st
import requests
import pandas as pd
import altair as alt
from datetime import datetime
import time

# ページ設定
st.set_page_config(page_title="SHOWROOM イベント分析ツール", layout="wide")

# タイトル
st.markdown(
    "<h1 style='text-align:center; color:#1f2937;'>SHOWROOM イベント分析ツール</h1>",
    unsafe_allow_html=True
)

# 説明文
st.markdown(
    "<p style='text-align:center; color:#4b5563;'>"
    "対象のイベントIDを入力すると、参加者の順位や獲得ポイントの推移をグラフで確認できます。"
    "</p>",
    unsafe_allow_html=True
)

st.markdown("---")

# イベントID入力
event_id = st.text_input("対象のイベントIDを入力してください（例：12345）", value="")

# 実行ボタン
start_button = st.button("データ取得 & グラフ表示")

if start_button:
    if not event_id:
        st.warning("イベントIDを入力してください。")
    else:
        st.info(f"イベント {event_id} のデータを取得します…")

        # ダミーデータ取得（実際はSHOWROOM APIを使用）
        # ここではサンプルとしてランダム生成
        participants = ['UserA', 'UserB', 'UserC', 'UserD']
        dates = pd.date_range(start='2025-09-01', periods=7)
        data = []
        import random
        for user in participants:
            points = 0
            for date in dates:
                points += random.randint(100, 500)  # 累積ポイント
                data.append({'ユーザー名': user, '日付': date, '累積ポイント': points})

        df = pd.DataFrame(data)

        st.markdown("### ポイント推移（累積）")
        # ラインチャート
        chart = alt.Chart(df).mark_line(point=True).encode(
            x='日付:T',
            y='累積ポイント:Q',
            color='ユーザー名:N',
            tooltip=['ユーザー名', '日付', '累積ポイント']
        ).interactive()

        st.altair_chart(chart, use_container_width=True)

        # ランキング表示
        latest_points = df[df['日付'] == df['日付'].max()]
        ranking = latest_points.sort_values(by='累積ポイント', ascending=False).reset_index(drop=True)
        ranking['順位'] = ranking.index + 1
        st.markdown("### 最新ポイントランキング")
        st.table(ranking[['順位', 'ユーザー名', '累積ポイント']])
