import base64
import os
import random
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components
from gtts import gTTS

# 設定網頁標題與寬度配置
st.set_page_config(page_title="港北社區 機智問答", page_icon="💡", layout="centered")

# --- 🎨 網頁樣式優化（長者友善大字體、隱藏音訊播放器、放大按鈕與黑字） ---
st.markdown(
    """
    <style>
    .stApp { background-color: #B0BEC5; }
    .big-title { font-size: 38px !important; font-weight: bold; color: #002244; text-align: center; }
    .question-box { background-color: #8FBC8F; padding: 30px; border-radius: 15px; border: 3px solid #2C5282; font-size: 32px !important; font-weight: bold; text-align: center; color: #111111; margin-bottom: 20px; }
    
    /* 放大並讓所有按鈕更大更好點擊 */
    .stButton>button {
        width: 100% !important;
        font-size: 26px !important;
        font-weight: bold;
        padding: 18px !important;
        border-radius: 12px;
    }
    
    /* 自動隱藏所有音訊播放器元件 */
    .stAudio {
        display: none;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    '<p class="big-title">🌟 港北社區共惠時間銀行 🌟</p>', unsafe_allow_html=True
)
st.markdown(
    '<p style="text-align: center; font-size: 22px; color: #1A365D; font-weight:'
    ' bold;">機智問答挑戰賽</p>',
    unsafe_allow_html=True,
)


# --- 📂 載入題庫 ---
@st.cache_data
def load_data():
  target_files = ["quiz_bank.xlsx", "quiz_bank", "quiz_bank.xls"]
  for fname in target_files:
    if os.path.exists(fname):
      df = pd.read_excel(fname).fillna("")
      df.columns = df.columns.str.strip()
      return df.to_dict(orient="records")
  return []


questions = load_data()


# --- 🎵 背景音樂處理（透過元件穩定播放背景音樂） ---
def play_bgm():
  bgm_path = "bgm_2.mp3" if os.path.exists("bgm_2.mp3") else "bgm.mp3"
  if os.path.exists(bgm_path):
    with open(bgm_path, "rb") as f:
      data = f.read()
    b64 = base64.b64encode(data).decode()
    audio_html = f"""
        <audio autoplay loop controls>
            <source src="data:audio/mp3;base64,{b64}" type="audio/mp3">
        </audio>
        <script>
            var audio = document.querySelector('audio');
            audio.volume = 0.5;
            audio.play().catch(function(error) {{
                console.log("Autoplay prevented:", error);
            }});
        </script>
        """
    components.html(audio_html, height=0, width=0)


# 啟動背景音樂
play_bgm()


# --- 🔊 語音合成函式 (gTTS)：優化數字與年份讀法 ---
def generate_speech(text):
  try:
    text_processed = (
        text.replace("第 2 題", "第貳題")
        .replace("第2題", "第貳題")
        .replace("100年", "一百年")
        .replace("100 年", "一百年")
    )

    tts = gTTS(text=text_processed, lang="zh-tw", slow=False)
    audio_path = "temp_speech.mp3"
    tts.save(audio_path)
    return audio_path
  except Exception as e:
    print(f"語音生成失敗: {e}")
    return None


# --- ⚙️ 定義檢查答案函式 ---
def check_ans(user_ans, q):
  correct_ans = str(q.get("正確答案", "")).strip().upper()
  st.session_state.answered = True
  if user_ans.upper() == correct_ans:
    st.session_state.score += 1
    st.session_state.is_correct = True
    st.session_state.effect_audio = (
        "correct.mp3" if os.path.exists("correct.mp3") else None
    )
  else:
    st.session_state.is_correct = False
    st.session_state.effect_audio = (
        "wrong.mp3" if os.path.exists("wrong.mp3") else None
    )
  st.rerun()


# --- 🔄 初始化遊戲狀態 ---
if "started" not in st.session_state:
  st.session_state.started = False
if "current_idx" not in st.session_state:
  st.session_state.current_idx = 0
if "score" not in st.session_state:
  st.session_state.score = 0
if "answered" not in st.session_state:
  st.session_state.answered = False
if "is_correct" not in st.session_state:
  st.session_state.is_correct = None
if "effect_audio" not in st.session_state:
  st.session_state.effect_audio = None

# --- 🚀 歡迎畫面 ---
if not st.session_state.started:
  st.markdown("<br><br>", unsafe_allow_html=True)
  col1, col2, col3 = st.columns([0.5, 3, 0.5])
  with col2:
    if st.button(
        "🚀 開始答題挑戰", use_container_width=True, key="start_btn"
    ):
      if questions:
        random.shuffle(questions)
        st.session_state.questions = questions
        st.session_state.started = True
        st.session_state.current_idx = 0
        st.session_state.score = 0
        st.session_state.answered = False
        st.session_state.effect_audio = None
        st.rerun()
      else:
        st.error("找不到 'quiz_bank.xlsx' 題庫檔案，請確認是否已上傳！")

# --- 📝 答題畫面 ---
else:
  q_list = st.session_state.questions
  idx = st.session_state.current_idx

  if idx < len(q_list):
    q = q_list[idx]
    q_type = str(q.get("題型", "")).strip()
    q_text = str(q.get("題目", "")).strip()

    st.markdown(
        f"### 📍 第 {idx + 1} / {len(q_list)} 題 [{q_type if q_type else '是非題'}]"
    )

    # 題目大框
    st.markdown(
        f'<div class="question-box">{q_text}</div>', unsafe_allow_html=True
    )

    # 自動生成並在背景朗讀題目
    speech_text = f"第 {idx + 1} 題。{q_text}"
    if "選擇" in q_type:
      for opt in ["A", "B", "C", "D"]:
        val = q.get(f"選項{opt}", "")
        if str(val).strip():
          speech_text += f"選項{opt}，{val}。"
    speech_file = generate_speech(speech_text)
    if speech_file:
      st.audio(speech_file, format="audio/mp3", autoplay=True)

    # 作答選項區域
    if not st.session_state.answered:
      if "選擇" in q_type:
        options = [
            ("A", q.get("選項A", "")),
            ("B", q.get("選項B", "")),
            ("C", q.get("選項C", "")),
            ("D", q.get("選項D", "")),
        ]
        for opt_key, opt_val in options:
          if str(opt_val).strip():
            if st.button(
                f"({opt_key}) {opt_val}",
                use_container_width=True,
                key=f"opt_{opt_key}",
            ):
              check_ans(opt_key, q)
      else:
        col1, col2 = st.columns(2)
        with col1:
          if st.button(
              "⭕ 正確 (O)", use_container_width=True, key="btn_o"
          ):
            check_ans("O", q)
        with col2:
          if st.button(
              "❌ 錯誤 (X)", use_container_width=True, key="btn_x"
          ):
            check_ans("X", q)
    else:
      # 播放答對/答錯音效
      if st.session_state.effect_audio and os.path.exists(
          st.session_state.effect_audio
      ):
        st.audio(
            st.session_state.effect_audio, format="audio/mp3", autoplay=True
        )

      correct_ans = str(q.get("正確答案", "")).strip().upper()
      explanation = str(q.get("解析", "")).strip()

      if st.session_state.is_correct:
        st.markdown(
            '<div style="background-color: #A3E4D7; padding: 25px;'
            ' border-radius: 12px; font-size: 28px; font-weight: bold;'
            ' color: #111111; text-align: center; margin-bottom: 20px;">✨'
            ' 答對了！讚讚讚！🎉</div>',
            unsafe_allow_html=True,
        )
      else:
        st.markdown(
            f'<div style="background-color: #F5B7B1; padding: 25px;'
            f' border-radius: 12px; font-size: 26px; font-weight: bold;'
            f' color: #111111; text-align: center; margin-bottom: 20px;">❌'
            f' 答錯了！正確答案是：【 {correct_ans} 】</div>',
            unsafe_allow_html=True,
        )
        if explanation:
          st.markdown(
              f'<div style="background-color: #AED6F1; padding: 25px;'
              f' border-radius: 12px; font-size: 24px; font-weight: bold;'
              f' color: #111111; margin-bottom: 25px; line-height: 1.5;">💡'
              f' 解析：<br>{explanation}</div>',
              unsafe_allow_html=True,
          )

      col1, col2, col3 = st.columns([0.5, 3, 0.5])
      with col2:
        if st.button(
            "下一題 ➡️", use_container_width=True, key="next_btn"
        ):
          st.session_state.current_idx += 1
          st.session_state.answered = False
          st.session_state.effect_audio = None
          st.rerun()

  else:
    # --- 📊 結算畫面 ---
    total_q = len(q_list)
    final_score = (
        round((st.session_state.score / total_q) * 100) if total_q > 0 else 0
    )

    if final_score >= 80:
      if os.path.exists("applaud.mp3"):
        st.audio("applaud.mp3", format="audio/mp3", autoplay=True)
      st.markdown(
          f'<div style="background-color: #A3E4D7; padding: 30px;'
          f' border-radius: 12px; font-size: 28px; font-weight: bold;'
          f' color: #111111; text-align: center; margin-bottom: 25px;">💯'
          f' 最終得分：{final_score} 分！挑戰成功！<br><br>👑 港北社區共惠 時間銀行'
          f' 👑<br>全體會員 恭喜您！！</div>',
          unsafe_allow_html=True,
      )
    else:
      if os.path.exists("wrong.mp3"):
        st.audio("wrong.mp3", format="audio/mp3", autoplay=True)
      st.markdown(
          f'<div style="background-color: #F5B7B1; padding: 30px;'
          f' border-radius: 12px; font-size: 28px; font-weight: bold;'
          f' color: #111111; text-align: center; margin-bottom: 25px;">💔'
          f' 最終得分：{final_score} 分，未達 80 分門檻，再接再勵！</div>',
          unsafe_allow_html=True,
      )

    col1, col2, col3 = st.columns([0.5, 3, 0.5])
    with col2:
      if st.button(
          "🔄 重新答題", use_container_width=True, key="restart_btn"
      ):
        st.session_state.started = False
        st.session_state.effect_audio = None
        st.rerun()