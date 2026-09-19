import streamlit as st
import requests
import re
import groq

GROQ_API_KEY = st.secrets["GROQ_API_KEY"]
SERPER_API_KEY = st.secrets["SERPER_API_KEY"]

client = groq.Client(api_key=GROQ_API_KEY)
# =========================
# 🔑 KEYS
# =========================
GROQ_API_KEY = st.secrets["GROQ_API_KEY"]
SERPER_API_KEY = st.secrets["SERPER_API_KEY"]

client = Groq(api_key=GROQ_API_KEY)

# =========================
# PAGE CONFIG
# =========================
st.set_page_config(page_title="MyAI Chat", layout="wide")

# =========================
# UI STYLE
# =========================
st.markdown("""
<style>
.user {
    background:#2563eb;
    padding:12px;
    border-radius:12px;
    margin:10px;
    color:white;
    text-align:right;
    max-width:70%;
    margin-left:auto;
}
.ai {
    background:#1e293b;
    padding:12px;
    border-radius:12px;
    margin:10px;
    color:white;
    max-width:70%;
}
</style>
""", unsafe_allow_html=True)

st.title("🤖 MyAI Chat")

# =========================
# SIDEBAR
# =========================
st.sidebar.title("💬 Chats")

if "chats" not in st.session_state:
    st.session_state.chats = {"Chat 1": []}

if "current_chat" not in st.session_state:
    st.session_state.current_chat = "Chat 1"

if st.sidebar.button("➕ New Chat"):
    name = f"Chat {len(st.session_state.chats)+1}"
    st.session_state.chats[name] = []
    st.session_state.current_chat = name

st.sidebar.markdown("---")

for chat in list(st.session_state.chats.keys()):
    col1, col2 = st.sidebar.columns([4,1])

    with col1:
        if st.button(chat, key=f"select_{chat}"):
            st.session_state.current_chat = chat

    with col2:
        if st.button("❌", key=f"delete_{chat}"):
            del st.session_state.chats[chat]

            if st.session_state.chats:
                st.session_state.current_chat = list(st.session_state.chats.keys())[0]
            else:
                st.session_state.chats["Chat 1"] = []
                st.session_state.current_chat = "Chat 1"

            st.rerun()

messages = st.session_state.chats[st.session_state.current_chat]

# =========================
# GOOGLE SEARCH
# =========================
def google_search(query):
    try:
        url = "https://google.serper.dev/search"
        headers = {
            "X-API-KEY": SERPER_API_KEY,
            "Content-Type": "application/json"
        }
        res = requests.post(url, headers=headers, json={"q": query})
        data = res.json()

        return " ".join([i.get("snippet","") for i in data.get("organic", [])[:5]])

    except:
        return ""

# =========================
# 🔥 CLEAN OUTPUT (FIXED)
# =========================
def clean_output(text):

    text = text.replace("Cov⁡", "\\operatorname{Cov}")
    text = text.replace("Var⁡", "\\operatorname{Var}")
    text = text.replace("Corr⁡", "\\operatorname{Corr}")

    text = text.replace("β", "\\beta")
    text = text.replace("ε", "\\varepsilon")
    text = text.replace("β^", "\\hat{\\beta}")

    # ✅ FIXED FUNCTION
    def fix_formula(match):
        content = match.group(1).strip()

        # Only convert if looks like math
        if re.search(r"[=+\-*/^]", content):
            content = re.sub(r"[,\.\s]+$", "", content)
            return f"$$ {content} $$"

        return f"[{content}]"

    def fix_table(match):
        table = match.group()
        return re.sub(r"\$\$.*?\$\$", "[formula below]", table)

    # ✅ Order fixed
    text = re.sub(r"(\|.*\|(?:\n\|.*\|)+)", fix_table, text)
    text = re.sub(r"\[(.*?)\]", fix_formula, text, flags=re.DOTALL)

    return text

# =========================
# 🔥 RENDER (FIXED)
# =========================
def render(text):
    text = clean_output(text)

    parts = re.split(r"(\$\$.*?\$\$)", text, flags=re.DOTALL)

    for part in parts:
        if part.startswith("$$") and part.endswith("$$"):
            formula = part[2:-2].strip()
            st.latex(formula)   # ✅ perfect rendering
        else:
            st.markdown(part)

# =========================
# AI RESPONSE
# =========================
def get_response(prompt):

    google_data = google_search(prompt)

    system_prompt = f"""
You are ChatGPT-level AI.

STRICT RULES:
- Tables: text only
- Formulas: MUST be in $$...$$ format only
- Clean formatting

Context:
{google_data}
"""

    response = client.chat.completions.create(
        model="openai/gpt-oss-120b",
        messages=[
            {"role": "system", "content": system_prompt},
            *messages,
            {"role": "user", "content": prompt}
        ]
    )

    return response.choices[0].message.content

# =========================
# INPUT + AUTO RENAME
# =========================
user_input = st.chat_input("Ask anything...")

if user_input:
    messages.append({"role": "user", "content": user_input})

    if st.session_state.current_chat.startswith("Chat"):
        new_name = user_input[:30].strip()

        count = 1
        base = new_name
        while new_name in st.session_state.chats:
            new_name = f"{base} ({count})"
            count += 1

        st.session_state.chats[new_name] = st.session_state.chats.pop(st.session_state.current_chat)
        st.session_state.current_chat = new_name
        messages = st.session_state.chats[new_name]

    reply = get_response(user_input)
    messages.append({"role": "assistant", "content": reply})

# =========================
# DISPLAY
# =========================
for msg in messages:

    if msg["role"] == "user":
        st.markdown(f'<div class="user">{msg["content"]}</div>', unsafe_allow_html=True)

    else:
        st.markdown('<div class="ai">', unsafe_allow_html=True)
        render(msg["content"])
        st.markdown('</div>', unsafe_allow_html=True)
