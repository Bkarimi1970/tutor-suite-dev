import os
import json
import re
import requests
import numpy as np
import matplotlib.pyplot as plt
import sympy as sp
import streamlit as st
from pint import UnitRegistry
from tools.fbd import fbd_atwood, fbd_incline, fbd_1d_horizontal

# -----------------------
# Config / Paths
# -----------------------
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PHYSICS_PROMPT_PATH = os.path.join(BASE_DIR, "physics_system_prompt.txt")
PROFILE_PATH = os.path.join(BASE_DIR, "student_profile.json")  # reuse
PLOTS_DIR = os.path.join(BASE_DIR, "plots")

MODEL_NAME = "llama-3.3-70b-versatile"
TEMPERATURE = 0.3

ureg = UnitRegistry()
Q_ = ureg.Quantity

# -----------------------
# Helpers
# -----------------------
def load_text(path: str) -> str:
    with open(path, "r", encoding="utf-8") as f:
        return f.read()

def load_profile() -> dict:
    if os.path.exists(PROFILE_PATH):
        with open(PROFILE_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"student_name": "Student", "level": "grade11", "style": "detailed"}

def build_wrapper(profile, mode, student_message):
    return f"""STUDENT_PROFILE:
{json.dumps(profile, ensure_ascii=False, indent=2)}

MODE: {mode}

STUDENT_MESSAGE:
{student_message}
""".strip()


def groq_chat(system_prompt: str, user_prompt: str) -> str:
    api_key = st.secrets.get("GROQ_API_KEY") or os.environ.get("GROQ_API_KEY")
    if not api_key:
        return "❌ GROQ_API_KEY is not set."

    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    payload = {
        "model": MODEL_NAME,
        "temperature": TEMPERATURE,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
    }

    r = requests.post(url, headers=headers, json=payload, timeout=60)
    r.raise_for_status()
    return r.json()["choices"][0]["message"]["content"].strip()

# -----------------------
# Command: /units
# Example: /units 72 km/h to m/s
# -----------------------
def cmd_units(text: str) -> str:
    # expected pattern: "<value> <unit> to <unit>"
    # e.g. "72 km/h to m/s"
    m = re.match(r"^\s*([-+]?[\d.]+)\s+(.+?)\s+to\s+(.+?)\s*$", text)
    if not m:
        return "Usage: /units <value> <unit> to <unit>\nExample: /units 72 km/h to m/s"

    value = float(m.group(1))
    from_unit = m.group(2).strip()
    to_unit = m.group(3).strip()

    try:
        q = Q_(value, from_unit).to(to_unit)
        return f"{value} {from_unit} = {q.magnitude:g} {to_unit}"
    except Exception as e:
        return f"❌ Unit conversion error: {e}"

# -----------------------
# Command: /kin (1D constant acceleration)
# Example: /kin v0=0 m/s, a=2 m/s^2, t=5 s
# You can give any subset of v0, v, a, t, dx
# -----------------------
def parse_kin_args(arg_str: str) -> dict:
    # accepts comma-separated pairs: key=value unit
    # e.g., "v0=0 m/s, a=2 m/s^2, t=5 s"
    parts = [p.strip() for p in arg_str.split(",") if p.strip()]
    out = {}
    for p in parts:
        if "=" not in p:
            continue
        key, rest = p.split("=", 1)
        key = key.strip()
        rest = rest.strip()
        # rest: "<number> <unit...>"
        m = re.match(r"^\s*([-+]?[\d.]+)\s*(.*)\s*$", rest)
        if not m:
            continue
        val = float(m.group(1))
        unit = m.group(2).strip() if m.group(2).strip() else None
        out[key] = (val, unit)
    return out

def cmd_kin(arg_str: str) -> str:
    args = parse_kin_args(arg_str)

    # Symbols
    v0, v, a, t, dx = sp.symbols("v0 v a t dx", real=True)

    # Equations for 1D constant acceleration
    eqs = [
        sp.Eq(v, v0 + a*t),
        sp.Eq(dx, v0*t + sp.Rational(1,2)*a*t**2),
        sp.Eq(v**2, v0**2 + 2*a*dx),
    ]

    # Known values (convert to SI when possible)
    known = {}

    def put(name, sym, default_unit):
        if name in args:
            val, unit = args[name]
            try:
                if unit:
                    q = Q_(val, unit).to(default_unit)
                    known[sym] = float(q.magnitude)
                else:
                    known[sym] = float(val)
            except Exception:
                # fallback raw
                known[sym] = float(val)

    put("v0", v0, "m/s")
    put("v", v, "m/s")
    put("a", a, "m/s^2")
    put("t", t, "s")
    put("dx", dx, "m")

    # Solve for unknowns: try solve for all symbols not in known
    unknown_syms = [s for s in [v0, v, a, t, dx] if s not in known]

    # Use sympy solve with substitutions
    subbed_eqs = [eq.subs(known) for eq in eqs]

    try:
        sol = sp.solve(subbed_eqs, unknown_syms, dict=True)
        if not sol:
            return "❌ Could not solve with given values. Provide at least 3 consistent quantities (e.g., v0, a, t) or (v0, v, a) or (v0, v, dx)."
        sol0 = sol[0]

        # Build a readable output
        lines = ["**1D Kinematics (constant acceleration) solution:**", ""]
        # Report given
        lines.append("**Given (SI):**")
        for sym, val in known.items():
            lines.append(f"- {str(sym)} = {val:g}")
        lines.append("")
        lines.append("**Solved:**")
        for sym in unknown_syms:
            if sym in sol0:
                lines.append(f"- {str(sym)} = {float(sol0[sym]):g}")
        lines.append("")
        lines.append("Units note: v0,v in m/s; a in m/s²; t in s; dx in m.")
        return "\n".join(lines)

    except Exception as e:
        return f"❌ Kinematics solver error: {e}"

# -----------------------
# Command: /plot_motion (1D constant a)
# Example: /plot_motion v0=0 m/s, a=2 m/s^2, t=5 s, x0=0 m
# Plots x(t), v(t), a(t) from 0..t
# -----------------------
def cmd_plot_motion(arg_str: str):
    args = parse_kin_args(arg_str)

    def get_q(name, default_unit, default_value=None):
        if name not in args:
            return default_value
        val, unit = args[name]
        if unit:
            return float(Q_(val, unit).to(default_unit).magnitude)
        return float(val)

    v0 = get_q("v0", "m/s", 0.0)
    a = get_q("a", "m/s^2", 0.0)
    T = get_q("t", "s", None)
    x0 = get_q("x0", "m", 0.0)

    if T is None:
        return None, "Usage: /plot_motion v0=..., a=..., t=... (required)\nExample: /plot_motion v0=0 m/s, a=2 m/s^2, t=5 s, x0=0 m"

    ts = np.linspace(0, T, 400)
    xs = x0 + v0*ts + 0.5*a*ts**2
    vs = v0 + a*ts
    acc = np.full_like(ts, a)

    fig = plt.figure()
    plt.plot(ts, xs)
    plt.grid(True)
    plt.xlabel("t (s)")
    plt.ylabel("x (m)")
    plt.title("Position vs Time: x(t)")

    os.makedirs(PLOTS_DIR, exist_ok=True)
    path1 = os.path.join(PLOTS_DIR, "motion_xt.png")
    plt.savefig(path1, dpi=150, bbox_inches="tight")
    st.pyplot(fig, clear_figure=True)

    fig2 = plt.figure()
    plt.plot(ts, vs)
    plt.grid(True)
    plt.xlabel("t (s)")
    plt.ylabel("v (m/s)")
    plt.title("Velocity vs Time: v(t)")
    path2 = os.path.join(PLOTS_DIR, "motion_vt.png")
    plt.savefig(path2, dpi=150, bbox_inches="tight")
    st.pyplot(fig2, clear_figure=True)

    fig3 = plt.figure()
    plt.plot(ts, acc)
    plt.grid(True)
    plt.xlabel("t (s)")
    plt.ylabel("a (m/s²)")
    plt.title("Acceleration vs Time: a(t)")
    path3 = os.path.join(PLOTS_DIR, "motion_at.png")
    plt.savefig(path3, dpi=150, bbox_inches="tight")
    st.pyplot(fig3, clear_figure=True)

    return (path1, path2, path3), "✅ Motion plots saved."

# -----------------------
# Streamlit UI
# -----------------------
st.set_page_config(page_title="Bahman's Physics Tutor (Kinematics)", layout="centered")
st.title("Bahman's Physics Tutor — Kinematics (1D/2D)")

system_prompt = load_text(PHYSICS_PROMPT_PATH)
profile = load_profile()

if "chat" not in st.session_state:
    st.session_state.chat = []
if "mode" not in st.session_state:
    st.session_state.mode = "tutor"

with st.sidebar:
    st.header("Commands")
    st.code("/units 72 km/h to m/s")
    st.code("/kin v0=0 m/s, a=2 m/s^2, t=5 s")
    st.code("/plot_motion v0=0 m/s, a=2 m/s^2, t=5 s, x0=0 m")
    st.session_state.mode = st.selectbox("Mode", ["tutor", "hints", "exam"], index=0)

# Display chat
for role, content in st.session_state.chat:
    with st.chat_message(role):
        st.markdown(content)

user_msg = st.chat_input("Ask a kinematics question… (or use /units, /kin, /plot_motion)")
if user_msg:
    st.session_state.chat.append(("user", user_msg))
    with st.chat_message("user"):
        st.markdown(user_msg)

    # Commands first
    if user_msg.startswith("/units "):
        out = cmd_units(user_msg[len("/units "):])
        st.session_state.chat.append(("assistant", out))
        with st.chat_message("assistant"):
            st.markdown(out)

    elif user_msg.startswith("/kin "):
        out = cmd_kin(user_msg[len("/kin "):])
        st.session_state.chat.append(("assistant", out))
        with st.chat_message("assistant"):
            st.markdown(out)

    elif user_msg.startswith("/plot_motion "):
        with st.chat_message("assistant"):
            paths, msg = cmd_plot_motion(user_msg[len("/plot_motion "):])
            st.markdown(msg)
        st.session_state.chat.append(("assistant", msg))

    else:
        wrapper = build_wrapper(profile, st.session_state.mode, user_msg)
        try:
            reply = groq_chat(system_prompt, wrapper)
        except Exception as e:
            reply = f"❌ API error: {e}"

        st.session_state.chat.append(("assistant", reply))
        with st.chat_message("assistant"):
            st.markdown(reply)
elif user_msg.startswith("/fbd "):
    # Examples:
    # /fbd atwood m1
    # /fbd atwood m2
    # /fbd incline
    # /fbd 1d

    cmd = user_msg[len("/fbd "):].strip().lower()

    outdir = os.path.join(BASE_DIR, "plots")

    try:
        if cmd.startswith("atwood"):
            parts = cmd.split()
            if len(parts) != 2:
                reply = "Usage: /fbd atwood m1   OR   /fbd atwood m2"
            else:
                mass_label = parts[1]
                fig, path = fbd_atwood(mass_label=mass_label, outdir=outdir)
                st.pyplot(fig)
                reply = f"✅ FBD saved to: `{path}`"

        elif cmd.startswith("incline"):
            fig, path = fbd_incline(outdir=outdir, show_components=True)
            st.pyplot(fig)
            reply = f"✅ FBD saved to: `{path}`"

        elif cmd.startswith("1d"):
            fig, path = fbd_1d_horizontal(outdir=outdir)
            st.pyplot(fig)
            reply = f"✅ FBD saved to: `{path}`"

        else:
            reply = "Usage:\n/fbd atwood m1\n/fbd atwood m2\n/fbd incline\n/fbd 1d"

    except Exception as e:
        reply = f"❌ FBD error: {e}"

    st.session_state.chat.append(("assistant", reply))
    with st.chat_message("assistant"):
        st.markdown(reply)
