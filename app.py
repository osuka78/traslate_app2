import streamlit as st
import google.generativeai as genai

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
            padding: 30px;
            border: 1px solid rgba(255, 255, 255, 0.4);
            box-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.05);
            margin-bottom: 30px;
            text-align: center;
        }

        .gradient-text {
            background: linear-gradient(90deg, #2563eb, #7c3aed);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            font-weight: 800;
            font-size: 2.5rem;
            margin: 0;
        }

        [data-testid="stStatusWidget"] {
            display: none;
        }
        
        .stForm {
            border: none !important;
            padding: 0 !important;
        }
        
        /* おすすめセクションを際立たせる */
        .recommended-box {
            background: #fffbef;
            border: 1px solid #ffe58f;
            border-radius: 10px;
            padding: 15px;
            margin-bottom: 20px;
        }
        </style>
    """, unsafe_allow_html=True)

# Page Config
st.set_page_config(page_title="Smart Business Comm", page_icon="💬", layout="centered")
apply_premium_styles()

# --- Gemini Configuration ---
API_KEY = "GOOGLE_API_KEY"
genai.configure(api_key=API_KEY)
model = genai.GenerativeModel('gemini-2.5-flash')

# Header Area
st.markdown('<div class="header-box"><h1 class="gradient-text">💬 Mail & Chat Assistant</h1><p style="color: #64748b;">相手のトーンに合わせた最適な返信をAIがプロデュース</p></div>', unsafe_allow_html=True)

# Initialize session state for referencing between fragments
if 'last_incoming' not in st.session_state:
    st.session_state.last_incoming = ""

# ==========================================
# Area 1: Incoming Translation
# ==========================================
st.subheader("1. 届いたメッセージを翻訳 (英 → 日)")

@st.fragment
def translation_fragment():
    incoming_text = st.text_area(
        "メッセージを貼り付けてください", 
        height=180, 
        placeholder="ここに貼り付けると、下の返信案の精度も上がります",
        key="inc_input_area_final"
    )

    if incoming_text:
        st.session_state.last_incoming = incoming_text # 保存
        status_msg = st.empty()
        status_msg.caption("⌛ トーンを分析中...")
        try:
            prompt = f"""
            以下の英語のテキストを日本語に翻訳してください。
            
            [指示]:
            1. 媒体（メール/チャット）と相手のトーン（硬い、フランク、急いでいる等）を分析し、最適な日本語で翻訳してください。
            [英語テキスト]:
            {incoming_text}
            """
            response = model.generate_content(prompt)
            status_msg.empty()
            st.markdown("---")
            st.markdown("#### 🇯🇵 日本語訳")
            st.info(response.text)
        except Exception as e:
            status_msg.empty()
            st.error(f"エラー: {e}")

translation_fragment()

st.markdown("<br><hr><br>", unsafe_allow_html=True)

# ==========================================
# Area 2: Reply Creation
# ==========================================
st.subheader("2. 返信案の作成 (日 → 英)")

@st.fragment
def reply_fragment():
    with st.form("reply_form_final"):
        reply_text = st.text_area(
            "返したい内容 (日本語)", 
            height=120, 
            placeholder="例：了解。詳細を後で送ります。",
            key="reply_input_area_final"
        )
        submit_button = st.form_submit_button("✨ 相手に合わせた返信案を生成")

        if submit_button:
            if reply_text.strip():
                status_msg_reply = st.empty()
                status_msg_reply.caption("⌛ 相手のトーンと同期した返信を構成中...")
                try:
                    # 1番に入力がある場合はそれを参考に、ない場合は一般常識で
                    ref_text = f"相手からのメッセージ: {st.session_state.last_incoming}" if st.session_state.last_incoming else "なし（一般的なビジネスマナー準拠）"
                    
                    prompt = f"""
                    プロのビジネス翻訳者として、最適な英語返信案を作成してください。
                    
                    [参照情報]:
                    {ref_text}
                    
                    [入力された日本語意図]:
                    {reply_text}
                    
                    [期待する出力]:
                    以下の3つのパターンを提示してください。
                    
                    1. 【AIオススメ：Best Match】
                       - 「参照情報」にある相手のメッセージのトーン（語彙の硬さ、絵文字の有無、文長）を分析し、それに最も近いトーンで返信を作成してください。
                       - なぜこれがオススメなのか（例：相手がフレンドリーなのでこちらも少し和らげました、等）の理由を添えてください。
                    
                    2. 【Formal：丁寧な表現】
                       - 相手のトーンに関わらず、目上の人やクライアントに送っても失礼のない、格調高い表現。
                    
                    3. 【Casual/Quick : 簡潔な表現】
                       - 意味を最小限の単語で伝える、チャット向けの極めて迅速な表現。
                    
                    各案には必ず「日本語訳」を添えてください。
                    """
                    response = model.generate_content(prompt)
                    status_msg_reply.empty()
                    st.markdown("---")
                    st.markdown("### 📝 AIからの提案結果")
                    st.markdown(response.text)
                except Exception as e:
                    status_msg_reply.empty()
                    st.error(f"エラー: {e}")
            else:
                st.warning("内容を入力してください。")

reply_fragment()

st.markdown("""
<br><br>
<div style="text-align: center; color: #94a3b8; font-size: 0.8rem;">
    Analyzing Tone & Mirroring Response • Powered by Gemini 2.5 Flash
</div>
""", unsafe_allow_html=True)