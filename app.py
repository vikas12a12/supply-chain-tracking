import streamlit as st
import pandas as pd
import hashlib
import json
import os
from datetime import datetime

# ==============================
# Blockchain Classes
# ==============================
class Transaction:
    def __init__(self, product_id, role, actor_name, location, status, notes, payment_type=None, payment_amount=0):
        self.product_id = product_id
        self.role = role
        self.actor_name = actor_name
        self.location = location
        self.status = status
        self.notes = notes
        self.timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.payment_type = payment_type  # "Debit" or "Credit"
        self.payment_amount = payment_amount

    def to_dict(self):
        return self.__dict__


class Block:
    def __init__(self, index, previous_hash, transaction):
        self.index = index
        self.timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.transaction = transaction
        self.previous_hash = previous_hash
        self.hash = self.compute_hash()

    def compute_hash(self):
        block_string = json.dumps({
            "index": self.index,
            "timestamp": self.timestamp,
            "transaction": self.transaction,
            "previous_hash": self.previous_hash
        }, sort_keys=True)
        return hashlib.sha256(block_string.encode()).hexdigest()

    def to_dict(self):
        return {
            "index": self.index,
            "timestamp": self.timestamp,
            "transaction": self.transaction,
            "previous_hash": self.previous_hash,
            "hash": self.hash
        }


class SimpleBlockchain:
    def __init__(self):
        self.chain = []
        self.load_chain()

    def create_genesis_block(self):
        genesis = Block(0, "0", {"msg": "Genesis Block"})
        self.chain.append(genesis)

    def add_block(self, transaction):
        prev_block = self.chain[-1]
        new_block = Block(len(self.chain), prev_block.hash, transaction.to_dict())
        self.chain.append(new_block)
        self.save_chain()

    def save_chain(self):
        with open("blockchain.json", "w") as f:
            json.dump([b.to_dict() for b in self.chain], f, indent=4)

    def load_chain(self):
        if os.path.exists("blockchain.json"):
            with open("blockchain.json", "r") as f:
                chain_data = json.load(f)
                self.chain = []
                for b in chain_data:
                    blk = Block(b["index"], b["previous_hash"], b["transaction"])
                    blk.timestamp = b["timestamp"]
                    blk.hash = b["hash"]
                    self.chain.append(blk)
        else:
            self.create_genesis_block()


# ==============================
# Streamlit UI
# ==============================
st.set_page_config(page_title="Blockchain Supply Chain Tracker", layout="wide")
st.title("🚚 Blockchain Supply Chain Tracker")

blockchain = SimpleBlockchain()

# Layout: only left column (right side is sidebar)
col1, _ = st.columns([3, 1])

# ==============================
# LEFT SIDE → Search & Blockchain
# ==============================
with col1:
    st.subheader("🔎 Search product journey")

    search_id = st.text_input("Enter Product ID to view journey", "")
    if st.button("View journey"):
        journey = [
            {
                "Time": block.timestamp,
                "Product ID": block.transaction.get("product_id", ""),
                "Role": block.transaction.get("role", ""),
                "Actor": block.transaction.get("actor_name", ""),
                "Location": block.transaction.get("location", ""),
                "Status": block.transaction.get("status", ""),
                "Notes": block.transaction.get("notes", ""),
                "Payment Type": block.transaction.get("payment_type", ""),
                "Payment Amount": block.transaction.get("payment_amount", 0),
                "Block #": block.index
            }
            for block in blockchain.chain
            if block.transaction.get("product_id") == search_id
        ]

        if journey:
            st.write("### Product Journey")
            df = pd.DataFrame(journey)
            df["Status"] = df["Status"].apply(lambda x: f"✅ {x}" if x=="Delivered" else x)
            st.dataframe(df)
        else:
            st.warning("No records found for this product.")

    # ==============================
    # Customer Payment Summary
    # ==============================
    st.subheader("💰 Customer Payment Summary")
    payments = [
        block.transaction
        for block in blockchain.chain[1:]  # skip genesis
        if block.transaction.get("payment_type") in ["Debit", "Credit"]
    ]

    total_debit = sum(b["payment_amount"] for b in payments if b["payment_type"]=="Debit")
    total_credit = sum(b["payment_amount"] for b in payments if b["payment_type"]=="Credit")
    balance = total_credit - total_debit

    st.write(f"**Total Debit:** ₹{total_debit}")
    st.write(f"**Total Credit:** ₹{total_credit}")
    st.write(f"**Balance:** ₹{balance}")

    # ==============================
    # Blockchain Overview
    # ==============================
    st.subheader("📦 Blockchain Overview")
    status_colors = {
        "Pending": "#FFA500", "Shipped": "#1E90FF",
        "In Transit": "#FFFF00", "Delivered": "#32CD32",
        "Returned": "#FF4500", "Cancelled": "#8B0000"
    }

    for block in blockchain.chain[1:]:  # skip genesis
        color = status_colors.get(block.transaction.get("status", ""), "#ccc")
        with st.container():
            st.markdown(
                f"""
                <div style="border:2px solid {color}; padding:12px; border-radius:10px; margin-bottom:10px;">
                <b>Block #{block.index}</b><br>
                <b>Time:</b> {block.timestamp}<br>
                <b>Product:</b> {block.transaction.get("product_id", "")}<br>
                <b>Role:</b> {block.transaction.get("role", "")}<br>
                <b>Actor:</b> {block.transaction.get("actor_name", "")}<br>
                <b>Location:</b> {block.transaction.get("location", "")}<br>
                <b>Status:</b> <span style="color:{color}; font-weight:bold">{block.transaction.get("status", "")}</span><br>
                <b>Notes:</b> {block.transaction.get("notes", "")}<br>
                <b>Payment Type:</b> {block.transaction.get("payment_type", "")} <br>
                <b>Payment Amount:</b> ₹{block.transaction.get("payment_amount",0)}<br>
                <small><b>Hash:</b> {block.hash}</small>
                </div>
                """,
                unsafe_allow_html=True
            )

# ==============================
# RIGHT SIDE → Log New Step in Sidebar
# ==============================
with st.sidebar:
    st.subheader("📝 Log a new step")

    product_id = st.text_input("Product ID")
    role = st.selectbox("Role", ["Farmer", "Wholesaler", "Distributor", "Retailer", "Customer"])
    actor_name = st.text_input("Actor name")

    location = st.selectbox("Location", ["Delhi", "Mumbai", "Chennai", "Kolkata", "Hyderabad", "Bangalore"])
    status = st.selectbox("Status", ["Pending", "Shipped", "In Transit", "Delivered", "Returned", "Cancelled"])
    notes = st.text_area("Notes")

    payment_type = st.selectbox("Payment Type", ["None", "Debit", "Credit"])
    payment_amount = st.number_input("Payment Amount", min_value=0, value=0)

    if st.button("✅ Submit transaction"):
        if product_id and actor_name:
            pt = None if payment_type == "None" else payment_type
            tx = Transaction(product_id, role, actor_name, location, status, notes, pt, payment_amount)
            blockchain.add_block(tx)
            st.success("Transaction added to blockchain!")
        else:
            st.error("Please enter Product ID and Actor name.")
