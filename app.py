import streamlit as st
import google.generativeai as genai
from google.api_core import exceptions

# --- UI Enhancement with Custom CSS ---
def apply_premium_styles():
    st.markdown("""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;800&display=swap');
        
        .stApp {
            background: linear-gradient(135deg, #f8faff 0%, #e8efff 100%);
            font-family: 'Outfit', sans-serif;
        }

        .header-box {
            background: rgba(255, 255, 255, 0.7);
            backdrop-filter: blur(12px);
            border-radius: 20px;
            padding: 20px;
            border: 1px solid rgba(255, 255, 255, 0.4);
            box-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.05);
            margin-bottom: 25px;
            text-align: center;
        }

        .gradient-text {
            background: linear-gradient(90deg, #2563eb, #7c3aed);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            font-weight: 800;
            font-size: 2.2rem;
            margin: 0;
        }

        /* カラムの中のカード風スタイル */
        .column-card {
            background: white;
            border-radius: 20px;
            padding: 25px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.03);
            border: 1px solid #f0f2f6;
            height: 100%;
        }

        [data-testid="stStatusWidget"] {
            display: none;
        }
        
        .stForm {
            border: none !important;
            padding: 0 !important;
        }
        </style>
    """, unsafe_allow_html=True)

# Page Config (Wide Layout for side-by-side)
st.set_page_config(page_title="Smart Business Comm", page_icon="💬", layout="wide")
apply_premium_styles()

# --- Gemini Configuration ---
API_KEY = st.secrets["GOOGLE_API_KEY"]
genai.configure(api_key=API_KEY)

# 利用可能なモデルの優先順位リスト（ユーザー提供のリストに基づく）
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
            # レート制限エラーの場合は次のモデルを試す
            last_exception = f"Rate limit reached for {model_name}"
            continue
        except Exception as e:
            # その他のエラーはそのままスロー
            raise e
    
    if last_exception:
        raise Exception(f"すべてのモデルでレート制限に達しました: {last_exception}")
    raise Exception("コンテンツの生成に失敗しました。")

# Header Area
st.markdown('<div class="header-box"><h1 class="gradient-text">💬 Mail & Chat Assistant</h1><p style="color: #64748b; margin-top:5px;">相手のトーンを読み取り、最適な返信を左右で同時サポート</p></div>', unsafe_allow_html=True)

# Session State
if 'last_incoming' not in st.session_state:
    st.session_state.last_incoming = ""

# --- Create Two Columns ---
col1, col2 = st.columns([1, 1], gap="large")

# ==========================================
# Left Column: Incoming Translation
# ==========================================
with col1:
    st.markdown("### 📥 届いたメッセージ (英 → 日)")
    st.caption("英語を貼り付けると自動で翻訳・トーン分析を行います")
    
    @st.fragment
    def translation_fragment():
        incoming_text = st.text_area(
            "Receive Area", 
            height=200, 
            placeholder="ここに相手からのメールやチャットを貼り付けてください",
            key="inc_input_area_wide",
            label_visibility="collapsed"
        )

        if incoming_text:
            st.session_state.last_incoming = incoming_text
            status_msg = st.empty()
            status_msg.caption("⌛ 分析中...")
            try:
                prompt = f"""
                以下の英語のテキストを日本語に翻訳してください。
                [指示]:
                1. 媒体（メール/チャット）と相手のトーンを分析し、最適な日本語で翻訳してください。
                [英語テキスト]: {incoming_text}
                """
                response, used_model = generate_with_fallback(prompt)
                status_msg.empty()
                st.markdown(f"#### 🇯🇵 翻訳と分析結果 (`{used_model}`)")
                st.info(response.text)
            except Exception as e:
                status_msg.empty()
                st.error(f"エラー: {e}")
        else:
            st.info("左側のボックスに翻訳したい文章を入力してください。")

    translation_fragment()


# ==========================================
# Right Column: Reply Creation
# ==========================================
with col2:
    st.markdown("### 📤 返信の作成 (日 → 英)")
    st.caption("左側のメッセージがある場合、そのトーンを考慮します")
    
    @st.fragment
    def reply_fragment():
        with st.form("reply_form_wide"):
            reply_text = st.text_area(
                "Reply Area", 
                height=200, 
                placeholder="例：了解しました。明日までに確認して連絡します。",
                key="reply_input_area_wide",
                label_visibility="collapsed"
            )
            submit_button = st.form_submit_button("✨ 英語の返信案を生成")

            if submit_button:
                if reply_text.strip():
                    status_msg_reply = st.empty()
                    status_msg_reply.caption("⌛ 相手に合わせた案を構成中...")
                    try:
                        ref_text = f"相手のメッセージ: {st.session_state.last_incoming}" if st.session_state.last_incoming else "なし"
                        prompt = f"""
                        プロのビジネス翻訳者として、最適な英語返信案を作成してください。
                        [コンテキスト]: {ref_text}
                        [入力日本語]: {reply_text}
                        [出力構成]:
                        1. AIオススメ（相手のトーンと同期）
                           - 英文
                           - 採用理由（※必ず日本語で説明してください）
                        2. Formal（丁寧）
                           - 英文と日本語訳
                        3. Casual（簡潔）
                           - 英文と日本語訳

                        [重要な指示]:
                        - 英文が適切である理由や、ニュアンスの解説は、すべて**日本語**で出力してください。
                        """
                        response, used_model = generate_with_fallback(prompt)
                        status_msg_reply.empty()
                        st.markdown("---")
                        st.markdown(f"#### 📝 AIからの提案 (`{used_model}`)")
                        st.markdown(response.text)
                    except Exception as e:
                        status_msg_reply.empty()
                        st.error(f"エラー: {e}")
                else:
                    st.warning("返信したい内容を入力してください。")

    reply_fragment()

st.markdown("""
<br><br>
<div style="text-align: center; color: #94a3b8; font-size: 0.8rem;">
    Side-by-Side Context Sync • Multi-Model Fallback Support
</div>
""", unsafe_allow_html=True)
