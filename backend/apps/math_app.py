import os
import json
import requests
import numpy as np
import matplotlib.pyplot as plt
import sympy as sp
import streamlit as st
from core.groq_client import groq_chat

def require_access():
    # Prefer Streamlit secrets; fallback to env var
    access_code = st.secrets.get("ACCESS_CODE", None) or os.environ.get("ACCESS_CODE", None)
    if not access_code:
        st.error("Server is missing ACCESS_CODE.")
        st.stop()

    if "authorized" not in st.session_state:
        st.session_state.authorized = False

    if not st.session_state.authorized:
        st.title("Bahman's AI Math Tutor")
        code = st.text_input("Access code", type="password")
        if st.button("Enter"):
            if code == access_code:
                st.session_state.authorized = True
                st.rerun()
            else:
                st.error("Incorrect access code.")
        st.stop()

        require_access()


# -----------------------
# Config / Paths
# -----------------------
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROFILE_PATH = os.path.join(BASE_DIR, "student_profile.json")
PROMPT_PATH = os.path.join(BASE_DIR, "system_prompt.txt")
PLOTS_DIR = os.path.join(BASE_DIR, "plots")

MODEL_NAME = "llama-3.3-70b-versatile"
TEMPERATURE = 0.3

# -----------------------
# Helpers
# -----------------------
def load_text(path: str) -> str:
    with open(path, "r", encoding="utf-8") as f:
        return f.read()

def load_profile() -> dict:
    with open(PROFILE_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def build_wrapper(profile: dict, mode: str, student_message: str) -> str:
    return f"""STUDENT_PROFILE:
{json.dumps(profile, indent=2, ensure_ascii=False)}

MODE: {mode}

STUDENT_MESSAGE:
{student_message}
""".strip()

def groq_chat(system_prompt: str, user_prompt: str) -> str:
    api_key = st.secrets.get("GROQ_API_KEY") or os.environ.get("GROQ_API_KEY")
    if not api_key:
        return "❌ GROQ_API_KEY is not set."

    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": MODEL_NAME,
        "temperature": TEMPERATURE,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
    }

    response = requests.post(url, headers=headers, json=payload, timeout=60)
    response.raise_for_status()

    return response.json()["choices"][0]["message"]["content"].strip()


    r = requests.post(url, headers=headers, json=payload, timeout=60)
    r.raise_for_status()
    return r.json()["choices"][0]["message"]["content"].strip()

# -----------------------
# Plotting
# -----------------------
x = sp.Symbol("x")

def plot_function(expr_str: str, x_min: float = -10, x_max: float = 10, n: int = 800):
    """
    Returns (fig, saved_path) or (None, error_message)
    """
    try:
        expr = sp.sympify(expr_str, locals={"x": x})
    except Exception as e:
        return None, f"Could not parse expression: {e}"

    f = sp.lambdify(x, expr, modules=["numpy"])
    xs = np.linspace(x_min, x_max, n)

    with np.errstate(all="ignore"):
        ys = f(xs)

    fig = plt.figure()
    plt.plot(xs, ys)
    plt.axhline(0)
    plt.axvline(0)
    plt.grid(True)
    plt.xlabel("x")
    plt.ylabel("y")
    plt.title(f"y = {sp.sstr(expr)}")

    os.makedirs(PLOTS_DIR, exist_ok=True)
    saved_path = os.path.join(PLOTS_DIR, "plot.png")
    plt.savefig(saved_path, dpi=150, bbox_inches="tight")
    return fig, saved_path

# -----------------------
# Streamlit UI
# -----------------------
st.set_page_config(page_title="Bahman's AI Math Tutor", layout="centered")
st.title("Bahman's AI Math Tutor")

# Session state
if "chat" not in st.session_state:
    st.session_state.chat = []  # list of (role, content)
if "mode" not in st.session_state:
    st.session_state.mode = "tutor"

system_prompt = load_text(PROMPT_PATH)
profile = load_profile()

with st.sidebar:
    st.header("Settings")
    st.session_state.mode = st.selectbox("Mode", ["tutor", "hints", "exam"], index=0)
    st.markdown("**Plot command**: `/plot x**2 - 3*x + 2`")
    st.markdown("Tip: Use `**` for powers, e.g. `x**2`.")

# Display chat
for role, content in st.session_state.chat:
    with st.chat_message(role):
        st.markdown(content)

# Input
user_msg = st.chat_input("Type a math question… (or /plot …)")
if user_msg:
    # show user
    st.session_state.chat.append(("user", user_msg))
    with st.chat_message("user"):
        st.markdown(user_msg)

    # Handle /plot locally
    if user_msg.startswith("/plot "):
        expr = user_msg[len("/plot "):].strip()
        fig, result = plot_function(expr)

        if fig is None:
            assistant_text = f"❌ Plot error: {result}"
            st.session_state.chat.append(("assistant", assistant_text))
            with st.chat_message("assistant"):
                st.markdown(assistant_text)
        else:
            assistant_text = f"✅ Plot saved to: `{result}`"
            st.session_state.chat.append(("assistant", assistant_text))
            with st.chat_message("assistant"):
                st.markdown(assistant_text)
                st.pyplot(fig, clear_figure=True)

    else:
        # Send to Groq
        wrapper = build_wrapper(profile, st.session_state.mode, user_msg)
        try:
            reply = groq_chat(system_prompt, wrapper)
        except Exception as e:
            reply = f"❌ API error: {e}"

        st.session_state.chat.append(("assistant", reply))
        with st.chat_message("assistant"):
            st.markdown(reply)
