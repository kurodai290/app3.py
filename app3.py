import streamlit as st
import pandas as pd

st.set_page_config(page_title="0.8倍サバイバル：脱落ルール", page_icon="🚫")

# --- セッション状態の初期化 ---
if 'game_active' not in st.session_state:
    st.session_state.update({
        'game_active': False,
        'players': [],
        'round': 1,
        'submitted_count': 0,
        'current_inputs': {},
    })

def start_game(names):
    # 空行を除外してプレイヤーリストを作成
    st.session_state.players = [{"name": name.strip(), "points": 0, "is_active": True} for name in names if name.strip()]
    st.session_state.game_active = True
    st.session_state.round = 1
    st.session_state.current_inputs = {}
    st.session_state.submitted_count = 0

# --- メインUI ---
st.title("⚖️ 0.8倍サバイバル：脱落戦")

if not st.session_state.game_active:
    st.subheader("プレイヤー登録")
    player_names = st.text_area("参加者の名前を改行して入力", "プレイヤー1\nプレイヤー2\nプレイヤー3")
    if st.button("ゲーム開始"):
        start_game(player_names.split('\n'))
        st.rerun()

else:
    # サイドバー：現在のスコアと脱落判定
    st.sidebar.header("📊 スコアボード")
    for p in st.session_state.players:
        status = "✅ 生存" if p['is_active'] else "💀 脱落"
        color = "white" if p['is_active'] else "red"
        st.sidebar.markdown(f":{color}[{p['name']}: {p['points']} pt ({status})]")
    
    if st.sidebar.button("ゲームをリセット"):
        st.session_state.game_active = False
        st.rerun()

    # 生存しているプレイヤーのみを抽出
    active_players = [p for p in st.session_state.players if p['is_active']]
    
    if len(active_players) <= 1:
        st.balloons()
        winner = active_players[0]['name'] if active_players else "なし"
        st.error(f"🏁 ゲーム終了！ 生き残った勝者は **{winner}** です！")
        if st.button("タイトルへ戻る"):
            st.session_state.game_active = False
            st.rerun()
    else:
        st.subheader(f"第 {st.session_state.round} ラウンド")
        
        # 現在入力すべき「生存プレイヤー」を特定
        current_active_idx = st.session_state.submitted_count
        
        if current_active_idx < len(active_players):
            current_player = active_players[current_active_idx]["name"]
            
            with st.form(key=f"input_{st.session_state.round}_{current_player}"):
                st.write(f"👉 **{current_player}** さんの番です")
                val = st.number_input("0〜100の整数を入力", 0, 100, step=1)
                st.caption("※他の人に見られないように！")
                if st.form_submit_button("確定"):
                    st.session_state.current_inputs[current_player] = val
                    st.session_state.submitted_count += 1
                    st.rerun()
        else:
            # 全員の入力完了後の計算
            if st.button("結果を表示する"):
                results = st.session_state.current_inputs
                vals = list(results.values())
                avg = sum(vals) / len(vals)
                target = avg * 0.8
                
                counts = {v: vals.count(v) for v in set(vals)}
                summary = []
                valid_entries = []

                # 1. 被りチェック（-2pt）
                for name, val in results.items():
                    p_ref = next(p for p in st.session_state.players if p["name"] == name)
                    if counts[val] > 1:
                        p_ref["points"] -= 2
                        summary.append({"名前": name, "数値": val, "判定": "💥 被り(-2pt)"})
                    else:
                        valid_entries.append({"name": name, "val": val, "player": p_ref})
                
                # 2. 勝者判定
                winner_name = None
                if valid_entries:
                    # 特殊ルール（0と100）
                    has_zero = any(d["val"] == 0 for d in valid_entries)
                    has_hundred = any(d["val"] == 100 for d in valid_entries)
                    
                    if has_zero and has_hundred:
                        win_data = [d for d in valid_entries if d["val"] == 100][0]
                    elif has_zero:
                        win_data = [d for d in valid_entries if d["val"] == 0][0]
                    else:
                        win_data = min(valid_entries, key=lambda x: abs(x["val"] - target))
                    
                    winner_name = win_data["name"]
                    
                    # 3. 敗者チェック（-1pt）
                    for d in valid_entries:
                        if d["name"] == winner_name:
                            summary.append({"名前": d["name"], "数値": d["val"], "判定": "👑 勝利！"})
                        else:
                            d["player"]["points"] -= 1
                            summary.append({"名前": d["name"], "数値": d["val"], "判定": "💀 敗北(-1pt)"})
                
                # 4. 脱落チェック
                for p in st.session_state.players:
                    if p["points"] <= -5:
                        p["is_active"] = False

                st.divider()
                st.info(f"平均: {avg:.1f}  →  **ターゲット(×0.8): {target:.2f}**")
                st.table(pd.DataFrame(summary))
                
                if st.button("次のラウンドへ"):
                    st.session_state.round += 1
                    st.session_state.submitted_count = 0
                    st.session_state.current_inputs = {}
                    st.rerun()
