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
st.title("⚖️ 0.8倍サバイバル：脱落戦")

if not st.session_state.game_active:
    st.subheader("プレイヤー登録")
    player_names = st.text_area("参加者の名前を改行して入力", "プレイヤー1\nプレイヤー2\nプレイヤー3")
    if st.button("ゲーム開始"):
        start_game(player_names.split('\n'))
        st.rerun()

else:
    # --- スコアボードの強化 ---
    st.sidebar.header("📊 スコアボード")
    for p in st.session_state.players:
        # ポイントに応じた色の設定
        if not p['is_active']:
            color = "gray"
            status_mark = "💀 脱落"
        elif p['points'] <= -4:
            color = "red"
            status_mark = "⚠️ リーチ！"
        else:
            color = "blue"
            status_mark = "✅ 生存"
        
        # ボックス型のスコア表示
        st.sidebar.markdown(f"""
        ---
        ### :{color}[{p['name']}]
        **得点: {p['points']} pt**  
        状態: {status_mark}
        """)
        # 脱落までの残りライフをプログレスバーで表示（-5で終了なので、5を最大値とする）
        life = max(0, 5 + p['points'])
        st.sidebar.progress(life / 5)

    if st.sidebar.button("ゲームを完全にリセット"):
        st.session_state.game_active = False
        st.rerun()

    active_players = [p for p in st.session_state.players if p['is_active']]
    
    if len(active_players) <= 1:
        st.balloons()
        winner = active_players[0]['name'] if active_players else "なし"
        st.error(f"🏁 終焉！ 生き残った勝者は **{winner}** です！")
        if st.button("タイトルへ戻る"):
            st.session_state.game_active = False
            st.rerun()
            
    elif not st.session_state.show_results:
        st.subheader(f"第 {st.session_state.round} ラウンド")
        current_active_idx = st.session_state.submitted_count
        
        if current_active_idx < len(active_players):
            current_player = active_players[current_active_idx]["name"]
            st.info(f"🎤 次の入力者: **{current_player}** さん")
            with st.form(key=f"form_r{st.session_state.round}_{current_player}"):
                val = st.number_input(f"{current_player} さんの数字 (0〜100)", 0, 100, step=1)
                if st.form_submit_button("確定して次の人へ"):
                    st.session_state.current_inputs[current_player] = val
                    st.session_state.submitted_count += 1
                    st.rerun()
        else:
            if st.button("全員完了！結果を見る"):
                # 計算ロジック
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
                        summary.append({"名前": name, "数値": val, "判定": "💥 被り(-2pt)"})
                    else:
                        valid_entries.append({"name": name, "val": val, "player": p_ref})
                
                # 勝者判定
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
                
                # 脱落チェック
                for p in st.session_state.players:
                    if p["points"] <= -5:
                        p["is_active"] = False
                
                st.session_state.last_summary = {"data": summary, "avg": avg, "target": target}
                st.session_state.show_results = True
                st.rerun()

    else:
        st.subheader(f"第 {st.session_state.round} ラウンド 結果")
        s = st.session_state.last_summary
        st.markdown(f"### 🎯 ターゲット: **{s['target']:.2f}** (平均 {s['avg']:.1f} の0.8倍)")
        st.table(pd.DataFrame(s['data']))
        
        if st.button("次のラウンドへ"):
            st.session_state.round += 1
            st.session_state.submitted_count = 0
            st.session_state.current_inputs = {}
            st.session_state.show_results = False
            st.rerun()
