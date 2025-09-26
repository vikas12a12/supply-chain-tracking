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
    def __init__(self, product_id, product_name, role, actor_name, location, status, notes, payment_method=None):
        self.product_id = product_id
        self.product_name = product_name
        self.role = role
        self.actor_name = actor_name
        self.location = location
        self.status = status
        self.notes = notes
        self.timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.payment_method = payment_method

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

# ==============================
# LEFT SIDE → Search & Product Journey
# ==============================
st.subheader("🔎 Search product journey")

search_id = st.text_input("Enter Product ID to view journey", "")
if st.button("View journey"):
    journey = [
        {
            "Time": block.timestamp,
            "Product ID": block.transaction.get("product_id", ""),
            "Product Name": block.transaction.get("product_name", ""),
            "Role": block.transaction.get("role", ""),
            "Actor": block.transaction.get("actor_name", ""),
            "Location": block.transaction.get("location", ""),
            "Status": block.transaction.get("status", ""),
            "Notes": block.transaction.get("notes", ""),
            "Payment Method": block.transaction.get("payment_method", ""),
            "Block #": block.index
        }
        for block in blockchain.chain
        if block.transaction.get("product_id") == search_id
    ]

    if journey:
        st.write("### Product Journey")
        df = pd.DataFrame(journey)
        df["Status"] = df["Status"].apply(lambda x: f"✅ {x}" if x == "Delivered" else x)
        st.dataframe(df)

        # ==============================
        # Customer Payment Summary
        # ==============================
        st.subheader("💰 Customer Payment Summary")
        last_tx = journey[-1]  # Show latest transaction
        st.write(f"*Customer Name:* {last_tx['Actor']}")
        st.write(f"*Product Name:* {last_tx['Product Name']}")
        st.write(f"*Product ID:* {last_tx['Product ID']}")
        st.write(f"*Place:* {last_tx['Location']}")
        st.write(f"*Payment Method:* {last_tx['Payment Method']}")
        st.write(f"*Status:* {last_tx['Status']}")
    else:
        st.warning("No records found for this product.")

# ==============================
# Blockchain Overview
# ==============================
st.subheader("📦 Blockchain Overview")
status_colors = {
    "Pending": "#FFA500", "Shipped": "#1E90FF", "Dispatched": "#1E90FF",
    "In Transit": "#FFFF00", "Delivered": "#32CD32", "Returned": "#FF4500",
    "Cancelled": "#8B0000", "Paid": "#32CD32"
}

for block in blockchain.chain[1:]:  # skip genesis
    color = status_colors.get(block.transaction.get("status", ""), "#ccc")
    with st.container():
        st.markdown(
            f"""
            <div style="border:2px solid {color}; padding:12px; border-radius:10px; margin-bottom:10px;">
            <b>Block #{block.index}</b><br>
            <b>Time:</b> {block.timestamp}<br>
            <b>Product:</b> {block.transaction.get("product_name", "")} (ID: {block.transaction.get("product_id", "")})<br>
            <b>Role:</b> {block.transaction.get("role", "")}<br>
            <b>Actor:</b> {block.transaction.get("actor_name", "")}<br>
            <b>Location:</b> {block.transaction.get("location", "")}<br>
            <b>Status:</b> <span style="color:{color}; font-weight:bold">{block.transaction.get("status", "")}</span><br>
            <b>Notes:</b> {block.transaction.get("notes", "")}<br>
            <b>Payment Method:</b> {block.transaction.get("payment_method", "")}<br>
            </div>
            """,
            unsafe_allow_html=True
        )

# ==============================
# RIGHT SIDE → Log Transaction with Place & Status
# ==============================
with st.sidebar:
    st.subheader("📝 Log Transaction / Payment")

    product_id = st.text_input("Product ID for Transaction")
    product_name = st.text_input("Product Name")
    actor_name = st.text_input("Customer / Actor Name")

    # Place selection
    location = st.selectbox("Place", ["Delhi", "Mumbai", "Chennai", "Kolkata", "Hyderabad", "Bangalore"])

    # Status selection
    status = st.selectbox(
        "Status",
        ["Pending", "Shipped", "Dispatched", "In Transit", "Delivered", "Returned", "Cancelled", "Paid"]
    )

    # Payment method
    payment_method = st.selectbox("Payment Method", ["UPI", "Cash on Delivery", "Card", "Net Banking"])

    if st.button("✅ Submit Transaction"):
        if product_id and product_name and actor_name:
            tx = Transaction(
                product_id=product_id,
                product_name=product_name,
                role="Customer",
                actor_name=actor_name,
                location=location,
                status=status,
                notes="Logged via sidebar",
                payment_method=payment_method
            )
            blockchain.add_block(tx)
            st.success("Transaction logged successfully!")
        else:
            st.error("Please enter Product ID, Product Name, and Customer Name.")
