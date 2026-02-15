# =======================
# Imports
# =======================

import os
import json
import time
import requests

import numpy as np
import matplotlib.pyplot as plt
import sympy as sp


# =======================
# Paths & Config
# =======================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

PROFILE_PATH = os.path.join(BASE_DIR, "student_profile.json")
PROMPT_PATH = os.path.join(BASE_DIR, "system_prompt.txt")
LOG_PATH = os.path.join(BASE_DIR, "session_log.jsonl")
PLOTS_DIR = os.path.join(BASE_DIR, "plots")

MODEL_NAME = "llama-3.3-70b-versatile"
TEMPERATURE = 0.3


# =======================
# Plotting Utilities
# =======================

x = sp.Symbol("x")

def plot_function(expr_str: str,
                  x_min: float = -10,
                  x_max: float = 10,
                  n: int = 800) -> None:
    """
    Plot a mathematical function of x and save it to disk.
    Example: "x**2 - 3*x + 2"
    """
    try:
        expr = sp.sympify(expr_str, locals={"x": x})
    except Exception as e:
        print(f"\nAI Tutor: ❌ Could not parse expression: {e}\n")
        return

    f = sp.lambdify(x, expr, modules=["numpy"])
    xs = np.linspace(x_min, x_max, n)

    with np.errstate(all="ignore"):
        ys = f(xs)

    plt.figure()
    plt.plot(xs, ys)
    plt.axhline(0)
    plt.axvline(0)
    plt.grid(True)
    plt.xlabel("x")
    plt.ylabel("y")
    plt.title(f"y = {sp.sstr(expr)}")

    os.makedirs(PLOTS_DIR, exist_ok=True)
    filepath = os.path.join(PLOTS_DIR, "plot.png")
    plt.savefig(filepath, dpi=150, bbox_inches="tight")

    print(f"\n📁 Plot saved to: {filepath}\n")
    plt.show()


# =======================
# File Utilities
# =======================

def load_text(path: str) -> str:
    with open(path, "r", encoding="utf-8") as f:
        return f.read()

def profile_path_for_user(user_id: str) -> str:
    safe = user_id.replace("/", "_").replace("\\", "_").replace(" ", "_")
    return os.path.join(BASE_DIR, "profiles", f"{safe}.json")

def load_profile(user_id: str = "default") -> dict:
    path = profile_path_for_user(user_id)
    if not os.path.exists(path):
        return {"user_id": user_id, "mastery": {}, "errors": {}, "history": []}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def save_profile(profile: dict, user_id: str = "default") -> None:
    path = profile_path_for_user(user_id)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(profile, f, indent=2, ensure_ascii=False)


def log_turn(student_msg: str,
             tutor_msg: str,
             profile: dict,
             mode: str) -> None:
    record = {
        "timestamp": time.time(),
        "mode": mode,
        "student_message": student_msg,
        "tutor_message": tutor_msg,
        "profile_snapshot": profile
    }
    with open(LOG_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")


# =======================
# Prompt Handling
# =======================

def build_wrapper(profile: dict,
                  mode: str,
                  student_message: str) -> str:
    return f"""STUDENT_PROFILE:
{json.dumps(profile, indent=2, ensure_ascii=False)}

MODE: {mode}

STUDENT_MESSAGE:
{student_message}
""".strip()


# =======================
# Groq API
# =======================

def groq_chat(system_prompt: str, user_prompt: str) -> str:
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        return "❌ GROQ_API_KEY is not set."

    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": MODEL_NAME,
        "temperature": TEMPERATURE,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
    }

    response = requests.post(url, headers=headers, json=payload, timeout=60)
    response.raise_for_status()

    return response.json()["choices"][0]["message"]["content"].strip()


# =======================
# API Entry Function
# =======================

def run_tutor_turn(user_id: str, level: str, mode: str, student_message: str) -> dict:
    """
    API-friendly single-turn tutor call.
    """

    system_prompt = load_text(PROMPT_PATH)
    profile = load_profile(user_id)

    # Inject level + mode into wrapper so prompt sees it
    wrapper = build_wrapper(
        profile=profile,
        mode=f"{mode}|{level}",
        student_message=student_message
    )

    try:
        tutor_reply = groq_chat(system_prompt, wrapper)
        status = "ok"
        err = None
    except Exception as e:
        tutor_reply = ""
        status = "error"
        err = f"API error: {e}"

    # Log + persist profile
    full_mode = f"{mode}|{level}"
    log_turn(student_message, tutor_reply, profile, full_mode)
    save_profile(profile, user_id)


    return {
        "status": status,
        "topic": "math",
        "final_answer": None,
        "steps": [],
        "feedback": tutor_reply,
        "diagnosis": [],
        "next_practice": [],
        "mastery_update": {},
        "error": err,
    }


def update_profile(profile: dict, student_msg: str, tutor_reply: str, max_history: int = 50) -> dict:
    profile.setdefault("history", [])
    profile.setdefault("mastery", {})
    profile.setdefault("errors", {})
    profile.setdefault("stuck_count", 0)

    # Store last turns
    profile["history"].append({
        "student": student_msg,
        "tutor": tutor_reply,
        "t": time.time()
    })
    profile["history"] = profile["history"][-max_history:]

    lower = (student_msg + " " + tutor_reply).lower()

    # Track algebra usage
    if "solve" in lower or "equation" in lower or "x =" in lower:
        profile["mastery"]["algebra"] = profile["mastery"].get("algebra", 0) + 1

    # Detect confusion
    if (
        "i don't know" in student_msg.lower()
        or "not sure" in student_msg.lower()
        or "confused" in student_msg.lower()
    ):
        profile["stuck_count"] += 1
    else:
        profile["stuck_count"] = 0

    return profile


# =======================
# Main Loop
# =======================

def main() -> None:
    system_prompt = load_text(PROMPT_PATH)
    profile = load_profile()
    mode = "tutor"

    print("=== Bahman's Math Tutor AI (Groq Version) ===")
    print("Type 'exit' to quit.\n")

    while True:
        student_msg = input("Student: ").strip()

        if not student_msg:
            print("Please enter a response or type 'exit' to quit.\n")
            continue

        if student_msg.lower() in {"exit", "quit"}:
            break

        if student_msg == "/profile":
            print(json.dumps(profile, indent=2, ensure_ascii=False))
            continue

        if student_msg == "/reset":
            profile = {"user_id": "default", "mastery": {}, "errors": {}, "history": []}
            save_profile(profile)
            print("✅ Profile reset.\n")
            continue

        if student_msg.startswith("/plot "):
            expr = student_msg[len("/plot "):].strip()
            plot_function(expr)
            continue
        if student_msg == "/answer":
            mode = "tutor_final_allowed"
            print("✅ OK — I can give the final answer now.\n")
            continue

        if student_msg == "/hint":
            mode = "tutor_hint_only"
            print("✅ OK — hint-only mode.\n")
            continue

        wrapper = build_wrapper(profile, mode, student_msg)

        try:
            tutor_reply = groq_chat(system_prompt, wrapper)
        except Exception as e:
            tutor_reply = f"❌ API error: {e}"

        print("\nAI Tutor:", tutor_reply, "\n")

        log_turn(student_msg, tutor_reply, profile, mode)
        save_profile(profile)


# =======================
# Entry Point
# =======================

if __name__ == "__main__":
    main()
