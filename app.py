import streamlit as st
import pandas as pd
import uuid
import os
import qrcode
from io import BytesIO

# 🔗 Replace with your deployed link
url = "https://your-app-name.streamlit.app"

# Generate QR
qr = qrcode.make(url)

# Convert to image buffer
buf = BytesIO()
qr.save(buf)

# Display
st.image(buf, caption="📱 Scan to Join Game", use_container_width=True)

# Also show clickable link
st.markdown(f"👉 [Click here to join]({url})")

TOTAL_AMOUNT = 100
DATA_FILE = "game_data.csv"
PAIR_FILE = "pairs.csv"

# ---------- INIT FILES ----------
if not os.path.exists(DATA_FILE):
    pd.DataFrame(columns=["pair_id", "role", "offer", "decision"]).to_csv(DATA_FILE, index=False)

if not os.path.exists(PAIR_FILE):
    pd.DataFrame(columns=["pair_id", "proposer", "responder", "offer", "decision"]).to_csv(PAIR_FILE, index=False)

# ---------- SESSION ----------
if "player_id" not in st.session_state:
    st.session_state.player_id = str(uuid.uuid4())[:8]

if "pair_id" not in st.session_state:
    st.session_state.pair_id = None

if "role" not in st.session_state:
    st.session_state.role = None

st.title("🧠 Ultimatum Game (Multiplayer)")

# ---------- JOIN GAME ----------
if st.button("🎮 Join Game"):

    pairs = pd.read_csv(PAIR_FILE)

    # Check for waiting proposer
    waiting = pairs[pairs["responder"].isna()]

    if not waiting.empty:
        pair = waiting.iloc[0]
        pair_id = pair["pair_id"]

        pairs.loc[pairs["pair_id"] == pair_id, "responder"] = st.session_state.player_id

        st.session_state.role = "Responder"
        st.session_state.pair_id = pair_id

    else:
        pair_id = str(uuid.uuid4())[:6]

        new_row = pd.DataFrame([{
            "pair_id": pair_id,
            "proposer": st.session_state.player_id,
            "responder": None,
            "offer": None,
            "decision": None
        }])

        pairs = pd.concat([pairs, new_row])

        st.session_state.role = "Proposer"
        st.session_state.pair_id = pair_id

    pairs.to_csv(PAIR_FILE, index=False)
    st.success(f"Joined as {st.session_state.role} (Pair {st.session_state.pair_id})")

# ---------- GAME ----------
if st.session_state.role == "Proposer":

    st.header("💰 Proposer")

    offer = st.slider("Choose amount to give", 0, TOTAL_AMOUNT, 50)

    if st.button("Submit Offer"):

        pairs = pd.read_csv(PAIR_FILE)
        pairs.loc[pairs["pair_id"] == st.session_state.pair_id, "offer"] = offer
        pairs.to_csv(PAIR_FILE, index=False)

        st.success("Offer submitted. Waiting for responder...")

elif st.session_state.role == "Responder":

    st.header("🤔 Responder")

    pairs = pd.read_csv(PAIR_FILE)
    row = pairs[pairs["pair_id"] == st.session_state.pair_id]

    if not row.empty and pd.notna(row.iloc[0]["offer"]):

        offer = int(row.iloc[0]["offer"])
        st.write(f"Offer received: ₹{offer}")

        decision = st.radio("Accept or Reject?", ["Accept", "Reject"])

        if st.button("Submit Decision"):

            pairs.loc[pairs["pair_id"] == st.session_state.pair_id, "decision"] = decision
            pairs.to_csv(PAIR_FILE, index=False)

            if decision == "Accept":
                st.success(f"You get ₹{offer}")
            else:
                st.error("Rejected! Both get ₹0")

    else:
        st.warning("Waiting for proposer to make an offer...")

# ---------- ADMIN VIEW ----------
st.sidebar.header("📊 Admin Panel")

if st.sidebar.button("Download Data"):
    data = pd.read_csv(PAIR_FILE)
    st.sidebar.download_button("Download CSV", data.to_csv(index=False), "results.csv")
