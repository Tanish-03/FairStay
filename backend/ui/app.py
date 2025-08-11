import time
import requests
import streamlit as st

st.set_page_config(page_title="FairStay", page_icon="🏠", layout="wide")

# 
st.sidebar.title("Settings")
API_URL = st.sidebar.text_input("API URL", "http://127.0.0.1:8000")
with st.sidebar:
    # Health check
    ok = False
    try:
        r = requests.get(f"{API_URL}/health", timeout=3)
        ok = (r.status_code == 200)
    except Exception:
        ok = False
    st.markdown(
        f"**API Status:** {' Connected' if ok else ' Not reachable'}"
    )
    st.caption("Tip: Start the API with `uvicorn backend.main:app --reload`")

st.title("FairStay — Tenant Complaint Submission")


with st.container():
    st.subheader("Submit a complaint")
    with st.form("submit_form", clear_on_submit=False):
        user_id = st.text_input("User ID (optional)", placeholder="e.g., anon-134")
        complaint_text = st.text_area(
            "Describe your issue",
            height=140,
            placeholder="What happened? Include facts: who, what, when, where.",
        )
        colA, colB, colC = st.columns([1,1,2])
        with colA:
            submit = st.form_submit_button("🚀 Submit Complaint")
        with colB:
            st.caption(f"Characters: {len(complaint_text)}")
        with colC:
            st.caption("Please avoid names if you want anonymity.")

    if submit:
        if not complaint_text.strip():
            st.error("Complaint text is required.")
        else:
            payload = {"user_id": user_id.strip() or None, "complaint_text": complaint_text.strip()}
            with st.spinner("Analyzing with AI…"):
                try:
                    res = requests.post(f"{API_URL}/submit_complaint", json=payload, timeout=30)
                except Exception as e:
                    st.error(f"Could not reach API: {e}")
                    st.stop()
            if res.status_code != 200:
                st.error(f"Error {res.status_code}: {res.text}")
            else:
                data = res.json()
                st.toast("Complaint submitted", icon="✅")
                st.success("AI analysis complete")
                m1, m2, m3 = st.columns(3)
                with m1: st.metric("Category", data.get("category", "-"))
                with m2: st.metric("Severity (1–5)", data.get("severity_score", "-"))
                with m3: st.metric("Record ID", data.get("id", "-"))
                st.write("**Summary**")
                st.write(data.get("generated_summary", ""))

st.markdown("---")
st.subheader("Browse complaints")

col1, col2, col3 = st.columns([1,1,2])
with col1:
    view_id = st.number_input("Fetch by ID", min_value=1, step=1, value=1)
with col2:
    limit = st.slider("Show recent (count)", min_value=5, max_value=50, value=15, step=5)

c1, c2 = st.columns([1,1])
with c1:
    if st.button("Fetch Complaint"):
        r = requests.get(f"{API_URL}/complaints/{int(view_id)}")
        if r.status_code == 200:
            st.json(r.json())
        else:
            st.error("Not found.")

with c2:
    if st.button("Load Recent"):
        try:
            r = requests.get(f"{API_URL}/complaints", params={"limit": int(limit)}, timeout=15)
            if r.status_code == 200:
                rows = r.json()
                if not rows:
                    st.info("No complaints yet.")
                else:
                    # quick severity filter
                    sev = st.select_slider("Filter by minimum severity", options=[1,2,3,4,5], value=1)
                    rows = [x for x in rows if (x.get("severity_score") or 0) >= sev]
                    st.dataframe(
                        rows,
                        use_container_width=True,
                        column_config={
                            "id": "ID",
                            "user_id": "User",
                            "category": "Category",
                            "severity_score": "Severity",
                            "generated_summary": st.column_config.TextColumn("Summary", width="large"),
                            "submitted_at": "Submitted",
                        },
                    )
            else:
                st.error(f"Error loading list: {r.status_code}")
        except Exception as e:
            st.error(f"Error: {e}")
