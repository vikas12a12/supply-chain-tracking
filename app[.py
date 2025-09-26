# app.py
# Streamlit Blockchain Supply Chain Tracker with Product ID + Customer Details
# Run: streamlit run app.py

import streamlit as st
import hashlib
import json
import os
import uuid
from datetime import datetime

CHAIN_FILE = "blockchain.json"
USERS_FILE = "users.json"

# Demo users
DEFAULT_USERS = {
    "farmer": {"password": "farmer123", "role": "Farmer", "name": "Farmer A"},
    "wholesaler": {"password": "wholesaler123", "role": "Wholesaler", "name": "Wholesaler B"},
    "distributor": {"password": "distributor123", "role": "Distributor", "name": "Distributor C"},
    "retailer": {"password": "retailer123", "role": "Retailer", "name": "Retailer D"},
    "customer": {"password": "customer123", "role": "Customer", "name": "Customer E"}
}

# -------- Blockchain Classes --------
class Block:
    def __init__(self, index, timestamp, product_id, actor_role, actor_name, location,
                 status, payment_method, details, previous_hash):
        self.index = index
        self.timestamp = timestamp
        self.product_id = product_id
        self.actor_role = actor_role
        self.actor_name = actor_name
        self.location = location
        self.status = status
        self.payment_method = payment_method
        self.details = details if details else {}
        self.previous_hash = previous_hash
        self.hash = self.compute_hash()

    def compute_hash(self):
        block_content = {
            "index": self.index,
            "timestamp": self.timestamp,
            "product_id": self.product_id,
            "actor_role": self.actor_role,
            "actor_name": self.actor_name,
            "location": self.location,
            "status": self.status,
            "payment_method": self.payment_method,
            "details": self.details,
            "previous_hash": self.previous_hash
        }
        return hashlib.sha256(json.dumps(block_content, sort_keys=True).encode()).hexdigest()

    def to_dict(self):
        return self.__dict__

class Blockchain:
    def __init__(self):
        self.chain = []
        if os.path.exists(CHAIN_FILE):
            self.load_from_file()
        else:
            self.create_genesis_block()

    def _now(self):
        return datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")

    def create_genesis_block(self):
        genesis = Block(0, self._now(), "GENESIS", "Network", "Genesis", "N/A",
                        "Genesis Block", "N/A", {"note": "Initial genesis block"}, "0")
        self.chain = [genesis]
        self.save_to_file()

    def add_block(self, product_id, actor_role, actor_name, location, status, payment_method, details):
        prev = self.chain[-1]
        block = Block(len(self.chain), self._now(), product_id, actor_role, actor_name,
                      location, status, payment_method, details, prev.hash)
        self.chain.append(block)
        self.save_to_file()
        return block

    def get_product_journey(self, product_id):
        return [b.to_dict() for b in self.chain if b.product_id == product_id]

    def save_to_file(self):
        with open(CHAIN_FILE, "w") as f:
            json.dump([b.to_dict() for b in self.chain], f, indent=2)

    def load_from_file(self):
        with open(CHAIN_FILE, "r") as f:
            data = json.load(f)
        self.chain = []
        for item in data:
            b = Block(item["index"], item["timestamp"], item["product_id"], item["actor_role"],
                      item["actor_name"], item["location"], item["status"], item["payment_method"],
                      item.get("details", {}), item["previous_hash"])
            b.hash = item.get("hash", b.compute_hash())
            self.chain.append(b)

# -------- Users --------
def ensure_users_file():
    if not os.path.exists(USERS_FILE):
        with open(USERS_FILE, "w") as f:
            json.dump(DEFAULT_USERS, f, indent=2)

def load_users():
    ensure_users_file()
    with open(USERS_FILE, "r") as f:
        return json.load(f)

# -------- Streamlit UI --------
st.set_page_config(page_title="Blockchain Supply Chain Tracker", layout="wide")
st.title("📦 Blockchain Supply Chain Tracker")

bc = Blockchain()
users = load_users()

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.user = None

left_col, right_col = st.columns([3,1])

# ---------- Login ----------
with right_col:
    st.markdown("### 🔐 Login")
    if not st.session_state.logged_in:
        username = st.text_input("Username", key="login_username")
        password = st.text_input("Password", type="password", key="login_password")
        if st.button("Login", key="login_btn"):
            if username in users and users[username]["password"] == password:
                st.session_state.logged_in = True
                st.session_state.user = {"username": username, **users[username]}
                st.success(f"Logged in as {users[username]['role']}")
            else:
                st.error("Invalid credentials")
    else:
        st.write("**User:**", st.session_state.user.get("name"))
        st.write("**Role:**", st.session_state.user.get("role"))
        if st.button("Logout", key="logout_btn"):
            st.session_state.logged_in = False
            st.session_state.user = None
            st.experimental_rerun()

# ---------- Actions ----------
with left_col:
    actions_col, view_col = st.columns([1,2])
    with actions_col:
        st.subheader("Actions")

        # Customer: Add product ID + customer details
        if st.session_state.logged_in and st.session_state.user["role"] == "Customer":
            st.markdown("### Add Product ID & Customer Details")
            product_id = st.text_input("Product ID", key="cust_product_id")
            customer_id = st.text_input("Customer ID", key="cust_id")
            name = st.text_input("Customer Name", value=st.session_state.user.get("name",""))
            phone = st.text_input("Phone")
            email = st.text_input("Email")
            address = st.text_area("Address")
            payment = st.selectbox("Payment Method", ["UPI","Credit Card","Cash on Delivery"])
            status = st.selectbox("Delivery Status", ["Delivered","Returned","Pending"])

            if st.button("Submit Customer Info"):
                if not (product_id.strip() and customer_id.strip() and name.strip()):
                    st.error("Product ID, Customer ID, and Name are required")
                else:
                    details = {
                        "customer_id": customer_id,
                        "customer_name": name,
                        "phone": phone,
                        "email": email,
                        "address": address
                    }
                    bc.add_block(product_id.strip(), "Customer", name.strip(), address.strip() or "Unknown",
                                 status, payment, details)
                    st.success(f"Customer details saved for Product {product_id}")

    # ---------- View ----------
    with view_col:
        st.subheader("🔎 View Product Journey")
        search_pid = st.text_input("Enter Product ID to view journey", key="view_pid")
        if st.button("View Journey"):
            journey = bc.get_product_journey(search_pid.strip())
            if not journey:
                st.warning("No records found")
            else:
                for b in journey:
                    st.markdown(f"**Block {b['index']} — {b['actor_role']} ({b['actor_name']})**")
                    st.write(f"- Timestamp: {b['timestamp']}")
                    st.write(f"- Location: {b['location']}")
                    st.write(f"- Status: {b['status']}")
                    st.write(f"- Payment: {b['payment_method']}")
                    st.write("Details:")
                    st.json(b['details'])
                    st.code(f"Previous Hash: {b['previous_hash']}")
                    st.code(f"Hash: {b['hash']}")
                    st.markdown("---")

        st.subheader("📄 Customer Summary")
        summary_pid = st.text_input("Product ID for customer summary", key="summary_pid")
        if st.button("Show Customer Summary"):
            journey = bc.get_product_journey(summary_pid.strip())
            if not journey:
                st.warning("No records found")
            else:
                final = journey[-1]
                st.write(f"**Product ID:** {summary_pid.strip()}")
                st.write(f"**Delivery Status:** {final['status']}")
                st.write(f"**Payment Method:** {final['payment_method']}")
                st.write("**Customer Details:**")
                st.json(final.get("details", {}))
