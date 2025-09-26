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
    def __init__(self, product_id, role, actor_name, location, status, notes, payment_method="", customer_name=""):
        self.product_id = product_id
        self.role = role
        self.actor_name = actor_name
        self.location = location
        self.status = status
        self.notes = notes
        self.payment_method = payment_method
        self.customer_name = customer_name
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
# Streamlit App
# ==============================
st.set_page_config(page_title="🚚 Blockchain Supply Chain Tracker", layout="wide")
st.title("🚚 Blockchain Supply Chain Tracker")

blockchain = SimpleBlockchain()

# Use session_state to store search
if "search_id" not in st.session_state:
    st.session_state.search_id = ""

# ------------------------------
# Layout
# ------------------------------
col1, col2 = st.columns([2, 1])

# ------------------------------
# RIGHT COLUMN → Log New Transaction (sticky)
# ------------------------------
with col2:
    st.subheader("📝 Log New Transaction")
    product_id = st.text_input("Product ID", key="pid2")
    role = st.selectbox("Role", ["Farmer", "Wholesaler", "Distributor", "Retailer", "Customer"])
    actor_name = st.text_input("Actor Name", key="actor")
    location = st.selectbox("Location", ["Delhi", "Mumbai", "Chennai", "Kolkata", "Hyderabad", "Bangalore"])
    status = st.selectbox("Status", ["Pending", "Shipped", "In Transit", "Delivered", "Returned", "Cancelled"])
    payment_method = st.selectbox("Payment Method", ["UPI", "Cash on Delivery", "Card", "Net Banking"])
    customer_name = ""
    if role == "Customer":
        customer_name = st.text_input("Customer Name", key="custname")
    notes = st.text_area("Notes", key="notes")

    if st.button("✅ Submit Transaction"):
        if product_id and actor_name:
            tx = Transaction(
                product_id, role, actor_name, location, status, notes,
                payment_method=payment_method, customer_name=customer_name
            )
            blockchain.add_block(tx)
            st.success("Transaction added to blockchain!")
            st.session_state.search_id = product_id  # auto set for search
        else:
            st.error("Please enter Product ID and Actor Name.")

# ------------------------------
# LEFT COLUMN → Search & Blockchain
# ------------------------------
with col1:
    st.subheader("🔎 Search Product Journey")
    search_input = st.text_input("Enter Product ID to view journey", value=st.session_state.search_id, key="search_input")
    
    if st.button("View Journey") or st.session_state.search_id:
        st.session_state.search_id = search_input
        search_id = st.session_state.search_id

        # Customer journey status
        customer_journey = [
            {"Time": block.timestamp, "Status": block.transaction.get("status", ""), "Block #": block.index}
            for block in blockchain.chain
            if block.transaction.get("product_id") == search_id and block.transaction.get("role") == "Customer"
        ]
        if customer_journey:
            st.markdown("### Product Journey (Customer Status)")
            st.dataframe(pd.DataFrame(customer_journey))
            
            # Customer Summary details
            customer_records = [
                {
                    "Payment Method": block.transaction.get("payment_method", ""),
                    "Customer Name": block.transaction.get("customer_name", ""),
                    "Product ID": block.transaction.get("product_id", ""),
                    "Actor": block.transaction.get("actor_name", ""),
                    "Location": block.transaction.get("location", "")
                }
                for block in blockchain.chain
                if block.transaction.get("product_id") == search_id and block.transaction.get("role") == "Customer"
            ]
            st.markdown("### 🧾 Customer Summary")
            st.dataframe(pd.DataFrame(customer_records))
        else:
            st.warning("No customer records found for this product.")

    # Always show blockchain overview
    st.subheader("📦 Blockchain Overview")
    for block in blockchain.chain:
        if block.index == 0:
            continue
        st.markdown(
            f"""
            <div style="border:1px solid #aaa; padding:15px; border-radius:12px; margin-bottom:12px; background-color:#fafafa;">
            <h4 style="margin-bottom:5px;">Block #{block.index}</h4>
            <b>Time:</b> {block.timestamp}<br>
            <b>Product:</b> {block.transaction.get("product_id", "")}<br>
            <b>Role:</b> {block.transaction.get("role", "")}<br>
            <b>Actor:</b> {block.transaction.get("actor_name", "")}<br>
            <b>Location:</b> {block.transaction.get("location", "")}<br>
            <b>Status:</b> {block.transaction.get("status", "")}<br>
            <b>Payment:</b> {block.transaction.get("payment_method", "")}<br>
            <b>Customer:</b> {block.transaction.get("customer_name", "")}<br>
            <b>Notes:</b> {block.transaction.get("notes", "")}<br>
            <small><b>Hash:</b> {block.hash}</small>
            </div>
            """, unsafe_allow_html=True
        )
