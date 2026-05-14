import streamlit as st
import pandas as pd

# 秘密のコードを設定（好きな文字に変えてください）
SECRET_CHEAT_CODE = "0542731081"

st.set_page_config(page_title="てんびん - ♦K", page_icon="⚖️")

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

st.title("⚖️ てんびん - ♦K")

if not st.session_state.game_active:
    st.subheader("参戦者の登録")
    player_names = st.text_area("参戦者の名前を改行して入力してください", "プレイヤー1\nプレイヤー2\nプレイヤー3")
    if st.button("均衡を開始する"):
        start_game(player_names.split('\n'))
        st.rerun()

else:
    # サイドバー（スコア）
    st.sidebar.header("⚖️ 均衡の秤")
    for p in st.session_state.players:
        color = "red" if p['points'] <= -4 else "blue"
        status = "💀 脱落" if not p['is_active'] else "✅ 均衡"
        st.sidebar.markdown(f"### :{color if p['is_active'] else 'gray'}[{p['name']}]\n**{p['points']} pt** ({status})")

    active_players = [p for p in st.session_state.players if p['is_active']]
    
    if len(active_players) <= 1:
        st.balloons()
        winner = active_players[0]['name'] if active_players else "なし"
        st.error(f"🏁 勝者: **{winner}**")
        if st.button("タイトルへ"):
            st.session_state.game_active = False
            st.rerun()
            
    elif not st.session_state.show_results:
        st.subheader(f"第 {st.session_state.round} ラウンド")
        current_player = active_players[st.session_state.submitted_count]["name"]
        
        with st.form(key=f"form_{st.session_state.round}_{current_player}", clear_on_submit=True):
            # マネージャー対策のためtext_input。autocompleteオフ
            val_input = st.text_input(f"{current_player} の数値 (0-100)", key=f"in_{st.session_state.round}_{current_player}", help="数字を入力してください")
            if st.form_submit_button("確定"):
                # チート判定 or 数値変換
                if val_input.lower() == SECRET_CHEAT_CODE:
                    st.session_state.current_inputs[current_player] = "CHEAT"
                elif val_input.isdigit() and 0 <= int(val_input) <= 100:
                    st.session_state.current_inputs[current_player] = int(val_input)
                else:
                    st.warning("有効な数値を入力してください")
                    st.stop()
                
                st.session_state.submitted_count += 1
                st.rerun()

    else:
        # --- 計算ロジック ---
        raw_results = st.session_state.current_inputs
        
        # チートコードを使っている人のために一旦仮の平均を出す
        # (チート以外の人の平均をターゲットの目安にする)
        normal_vals = [v for v in raw_results.values() if v != "CHEAT"]
        temp_avg = sum(normal_vals) / len(normal_vals) if normal_vals else 50
        temp_target = round(temp_avg * 0.8)

        # チート使用者の値をターゲットに書き換え
        final_results = {k: (temp_target if v == "CHEAT" else v) for k, v in raw_results.items()}
        
        vals = list(final_results.values())
        avg = sum(vals) / len(vals)
        target = avg * 0.8
        counts = {v: vals.count(v) for v in set(vals)}
        
        summary = []
        valid_entries = []
        for name, val in final_results.items():
            p_ref = next(p for p in st.session_state.players if p["name"] == name)
            if counts[val] > 1:
                p_ref["points"] -= 2
                summary.append({"名前": name, "数値": val, "判定": "💥 被り (-2)"})
            else:
                valid_entries.append({"name": name, "val": val, "player": p_ref})

        if valid_entries:
            has_zero = any(d["val"] == 0 for d in valid_entries)
            has_hundred = any(d["val"] == 100 for d in valid_entries)
            
            if has_zero and has_hundred:
                win_data = min([d for d in valid_entries if d["val"] == 100], key=lambda x: x['name'])
            elif has_zero and len(active_players) == 2:
                win_data = min([d for d in valid_entries if d["val"] == 0], key=lambda x: x['name'])
            else:
                win_data = min(valid_entries, key=lambda x: abs(x["val"] - target))
            
            for d in valid_entries:
                if d["name"] == win_data["name"]:
                    summary.append({"名前": d["name"], "数値": d["val"], "判定": "👑 勝利"})
                else:
                    d["player"]["points"] -= 1
                    summary.append({"名前": d["name"], "数値": d["val"], "判定": "💀 敗北 (-1)"})

        for p in st.session_state.players:
            if p["points"] <= -5: p["is_active"] = False

        st.subheader("判定結果")
        st.markdown(f"### 🎯 ターゲット: **{target:.2f}**")
        st.table(pd.DataFrame(summary))
        if st.button("次へ"):
            st.session_state.update({'round': st.session_state.round + 1, 'submitted_count': 0, 'current_inputs': {}, 'show_results': False})
            st.rerun()
