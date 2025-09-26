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
    def __init__(self, product_id, role, name, location, status, notes, payment_method="", customer_name=""):
        self.product_id = product_id
        self.role = role
        self.name = name  # Changed from actor_name
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
        self.save_chain()

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

# ------------------------------
# Layout Columns
# ------------------------------
col1, col2 = st.columns([2, 1])

# ------------------------------
# RIGHT COLUMN → Log Transaction
# ------------------------------
with col2:
    st.subheader("📝 Log New Transaction")

    product_id = st.text_input("Product ID", key="pid2")
    role = st.selectbox("Role", ["Farmer", "Wholesaler", "Distributor", "Retailer", "Customer"])
    name = st.text_input("Customer Name / Name", key="actor")  # Changed label here
    location = st.selectbox("Location", ["Delhi", "Mumbai", "Chennai", "Kolkata", "Hyderabad", "Bangalore"])
    status = st.selectbox("Status", ["Pending", "Shipped", "In Transit", "Delivered", "Returned", "Cancelled"])
    payment_method = st.selectbox("Payment Method", ["UPI", "Cash on Delivery", "Card", "Net Banking"])
    notes = st.text_area("Notes", key="notes")

    if st.button("✅ Submit Transaction"):
        if product_id and name:
            tx = Transaction(
                product_id, role, name, location, status, notes,
                payment_method=payment_method, customer_name=name  # Store name for customer summary
            )
            blockchain.add_block(tx)
            st.success("✅ Transaction added successfully!")
        else:
            st.error("❌ Please enter Product ID and Name.")

# ------------------------------
# LEFT COLUMN → Search & Blockchain
# ------------------------------
with col1:
    st.subheader("🔎 Search Product Journey")

    search_id = st.text_input("Enter Product ID to view journey", key="search_input")
    if st.button("View Journey"):
        if search_id.strip() == "":
            st.warning("Please enter a Product ID")
        else:
            # Customer Journey Table (Status over time)
            customer_journey = [
                {"Time": b.timestamp, "Status": b.transaction.get("status", ""), "Block #": b.index}
                for b in blockchain.chain
                if b.transaction.get("product_id") == search_id and b.transaction.get("role") == "Customer"
            ]
            if customer_journey:
                st.markdown("### Product Journey (Customer Status)")
                st.dataframe(pd.DataFrame(customer_journey))

                # Customer Summary Table (Full details)
                customer_summary = [
                    {
                        "Payment Method": b.transaction.get("payment_method", ""),
                        "Customer Name": b.transaction.get("customer_name", ""),
                        "Product ID": b.transaction.get("product_id", ""),
                        "Name": b.transaction.get("name", ""),
                        "Location": b.transaction.get("location", "")
                    }
                    for b in blockchain.chain
                    if b.transaction.get("product_id") == search_id and b.transaction.get("role") == "Customer"
                ]
                st.markdown("### 🧾 Customer Summary")
                st.dataframe(pd.DataFrame(customer_summary))
            else:
                st.warning("No customer records found for this Product ID.")

    # Blockchain Overview (Always show)
    st.subheader("📦 Blockchain Overview")
    for block in blockchain.chain:
        if block.index == 0:
            continue
        st.markdown(
            f"""
            <div style="border:1px solid #ccc; padding:12px; border-radius:10px; margin-bottom:10px; background-color:#f9f9f9;">
            <b>Block #{block.index}</b><br>
            <b>Time:</b> {block.timestamp}<br>
            <b>Product:</b> {block.transaction.get("product_id", "")}<br>
            <b>Role:</b> {block.transaction.get("role", "")}<br>
            <b>Name:</b> {block.transaction.get("name", "")}<br>
            <b>Location:</b> {block.transaction.get("location", "")}<br>
            <b>Status:</b> {block.transaction.get("status", "")}<br>
            <b>Payment:</b> {block.transaction.get("payment_method", "")}<br>
            <b>Customer:</b> {block.transaction.get("customer_name", "")}<br>
            <b>Notes:</b> {block.transaction.get("notes", "")}<br>
            <small><b>Hash:</b> {block.hash}</small>
            </div>
            """,
            unsafe_allow_html=True
        )
