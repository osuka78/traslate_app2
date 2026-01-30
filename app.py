import streamlit as st
import google.generativeai as genai
from google.api_core import exceptions

# --- Simplified & High Contrast UI with Custom CSS ---
def apply_premium_styles():
    st.markdown("""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap');
        
        /* 背景は白に近く、文字は真っ黒に近い色でコントラストを最大化 */
        .stApp {
            background-color: #fcfcfc;
            font-family: 'Inter', sans-serif;
        }

        /* ヘッダーを最小限に */
        .header-box {
            padding: 10px 0;
            margin-bottom: 20px;
            border-bottom: 2px solid #eeeeee;
        }

        .header-title {
            color: #000000;
            font-weight: 800;
            font-size: 1.5rem;
            margin: 0;
        }

        /* テキストエリアの視認性を極限まで高める */
        .stTextArea textarea {
            background-color: #ffffff !important;
            color: #000000 !important;
            border: 2px solid #222222 !important;
            border-radius: 8px !important;
            font-size: 1.1rem !important;
        }

        /* 回答エリア（st.info）を白背景、黒文字、太い枠線でくっきりさせる */
        .stAlert {
            background-color: #ffffff !important;
            color: #000000 !important;
            border: 2px solid #000000 !important;
            box-shadow: 4px 4px 0px #eeeeee !important;
            border-radius: 8px !important;
        }
        
        /* ラベルやキャプションのコントラストも上げる */
        h3, p, span, label {
            color: #000000 !important;
            font-weight: 600 !important;
        }
        
        .stCaption {
            color: #444444 !important;
        }

        /* スマホ向けのパディング調整 */
        @media (max-width: 768px) {
            .header-title {
                font-size: 1.2rem;
            }
        }

        [data-testid="stStatusWidget"] {
            display: none;
        }
        
        .stForm {
            border: none !important;
            padding: 0 !important;
        }

        /* ボタンを目立たせる */
        .stButton button {
            background-color: #000000 !important;
            color: #ffffff !important;
            border-radius: 8px !important;
            border: none !important;
            font-weight: 800 !important;
            padding: 10px 20px !important;
        }
        </style>
    """, unsafe_allow_html=True)

# Page Config
st.set_page_config(page_title="Translator", page_icon="💬", layout="wide")
apply_premium_styles()

# --- Gemini Configuration ---
API_KEY = st.secrets["GOOGLE_API_KEY"]
genai.configure(api_key=API_KEY)

# 利用可能なモデルの優先順位リスト
MODEL_PRIORITY = [
    'models/gemini-2.5-flash', 
    'models/gemini-2.0-flash', 
    'models/gemini-2.5-flash-lite', 
    'models/gemini-2.5-pro', 
    'models/gemini-pro-latest',
    'models/gemini-exp-1206'
]

def generate_with_fallback(prompt):
    """レート制限が発生した場合にモデルを切り替えて再試行する関数"""
    last_exception = None
    for model_name in MODEL_PRIORITY:
        try:
            model = genai.GenerativeModel(model_name)
            response = model.generate_content(prompt)
            return response, model_name
        except exceptions.ResourceExhausted:
            last_exception = f"Rate limit reached for {model_name}"
            continue
        except Exception as e:
            raise e
    
    if last_exception:
        raise Exception(f"すべてのモデルでレート制限に達しました: {last_exception}")
    raise Exception("コンテンツの生成に失敗しました。")

# Minimal Header
st.markdown('<div class="header-box"><h1 class="header-title">💬 Translator & Reply</h1></div>', unsafe_allow_html=True)

# Session State
if 'last_incoming' not in st.session_state:
    st.session_state.last_incoming = ""
if 'last_reply_result' not in st.session_state:
    st.session_state.last_reply_result = ""
if 'last_reply_model' not in st.session_state:
    st.session_state.last_reply_model = ""
if 'last_reply_input' not in st.session_state:
    st.session_state.last_reply_input = ""

# --- Create Two Columns ---
col1, col2 = st.columns([1, 1], gap="medium")

# ==========================================
# Left Column: Incoming Translation
# ==========================================
with col1:
    st.markdown("### 📥 英 → 日")
    
    @st.fragment
    def translation_fragment():
        st.markdown('<p style="margin-bottom: -10px;">受信内容（英語）</p>', unsafe_allow_html=True)
        incoming_text = st.text_area(
            "Receive Area", 
            height=180, 
            placeholder="英語を入力してください",
            key="inc_input_area_wide",
            label_visibility="collapsed"
        )

        if incoming_text:
            st.session_state.last_incoming = incoming_text
            status_msg = st.empty()
            status_msg.caption("⏳ 翻訳中...")
            try:
                prompt = f"""
                プロの翻訳者として、以下の英語のテキストを自然な日本語に翻訳してください。
                [英語テキスト]: {incoming_text}
                """
                response, used_model = generate_with_fallback(prompt)
                status_msg.empty()
                st.markdown(f"**翻訳結果 ({used_model})**")
                st.info(response.text)
            except Exception as e:
                status_msg.empty()
                st.error(f"エラー: {e}")

    translation_fragment()


# ==========================================
# Right Column: Reply Creation
# ==========================================
with col2:
    st.markdown("### 📤 日 → 英")
    
    @st.fragment
    def reply_fragment():
        with st.form("reply_form_wide"):
            st.markdown('<p style="margin-bottom: -10px;">返信内容（日本語）</p>', unsafe_allow_html=True)
            reply_text = st.text_area(
                "Reply Area", 
                height=150, 
                placeholder="返信内容（日本語）を入力してください",
                key="reply_input_area_wide",
                label_visibility="collapsed"
            )
            
            st.markdown('<p style="margin-bottom: -10px; margin-top: 10px;">修正・追加の指示 (任意)</p>', unsafe_allow_html=True)
            instruction_text = st.text_area(
                "Instructions",
                height=65,
                placeholder="例：この情報を追加して、もっと○○なニュアンスで、など",
                key="reply_instruction_wide",
                label_visibility="collapsed"
            )
            
            col_btn1, col_btn2 = st.columns([1, 1])
            with col_btn1:
                submit_button = st.form_submit_button("✨ 英文生成 / 修正")
            with col_btn2:
                clear_button = st.form_submit_button("🗑️ リセット")

            if clear_button:
                st.session_state.last_reply_result = ""
                st.session_state.last_reply_model = ""
                st.session_state.last_reply_input = ""
                st.rerun()

            if submit_button:
                if reply_text.strip():
                    status_msg_reply = st.empty()
                    status_msg_reply.caption("⏳ 生成中...")
                    try:
                        ref_text = f"Context: {st.session_state.last_incoming}" if st.session_state.last_incoming else "None"
                        
                        # リファインメントか新規生成かの判定
                        is_refinement = (
                            st.session_state.last_reply_result and 
                            reply_text == st.session_state.last_reply_input and 
                            instruction_text.strip()
                        )

                        if is_refinement:
                            prompt = f"""
                            プロのビジネス翻訳者として、以前の提案をベースに修正・追加を行ってください。
                            [コンテキスト]: {ref_text}
                            [元の入力日本語]: {reply_text}
                            [以前の提案結果]: 
                            {st.session_state.last_reply_result}
                            
                            [修正・追加の指示]: {instruction_text}
                            
                            上記の結果に対し、ユーザーの指示を完璧に反映した、さらに洗練された返信案を提示してください。
                            """
                        else:
                            prompt = f"""
                            プロのビジネス翻訳者として、最適な英語返信案を作成してください。
                            [コンテキスト]: {ref_text}
                            [入力日本語]: {reply_text}
                            [追加指示]: {instruction_text if instruction_text else "特になし"}
                            
                            [出力構成]:
                            1. AIオススメ（英文、戻し訳[日本語]、採用理由[日本語]）
                            2. Formal（英文、日本語訳）
                            3. Casual（英文、日本語訳）

                            [重要な指示]:
                            - 解説・理由はすべて日本語で出力してください。
                            - AIオススメには戻し訳（日本語）を必ず含めてください。
                            """
                        
                        response, used_model = generate_with_fallback(prompt)
                        status_msg_reply.empty()
                        
                        # セッション状態の更新
                        st.session_state.last_reply_result = response.text
                        st.session_state.last_reply_model = used_model
                        st.session_state.last_reply_input = reply_text
                        st.rerun()

                    except Exception as e:
                        status_msg_reply.empty()
                        st.error(f"エラー: {e}")
                else:
                    st.warning("内容を入力してください。")

        # 結果の常時表示
        if st.session_state.last_reply_result:
            st.markdown(f"**AI案 ({st.session_state.last_reply_model})**")
            st.info(st.session_state.last_reply_result)

    reply_fragment()

# Footer
st.markdown("""
<div style="text-align: center; color: #000000; font-size: 0.75rem; margin-top: 50px; border-top: 1px solid #eeeeee; padding-top: 10px;">
    Modern Translator Framework • Multi-Model
</div>
""", unsafe_allow_html=True)
