"""
app.py – Streamlit dashboard for the Invoice Extractor.

Run with:
    streamlit run app.py
"""

import requests
import streamlit as st
import pandas as pd

API_URL = "http://127.0.0.1:8000"

st.set_page_config(page_title="Invoice Extractor", layout="wide")
st.title("🧾 Invoice Extractor Dashboard")

# ── Upload section ────────────────────────────────────────────────────────────
st.header("1. Upload Invoices")
uploaded_files = st.file_uploader(
    "Upload one or more invoice images",
    accept_multiple_files=True,
    type=["png", "jpg", "jpeg"],
)

if st.button("Process Invoices", type="primary"):
    if uploaded_files:
        with st.spinner(f"Processing {len(uploaded_files)} invoice(s) through Qwen…"):
            files_to_send = [
                ("files", (f.name, f.getvalue(), f.type)) for f in uploaded_files
            ]
            try:
                res = requests.post(f"{API_URL}/upload/", files=files_to_send)
                if res.status_code == 200:
                    st.success("Processing complete!")
                    with st.expander("View Raw Output Logs"):
                        st.json(res.json())
                else:
                    st.error(f"API error {res.status_code}: {res.text}")
            except requests.ConnectionError:
                st.error("Could not connect to the API. Is it running?")
    else:
        st.warning("Please upload at least one file first.")

st.divider()

# ── Database section ──────────────────────────────────────────────────────────
st.header("2. Database Records")
tab_valid, tab_invalid = st.tabs(
    ["✅ Valid Invoices (MongoDB)", "⚠️ Invalid Invoices (GridFS)"]
)

with tab_valid:
    col1, col2 = st.columns([0.8, 0.2])
    with col1:
        st.subheader("Successfully Extracted Data")
    with col2:
        st.button("🔄 Refresh Valid")   # triggers a full Streamlit rerun

    try:
        valid_res = requests.get(f"{API_URL}/valid/")
        if valid_res.status_code == 200 and valid_res.json():
            records = []
            for doc in valid_res.json():
                inv = doc.get("invoice", {})
                records.append(
                    {
                        "File":           doc.get("source_file"),
                        "Extracted At":   (doc.get("extracted_at") or "")[:16].replace("T", " "),
                        "Confidence":     doc.get("confidence"),
                        "Total Expenses": inv.get("expenses"),
                        "Date":           inv.get("date"),
                        "Item Count":     len(inv.get("items", [])),
                    }
                )
            st.dataframe(pd.DataFrame(records), use_container_width=True)
            with st.expander("View Raw JSON Documents"):
                st.json(valid_res.json())
        else:
            st.info("No valid invoices found in the database.")
    except requests.ConnectionError as e:
        st.error(f"Could not connect to API: {e}")

with tab_invalid:
    col1, col2 = st.columns([0.8, 0.2])
    with col1:
        st.subheader("Failed / Low-Confidence Files")
    with col2:
        st.button("🔄 Refresh Invalid")

    try:
        invalid_res = requests.get(f"{API_URL}/invalid/")
        if invalid_res.status_code == 200 and invalid_res.json():
            invalid_data = invalid_res.json()
            cols = st.columns(3)
            for idx, item in enumerate(invalid_data):
                with cols[idx % 3]:
                    st.error(f"**{item['filename']}**")
                    st.caption(f"Reason: {item['reason']}")
                    st.caption(f"Confidence: {item['confidence']}")
                    img_url = f"{API_URL}/invalid/image/{item['_id']}"
                    st.image(img_url, use_column_width=True)
        else:
            st.info("No invalid files found in GridFS.")
    except requests.ConnectionError as e:
        st.error(f"Could not connect to API: {e}")
