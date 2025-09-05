import json
import pandas as pd
import plotly.express as px
from datetime import datetime

# -----------------------------
# 1. JSONデータ読み込み（例）
# -----------------------------
# 例としてのJSON構造：
# [
#   {"timestamp": "2025-09-06 12:00", "participants": [
#       {"id": "user1", "name": "ライバーA", "rank": 1, "points": 1500},
#       {"id": "user2", "name": "ライバーB", "rank": 2, "points": 1200}
#   ]},
#   {"timestamp": "2025-09-06 13:00", "participants": [...]} 
# ]

with open('event_data.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# -----------------------------
# 2. データ整形
# -----------------------------
rows = []
for record in data:
    timestamp = datetime.strptime(record['timestamp'], '%Y-%m-%d %H:%M')
    for p in record['participants']:
        rows.append({
            'timestamp': timestamp,
            'id': p['id'],
            'name': p['name'],
            'rank': p['rank'],
            'points': p['points']
        })

df = pd.DataFrame(rows)

# -----------------------------
# 3. CSV出力
# -----------------------------
df.to_csv('event_data_output.csv', index=False, encoding='utf-8-sig')

# -----------------------------
# 4. 順位推移グラフ
# -----------------------------
fig_rank = px.line(df, x='timestamp', y='rank', color='name', markers=True,
                   title='順位推移グラフ', labels={'rank': '順位', 'timestamp': '時刻'})
fig_rank.update_yaxes(autorange="reversed")  # 順位1位を上に
fig_rank.show()

# -----------------------------
# 5. ポイント推移グラフ
# -----------------------------
fig_points = px.line(df, x='timestamp', y='points', color='name', markers=True,
                     title='ポイント推移グラフ', labels={'points': 'ポイント', 'timestamp': '時刻'})
fig_points.show()
