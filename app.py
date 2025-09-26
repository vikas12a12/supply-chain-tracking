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
    def __init__(self, product_id, role, actor_name, location, status, notes):
        self.product_id = product_id
        self.role = role
        self.actor_name = actor_name
        self.location = location
        self.status = status
        self.notes = notes
        self.timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

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

# Layout: left (search & blocks) | right (log transaction)
col1, col2 = st.columns([2, 1])

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
                "Block #": block.index
            }
            for block in blockchain.chain
            if block.transaction.get("product_id") == search_id
        ]

        if journey:
            st.write("### Product Journey")
            st.dataframe(pd.DataFrame(journey))
        else:
            st.warning("No records found for this product.")

    st.subheader("📦 Blockchain Overview")
    for block in blockchain.chain:
        if block.index == 0:
            continue
        with st.container():
            st.markdown(
                f"""
                <div style="border:1px solid #444; padding:12px; border-radius:10px; margin-bottom:10px;">
                <b>Block #{block.index}</b><br>
                <b>Time:</b> {block.timestamp}<br>
                <b>Product:</b> {block.transaction.get("product_id", "")}<br>
                <b>Role:</b> {block.transaction.get("role", "")}<br>
                <b>Actor:</b> {block.transaction.get("actor_name", "")}<br>
                <b>Location:</b> {block.transaction.get("location", "")}<br>
                <b>Status:</b> {block.transaction.get("status", "")}<br>
                <b>Notes:</b> {block.transaction.get("notes", "")}<br>
                <small><b>Hash:</b> {block.hash[:20]}...</small>
                </div>
                """,
                unsafe_allow_html=True
            )

# ==============================
# RIGHT SIDE → Log New Step
# ==============================
with col2:
    st.subheader("📝 Log a new step")

    product_id = st.text_input("Product ID")
    role = st.selectbox("Role", ["Farmer", "Wholesaler", "Distributor", "Retailer", "Customer"])
    actor_name = st.text_input("Actor name")

    location = st.selectbox("Location", ["Delhi", "Mumbai", "Chennai", "Kolkata", "Hyderabad", "Bangalore"])
    status = st.selectbox("Status", ["Pending", "Shipped", "In Transit", "Delivered", "Returned", "Cancelled"])
    notes = st.text_area("Notes")

    if st.button("✅ Submit transaction"):
        if product_id and actor_name:
            tx = Transaction(product_id, role, actor_name, location, status, notes)
            blockchain.add_block(tx)
            st.success("Transaction added to blockchain!")
        else:
            st.error("Please enter Product ID and Actor name.")
