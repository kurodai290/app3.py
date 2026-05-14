import streamlit as st
import pandas as pd

st.set_page_config(page_title="てんびん - ♦K", page_icon="⚖️")

# --- セッション状態の初期化 ---
if 'game_active' not in st.session_state:
    st.session_state.update({
        'game_active': False,
        'players': [],
        'round': 1,
        'submitted_count': 0,
        'current_inputs': {},
        'show_results': False,
        'last_summary': None
    })

def start_game(names):
    st.session_state.players = [{"name": name.strip(), "points": 0, "is_active": True} for name in names if name.strip()]
    st.session_state.game_active = True
    st.session_state.round = 1
    st.session_state.current_inputs = {}
    st.session_state.submitted_count = 0
    st.session_state.show_results = False

# --- メインUI ---
st.title("⚖️ てんびん - ♦K")

if not st.session_state.game_active:
    st.subheader("参戦者の登録")
    player_names = st.text_area("参戦者の名前を改行して入力してください", "プレイヤー1\nプレイヤー2\nプレイヤー3\nプレイヤー4")
    if st.button("均衡を開始する"):
        start_game(player_names.split('\n'))
        st.rerun()

else:
    # スコアボード
    st.sidebar.header("⚖️ 均衡の秤")
    for p in st.session_state.players:
        if not p['is_active']:
            color, status = "gray", "💀 脱落"
        elif p['points'] <= -4:
            color, status = "red", "⚠️ 均衡の危機"
        else:
            color, status = "blue", "✅ 均衡を維持"
        
        st.sidebar.markdown(f"### :{color}[{p['name']}]\n**均衡点: {p['points']} pt**\n{status}")
        st.sidebar.progress(max(0, 5 + p['points']) / 5)

    if st.sidebar.button("ゲームをリセット"):
        st.session_state.game_active = False
        st.rerun()

    active_players = [p for p in st.session_state.players if p['is_active']]
    
    if len(active_players) <= 1:
        st.balloons()
        winner = active_players[0]['name'] if active_players else "なし"
        st.error(f"🏁 審判終了。最後に残った勝者は **{winner}** です。")
        st.table(pd.DataFrame(st.session_state.players))
        if st.button("タイトルへ戻る"):
            st.session_state.game_active = False
            st.rerun()
            
    elif not st.session_state.show_results:
        st.subheader(f"第 {st.session_state.round} ラウンド")
        current_active_idx = st.session_state.submitted_count
        
        if current_active_idx < len(active_players):
            current_player = active_players[current_active_idx]["name"]
            st.info(f"⚖️ 思考中: **{current_player}** (他の人に見られないように入力してください)")
            # keyにラウンドとプレイヤー名を含めてリセットを防ぐ
            with st.form(key=f"input_form_{st.session_state.round}_{current_player}"):
                val = st.number_input(f"{current_player} の数値 (0〜100)", 0, 100, step=1, type="password", key=f"num_{st.session_state.round}_{current_player}")
                if st.form_submit_button("数値を確定"):
                    st.session_state.current_inputs[current_player] = val
                    st.session_state.submitted_count += 1
                    st.rerun()
        else:
            if st.button("全ての天秤が揃いました"):
                results = st.session_state.current_inputs
                vals = list(results.values())
                avg = sum(vals) / len(vals)
                target = avg * 0.8
                counts = {v: vals.count(v) for v in set(vals)}
                summary = []
                valid_entries = []

                # 被り判定
                for name, val in results.items():
                    p_ref = next(p for p in st.session_state.players if p["name"] == name)
                    if counts[val] > 1:
                        p_ref["points"] -= 2
                        summary.append({"名前": name, "数値": val, "判定": "💥 被り (-2)"})
                    else:
                        valid_entries.append({"name": name, "val": val, "player": p_ref})
                
                if valid_entries:
                    has_zero = any(d["val"] == 0 for d in valid_entries)
                    has_hundred = any(d["val"] == 100 for d in valid_entries)
                    
                    # 特殊ルール判定
                    # 1. 100 vs 0 (0がいる時に100がいれば100の勝ち)
                    if has_zero and has_hundred:
                        win_data = min([d for d in valid_entries if d["val"] == 100], key=lambda x: x['name'])
                    # 2. 0のルール (2人の時のみ有効。3人以上の時は0は最強ではない)
                    elif has_zero and len(active_players) == 2:
                        win_data = min([d for d in valid_entries if d["val"] == 0], key=lambda x: x['name'])
                    # 3. 通常ルール (ターゲットに一番近い)
                    else:
                        win_data = min(valid_entries, key=lambda x: abs(x["val"] - target))
                    
                    winner_name = win_data["name"]
                    for d in valid_entries:
                        if d["name"] == winner_name:
                            summary.append({"名前": d["name"], "数値": d["val"], "判定": "👑 勝利"})
                        else:
                            d["player"]["points"] -= 1
                            summary.append({"名前": d["name"], "数値": d["val"], "判定": "💀 敗北 (-1)"})
                
                for p in st.session_state.players:
                    if p["points"] <= -5: p["is_active"] = False
                
                st.session_state.last_summary = {"data": summary, "avg": avg, "target": target}
                st.session_state.show_results = True
                st.rerun()

    else:
        st.subheader(f"判定結果")
        s = st.session_state.last_summary
        st.markdown(f"### 🎯 ターゲット: **{s['target']:.2f}** (平均×0.8)")
        st.table(pd.DataFrame(s['data']))
        
        if st.button("次の審判へ"):
            st.session_state.round += 1
            st.session_state.submitted_count = 0
            st.session_state.current_inputs = {}
            st.session_state.show_results = False
            st.rerun()
