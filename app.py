# app.py
import streamlit as st
import requests
import pandas as pd
from datetime import datetime
import time

st.set_page_config(page_title="SHOWROOM イベント確認ツール", layout="wide")
st.title("SHOWROOM イベント確認ツール")

# -----------------------
# ヘルパー関数
# -----------------------
HEADERS = {"User-Agent": "Mozilla/5.0"}

def fetch_events_pages(page_count: int, include_ended: int = 1):
    """ /api/event/search を複数ページ呼んで event_list を集める """
    events = []
    for page in range(1, page_count + 1):
        url = f"https://www.showroom-live.com/api/event/search?page={page}&include_ended={include_ended}"
        try:
            r = requests.get(url, headers=HEADERS, timeout=10)
            r.raise_for_status()
            j = r.json()
            page_events = j.get("event_list", [])
            events.extend(page_events)
            st.write(f"ページ {page} 取得件数: {len(page_events)}")
        except Exception as e:
            st.error(f"ページ {page} 取得中にエラー: {e}")
            # 続行（失敗ページはスキップ）
    return events

def _detect_ranking_list_in_json(j):
    """
    JSON の中から「ランキング配列らしきもの」を探す（最初に見つかった list[dict] を返す）。
    要素が dict で、その中に 'rank' or 'point' などのキーを持っていれば有力とみなす。
    """
    if isinstance(j, dict):
        for k, v in j.items():
            if isinstance(v, list) and v and isinstance(v[0], dict):
                # 要素に 'rank' / 'point' / 'room_id' / 'room_name' などを含むか確認
                element_keys = set(v[0].keys())
                if element_keys & {"rank", "point", "points", "room_id", "room_name", "user_name", "name"}:
                    return v, k
                # それらのキーが無くても list[dict] を返して良いこともある（慎重に）
                # ただし空っぽのリストはスキップ
        # 二重ネストなどもチェック（辞書の中の辞書）
    return None, None

def fetch_ranking_candidates(event_id: int, event_url_key: str = None, max_pages=5):
    """
    複数の候補エンドポイントを順に試し、ページを取得して結合した DataFrame を返す。
    返り値: (df or None, meta) meta は試行した endpoint リストや last_status などの辞書
    """
    base_candidates = [
        "https://www.showroom-live.com/api/event/ranking?event_id={event_id}&page={page}",
        "https://www.showroom-live.com/api/event/rank_list?event_id={event_id}&page={page}",
        "https://www.showroom-live.com/api/event/room_ranking?event_id={event_id}&page={page}",
    ]
    if event_url_key:
        # event_url_key を使ったエンドポイント候補
        base_candidates.extend([
            f"https://www.showroom-live.com/api/event/{event_url_key}/ranking?page={{page}}",
            f"https://www.showroom-live.com/api/event/{event_url_key}/room_ranking?page={{page}}",
            f"https://www.showroom-live.com/api/event/{event_url_key}/rank_list?page={{page}}",
        ])

    tried = []
    last_resp_sample = None

    for base in base_candidates:
        all_items = []
        success_any = False
        for page in range(1, max_pages + 1):
            url = base.format(event_id=event_id, page=page)
            tried.append(url)
            try:
                r = requests.get(url, headers=HEADERS, timeout=10)
                # ステータスが 200 以外（404 等）はページ終了の合図として break する場合がある
                if r.status_code != 200:
                    last_resp_sample = (url, r.status_code, r.text[:400])
                    break
                j = r.json()
                page_items, found_key = _detect_ranking_list_in_json(j)
                # もし直接配列が返ってくる形式（トップレベルが list）ならそれも扱う
                if isinstance(j, list) and j and isinstance(j[0], dict):
                    page_items = j
                    found_key = None

                if not page_items:  # ページ内にランキングがなければループ終了
                    # ただし空リスト（ランキングが終了）ならループ終了
                    # もし page==1 かつ空ならそもそもこのエンドポイントは向いてない可能性
                    if page == 1:
                        # この base は向いてない可能性。 break out and try next base.
                        last_resp_sample = (url, r.status_code, r.text[:400])
                        all_items = []  # 念のためクリア
                    break
                # 追加
                all_items.extend(page_items)
                success_any = True
                # 次ページを試す（ページの空になるタイミングで break する）
            except Exception as e:
                last_resp_sample = (url, "exception", str(e)[:400])
                break

            # 連続アクセスを控える
            time.sleep(0.08)

        if success_any and all_items:
            # DataFrame にして返す
            df = pd.DataFrame(all_items)
            meta = {
                "used_base": base,
                "tried_urls": tried,
                "last_resp_sample": last_resp_sample
            }
            return df, meta

    # どれもダメだった
    meta = {"used_base": None, "tried_urls": tried, "last_resp_sample": last_resp_sample}
    return None, meta

def normalize_ranking_df(df: pd.DataFrame):
    """
    取得したランキング DataFrame の列名がまちまちなので、
    '順位','ユーザー名','獲得ポイント' にマッピングして返す（可能な限り）。
    """
    cols = df.columns.tolist()
    colmap = {}

    # 順位カラム
    for candidate in ["rank", "順位", "position", "no", "ranking"]:
        if candidate in cols:
            colmap[candidate] = "順位"
            break

    # ユーザー名カラム（API により 'room_name' や 'user_name' など）
    for candidate in ["user_name", "room_name", "name", "display_name", "user"]:
        if candidate in cols:
            colmap[candidate] = "ユーザー名"
            break

    # ポイントカラム
    for candidate in ["point", "points", "score", "value"]:
        if candidate in cols:
            colmap[candidate] = "獲得ポイント"
            break

    # room_id など（あれば保持）
    if "room_id" in cols and "room_id" not in colmap:
        colmap["room_id"] = "room_id"

    # apply renaming
    if colmap:
        df = df.rename(columns=colmap)

    # 保持しておく主要列が無ければ追加して安全化
    if "順位" not in df.columns:
        # try to infer from index or create sequential ranks
        df["順位"] = df.index + 1
    if "獲得ポイント" not in df.columns:
        # 0で埋める
        df["獲得ポイント"] = 0
    if "ユーザー名" not in df.columns:
        # 可能なら room_name 代替、無ければ room_id
        if "room_id" in df.columns:
            df["ユーザー名"] = df["room_id"].astype(str)
        else:
            df["ユーザー名"] = ""

    # 順位を numeric にしてソート
    try:
        df["順位"] = pd.to_numeric(df["順位"], errors="coerce").fillna(method="ffill").astype(int)
    except:
        pass

    # 降順（順位1が上）にソートし、重複排除
    df = df.sort_values("順位").reset_index(drop=True)
    return df

# -----------------------
# UI: イベント取得
# -----------------------
col1, col2 = st.columns([2, 1])
with col1:
    page_count = st.number_input("取得するページ数", min_value=1, max_value=50, value=3, step=1)
with col2:
    include_ended_choice = st.selectbox("イベント種類を選択", ("開催中のみ", "終了含む"))
include_ended = 1 if include_ended_choice == "開催中のみ" else 0

if "events" not in st.session_state:
    st.session_state.events = None
if "events_df" not in st.session_state:
    st.session_state.events_df = None
if "ranking_df" not in st.session_state:
    st.session_state.ranking_df = None
if "ranking_meta" not in st.session_state:
    st.session_state.ranking_meta = None

if st.button("イベント取得"):
    st.info("イベント取得中...")
    events = fetch_events_pages(page_count, include_ended=1 if include_ended_choice=="開催中" or include_ended_choice=="開催中のみ" else 0)
    if not events:
        st.warning("取得できるイベントがありませんでした。")
        st.session_state.events = []
        st.session_state.events_df = None
    else:
        st.success(f"合計 {len(events)} 件のイベントを取得しました！")
        st.session_state.events = events
        df_events = pd.DataFrame(events)
        st.session_state.events_df = df_events

# -----------------------
# イベント一覧表示と選択
# -----------------------
if st.session_state.events_df is not None:
    df_events = st.session_state.events_df
    # 表示カラムを安全に選ぶ（存在しないとエラーになるため try）
    display_cols = []
    for c in ["event_id", "event_name", "started_at", "ended_at", "type_name", "event_url_key"]:
        if c in df_events.columns:
            display_cols.append(c)
    df_display = df_events[display_cols].copy()
    # 日付変換（あれば）
    if "started_at" in df_display.columns:
        df_display["開始日時"] = pd.to_datetime(df_display["started_at"], unit="s")
    if "ended_at" in df_display.columns:
        df_display["終了日時"] = pd.to_datetime(df_display["ended_at"], unit="s")

    st.markdown("**取得したイベント一覧（クリックで選択）**")
    # 使いやすい選択肢を作る
    df_display["choice_label"] = df_display.apply(
        lambda r: f'{r.get("event_name","(no name)")}  (id:{r.get("event_id")})', axis=1
    )
    choice = st.selectbox("詳細を表示するイベントを選択してください", options=df_display.index, format_func=lambda i: df_display.loc[i, "choice_label"])

    selected_event = df_display.loc[choice]
    st.write(f"選択されたイベントID: {selected_event.get('event_id')}")
    st.write(f"event_url_key：{selected_event.get('event_url_key', '')}")

    # -----------------------
    # ランキング取得ボタン
    # -----------------------
    if st.button("ランキング取得"):
        st.info("ランキング取得中...")
        event_id = selected_event["event_id"]
        event_url_key = selected_event.get("event_url_key", None)
        ranking_df, meta = fetch_ranking_candidates(event_id=event_id, event_url_key=event_url_key, max_pages=10)
        if ranking_df is None or ranking_df.empty:
            st.error("ランキング取得に失敗しました。")
            # デバッグ情報を表示
            st.write("試行した URL の一部（最新）:", meta.get("tried_urls", [])[-6:])
            if meta.get("last_resp_sample"):
                st.write("最後に受け取ったレスポンスサンプル:", meta.get("last_resp_sample"))
            st.session_state.ranking_df = None
            st.session_state.ranking_meta = meta
        else:
            st.success(f"ランキング取得成功：{len(ranking_df)} 件")
            norm_df = normalize_ranking_df(ranking_df)
            st.session_state.ranking_df = norm_df
            st.session_state.ranking_meta = meta

# -----------------------
# 取得結果の表示（永続化）
# -----------------------
if st.session_state.ranking_df is not None:
    df = st.session_state.ranking_df.copy()
    meta = st.session_state.ranking_meta or {}
    st.markdown("**ランキング（取得済）**")
    # デバッグ：利用したエンドポイント
    st.caption(f"使用した候補（最後に成功した base）: {meta.get('used_base')}")
    # 表示可能な列を自動で選ぶ
    show_cols = []
    for col in ["順位", "ユーザー名", "獲得ポイント"]:
        if col in df.columns:
            show_cols.append(col)
    if not show_cols:
        st.warning("取得データに表示可能な列が見つかりませんでした。生データのカラムを確認してください。")
        st.write("取得した生データの列:", df.columns.tolist())
        st.dataframe(df.head(50))
    else:
        # 上位100件を表示
        st.dataframe(df[show_cols].head(100), use_container_width=True)

    # 簡易グラフ（ポイントがあれば）
    if "獲得ポイント" in df.columns:
        st.subheader("獲得ポイント（上位20）")
        try:
            top20 = df.sort_values("順位").head(20)
            st.bar_chart(top20.set_index("ユーザー名")["獲得ポイント"])
        except Exception as e:
            st.write("グラフ作成でエラー:", e)

    # 保存しておきたい場合のためにデバッグ情報
    if st.button("取得した生データのカラムを表示"):
        st.write(df.columns.tolist())
    if st.button("デバッグ: 試行URL一覧（最新20）"):
        st.write(meta.get("tried_urls", [])[-20:])

