import streamlit as st

with st.sidebar:
    st.success("✅ Deployed: logout-test v1")
import streamlit as st

CLOUDFLARE_LOGOUT_URL = "https://bahmankarimi.cloudflareaccess.com/cdn-cgi/access/logout"

with st.sidebar:
    st.markdown("### Account")
    st.markdown(
        f"""
        <a href="{CLOUDFLARE_LOGOUT_URL}" target="_self"
           style="display:inline-block;padding:0.5rem 0.9rem;border:1px solid #ccc;border-radius:8px;
                  text-decoration:none;">
           🚪 Log out
        </a>
        """,
        unsafe_allow_html=True,
    )
from flask import Flask, request, jsonify
from flask_cors import CORS
from math_tutor import run_tutor_turn
import os

app = Flask(__name__)
CORS(app, resources={
    r"/api/*": {
        "origins": [
            "https://tutor.bahmankarimi.com",
            "https://bahmankarimi.cloudflareaccess.com",
            "https://api.bahmankarimi.com"
        ]
    }
})
def get_cf_email():
    return (request.headers.get("cf-access-authenticated-user-email")
            or request.headers.get("CF-Access-Authenticated-User-Email"))

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/api/tutor")
def tutor():
    email = get_cf_email()
    if not email:
        return jsonify({
            "status": "error",
            "error": "No Cloudflare identity header found. Access this via Cloudflare Access."
        }), 401

    data = request.get_json(force=True) or {}
    msg = (data.get("message") or "").strip()
    level = (data.get("level") or "default").strip()
    mode = (data.get("mode") or "tutor").strip()

    if not msg:
        return jsonify({"status": "error", "error": "Missing 'message'"}), 400

    result = run_tutor_turn(user_id=email, level=level, mode=mode, student_message=msg)
    result["user"] = {"email": email}
    return jsonify(result)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", "8000"))
    app.run(host="0.0.0.0", port=port, debug=True)
