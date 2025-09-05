import streamlit as st
import requests
import pandas as pd
from datetime import datetime
import math

st.set_page_config(page_title="SHOWROOM イベント＆ランキング確認ツール", layout="wide")

st.title("SHOWROOM イベント確認テスト")

# ---------------------------------
# 共通: 安全な GET（ヘッダー付き & タイムアウト & 例外吸収）
# ---------------------------------
DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "ja,en;q=0.9",
    # Referer は必要に応じて動的に足す
}

def safe_get(url: str, headers: dict = None, timeout: int = 20):
    try:
        h = dict(DEFAULT_HEADERS)
        if headers:
            h.update(headers)
        resp = requests.get(url, headers=h, timeout=timeout)
        return resp
    except requests.RequestException as e:
        return None

# ---------------------------------
# イベント一覧取得（公開 API）
# show_status:
#   1 = 開催中, 2 = 開始前, 3 = 終了, 0 = 指定なし（全部）
# ---------------------------------
def fetch_events(pages: int, show_status: int):
    all_events = []
    for p in range(1, pages + 1):
        url = f"https://www.showroom-live.com/api/event/search?page={p}"
        if show_status in (0, 1, 2, 3):
            url += f"&show_status={show_status}"
        resp = safe_get(url)
        if resp is None:
            st.warning(f"ページ {p} の取得でネットワーク例外が発生しました。")
            continue
        if resp.status_code != 200:
            st.warning(f"ページ {p} の取得で HTTP {resp.status_code} が返りました。")
            continue
        try:
            j = resp.json()
        except ValueError:
            st.warning(f"ページ {p} は JSON ではありませんでした。先頭 200 文字: {resp.text[:200]}")
            continue

        event_list = j.get("event_list", [])
        st.write(f"ページ {p} 取得件数: {len(event_list)}")
        all_events.extend(event_list)
    return all_events

# ---------------------------------
# ランキング取得（堅牢化）
# - レスポンスのキー差異に対応
# - ページング対応
# - 失敗時は詳細を警告表示
# ---------------------------------
def extract_ranking_rows(j: dict):
    """
    返ってきた JSON からランキング配列を取り出す。
    代表的なキーを総当たりで探し、見つかったリストを返す。
    """
    if isinstance(j, list):
        return j

    candidate_keys = [
        "ranking", "rankings", "ranking_list", "list",
        "rooms", "room_list", "data", "items"
    ]
    for k in candidate_keys:
        v = j.get(k)
        if isinstance(v, list):
            return v
    # JSON 直下に次のような構造がある可能性に一応対応
    for v in j.values():
        if isinstance(v, list) and len(v) > 0 and isinstance(v[0], dict) and ("rank" in v[0] or "point" in v[0]):
            return v
    return []

def normalize_ranking_df(rows: list):
    """
    ランキング行配列を DataFrame に正規化し、汎用カラムに寄せる。
    存在しないカラムは可能な限り補完。最終的に rank, room_name, point, room_id を持つ。
    """
    if not rows:
        return pd.DataFrame()

    df_raw = pd.json_normalize(rows)

    # 候補から最初に見つかったものを採用
    def pick(cols):
        for c in cols:
            if c in df_raw.columns:
                return c
        return None

    col_rank = pick(["rank", "rnk", "order_no", "ranking"])
    col_point = pick(["point", "score", "event_point", "score_point", "pt"])
    col_room_name = pick(["room_name", "name", "main_name", "room.main_name"])
    col_room_id = pick(["room_id", "id", "room_id.0", "room.id"])

    # 無ければ作る（NaN→0/空）
    if col_rank is None:
        df_raw["rank"] = range(1, len(df_raw) + 1)
        col_rank = "rank"
    if col_point is None:
        df_raw["point"] = 0
        col_point = "point"
    if col_room_name is None:
        df_raw["room_name"] = ""
        col_room_name = "room_name"
    if col_room_id is None:
        df_raw["room_id"] = pd.NA
        col_room_id = "room_id"

    df = df_raw[[col_rank, col_room_name, col_point, col_room_id]].copy()
    df.columns = ["rank", "room_name", "point", "room_id"]

    # 型整形
    with pd.option_context("mode.chained_assignment", None):
        df["rank"] = pd.to_numeric(df["rank"], errors="coerce").fillna(0).astype(int)
        df["point"] = pd.to_numeric(df["point"], errors="coerce").fillna(0).astype(int)
        df["room_name"] = df["room_name"].astype(str)

    df = df.sort_values(["rank", "room_name"]).reset_index(drop=True)
    return df

def fetch_ranking(event_id: int, event_url_key: str = "", max_pages: int = 10):
    """
    代表的なランキング API を試し、取れたものを採用。
    取得できたページまで結合して返す。
    """
    base_candidates = [
        f"https://www.showroom-live.com/api/event/ranking?event_id={event_id}&page={{page}}",
        # 予備候補（環境差異用。存在しない場合もある）
        f"https://www.showroom-live.com/api/event/rank_list?event_id={event_id}&page={{page}}",
        f"https://www.showroom-live.com/api/event/room_ranking?event_id={event_id}&page={{page}}",
    ]

    referer = {}
    if event_url_key:
        referer = {"Referer": f"https://www.showroom-live.com/event/{event_url_key}"}

    collected = []
    last_err = ""

    for base in base_candidates:
        collected.clear()
        last_err = ""
        for page in range(1, max_pages + 1):
            url = base.format(page=page)
            resp = safe_get(url, headers=referer)
            if resp is None:
                last_err = f"{url} の取得でネットワーク例外が発生しました。"
                break

            if resp.status_code != 200:
                # 先頭だけ覗く
                tail = resp.text[:180] if resp.text else ""
                last_err = f"HTTP {resp.status_code} / {url}\nレスポンス冒頭: {tail}"
                # 別の候補 URL を試すため break
                collected = []
                break

            try:
                j = resp.json()
            except ValueError:
                last_err = f"JSON デコード失敗 / {url}\nレスポンス冒頭: {resp.text[:180]}"
                collected = []
                break

            rows = extract_ranking_rows(j)
            if not rows:
                # ページ 1 から空なら、この候補は不適合
                if page == 1:
                    last_err = f"ランキング配列が見つかりませんでした / {url}\nJSON のキー: {list(j.keys()) if isinstance(j, dict) else type(j)}"
                    collected = []
                # 2 ページ目以降で空=ページング終端
                break

            collected.extend(rows)

            # 次ページが無さそうなら終了（簡易: 30件未満 or 次ページキーが無い等）
            # 件数が 30 固定と限らないので、次が空になるまで回す形にしている。
            # ここでは上限 max_pages で打ち切り。
        if collected:
            # 何かしら取れた候補があれば採用
            break

    if not collected:
        return pd.DataFrame(), last_err

    df = normalize_ranking_df(collected)
    return df, ""

# ---------------------------------
# 画面
# ---------------------------------
col1, col2 = st.columns([3, 2])

with col1:
    st.subheader("イベント取得")
    pages = st.number_input("取得するページ数", min_value=1, max_value=20, value=3, step=1)
    status_option = st.selectbox(
        "イベント種類を選択",
        options=[("開催中", 1), ("開始前", 2), ("終了", 3), ("終了含む(全部)", 0)],
        index=0,
        format_func=lambda x: x[0]
    )
    show_status = status_option[1]

    if st.button("イベント一覧を取得"):
        events = fetch_events(pages, show_status)
        if not events:
            st.warning("取得できるイベントがありませんでした。")
        else:
            st.success(f"合計 {len(events)} 件のイベントを取得しました！")

            # 表示用に整形（存在する列だけ使う）
            df_events = pd.DataFrame(events)

            # UNIX 秒 → 日時
            def to_dt(col):
                if col in df_events.columns:
                    df_events[col] = pd.to_datetime(df_events[col], unit="s", utc=True).dt.tz_convert("Asia/Tokyo").dt.strftime("%Y-%m-%d %H:%M")

            to_dt("started_at")
            to_dt("ended_at")
            # 表示列（存在チェック込み）
            show_cols = [c for c in ["event_id", "event_name", "event_url_key", "type_name", "started_at", "ended_at", "show_ranking"] if c in df_events.columns]
            st.dataframe(df_events[show_cols], use_container_width=True)

            # 選択してランキング取得
            st.markdown("---")
            st.subheader("詳細を表示するイベントを選択してください")
            # 選択肢: (ラベル, 実体)
            options = [(f"{e.get('event_name','(名称不明)')}", e) for e in events]
            selected = st.selectbox("イベントを選択", options=options, format_func=lambda x: x[0])
            event = selected[1] if isinstance(selected, tuple) else selected
            event_id = int(event.get("event_id", 0))
            event_key = event.get("event_url_key", "")

            st.write(f"選択したイベントID：{event_id}")

            if event_id:
                # ランキング取得
                df_rank, err = fetch_ranking(event_id, event_key, max_pages=10)
                if err:
                    st.warning("ランキングの取得に失敗しました。\n\n" + err)
                elif df_rank.empty:
                    st.warning("ランキングを取得できませんでした。")
                else:
                    st.success(f"ランキングを {len(df_rank)} 件取得しました。")
                    st.dataframe(df_rank, use_container_width=True)

                    # ちょい可視化（上位のポイント分布）
                    top_n = min(50, len(df_rank))
                    st.markdown(f"**上位 {top_n} 名のポイント分布**")
                    top_df = df_rank.head(top_n)
                    st.bar_chart(top_df.set_index("rank")["point"])
