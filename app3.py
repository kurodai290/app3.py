import streamlit as st
import pandas as pd

st.set_page_config(page_title="0.8倍サバイバル", page_icon="⚖️")

# --- セッション状態の初期化 ---
if 'game_active' not in st.session_state:
    st.session_state.update({
        'game_active': False,
        'players': [],
        'round': 1,
        'submitted_count': 0,
        'current_inputs': {},
        'show_results': False, # 結果表示フラグを追加
        'last_summary': None    # 前回の計算結果を保存
    })

def start_game(names):
    st.session_state.players = [{"name": name.strip(), "points": 0, "is_active": True} for name in names if name.strip()]
    st.session_state.game_active = True
    st.session_state.round = 1
    st.session_state.current_inputs = {}
    st.session_state.submitted_count = 0
    st.session_state.show_results = False

# --- メインUI ---
st.title("⚖️ 0.8倍サバイバル：脱落戦")

if not st.session_state.game_active:
    st.subheader("プレイヤー登録")
    player_names = st.text_area("参加者の名前を改行して入力", "プレイヤー1\nプレイヤー2\nプレイヤー3")
    if st.button("ゲーム開始"):
        start_game(player_names.split('\n'))
        st.rerun()

else:
    # サイドバー：スコア
    st.sidebar.header("📊 スコアボード")
    for p in st.session_state.players:
        status = "✅ 生存" if p['is_active'] else "💀 脱落"
        color = "white" if p['is_active'] else "red"
        st.sidebar.markdown(f":{color}[{p['name']}: {p['points']} pt ({status})]")
    
    if st.sidebar.button("ゲームを終了"):
        st.session_state.game_active = False
        st.rerun()

    active_players = [p for p in st.session_state.players if p['is_active']]
    
    if len(active_players) <= 1:
        st.balloons()
        winner = active_players[0]['name'] if active_players else "なし"
        st.error(f"🏁 終焉！ 勝者は **{winner}** です！")
        if st.button("タイトルへ戻る"):
            st.session_state.game_active = False
            st.rerun()
            
    elif not st.session_state.show_results:
        st.subheader(f"第 {st.session_state.round} ラウンド")
        current_active_idx = st.session_state.submitted_count
        
        if current_active_idx < len(active_players):
            current_player = active_players[current_active_idx]["name"]
            with st.form(key=f"form_r{st.session_state.round}_{current_player}"):
                st.write(f"👉 **{current_player}** さんの番")
                val = st.number_input("0〜100の整数", 0, 100, step=1)
                if st.form_submit_button("確定"):
                    st.session_state.current_inputs[current_player] = val
                    st.session_state.submitted_count += 1
                    st.rerun()
        else:
            if st.button("結果を計算する"):
                # 計算ロジック
                results = st.session_state.current_inputs
                vals = list(results.values())
                avg = sum(vals) / len(vals)
                target = avg * 0.8
                counts = {v: vals.count(v) for v in set(vals)}
                summary = []
                valid_entries = []

                for name, val in results.items():
                    p_ref = next(p for p in st.session_state.players if p["name"] == name)
                    if counts[val] > 1:
                        p_ref["points"] -= 2
                        summary.append({"名前": name, "数値": val, "判定": "💥 被り(-2pt)"})
                    else:
                        valid_entries.append({"name": name, "val": val, "player": p_ref})
                
                if valid_entries:
                    has_zero = any(d["val"] == 0 for d in valid_entries)
                    has_hundred = any(d["val"] == 100 for d in valid_entries)
                    if has_zero and has_hundred:
                        win_data = min([d for d in valid_entries if d["val"] == 100], key=lambda x: x['name'])
                    elif has_zero:
                        win_data = min([d for d in valid_entries if d["val"] == 0], key=lambda x: x['name'])
                    else:
                        win_data = min(valid_entries, key=lambda x: abs(x["val"] - target))
                    
                    winner_name = win_data["name"]
                    for d in valid_entries:
                        if d["name"] == winner_name:
                            summary.append({"名前": d["name"], "数値": d["val"], "判定": "👑 勝利！"})
                        else:
                            d["player"]["points"] -= 1
                            summary.append({"名前": d["name"], "数値": d["val"], "判定": "💀 敗北(-1pt)"})
                
                for p in st.session_state.players:
                    if p["points"] <= -5: p["is_active"] = False
                
                st.session_state.last_summary = {"data": summary, "avg": avg, "target": target}
                st.session_state.show_results = True
                st.rerun()

    else:
        # 結果表示画面
        st.subheader(f"第 {st.session_state.round} ラウンド 結果")
        s = st.session_state.last_summary
        st.info(f"平均: {s['avg']:.1f}  →  **ターゲット: {s['target']:.2f}**")
        st.table(pd.DataFrame(s['data']))
        
        if st.button("次のラウンドへ"):
            st.session_state.round += 1
            st.session_state.submitted_count = 0
            st.session_state.current_inputs = {}
            st.session_state.show_results = False
            st.rerun()
