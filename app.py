# app.py
# Run this with: streamlit run app.py

import streamlit as st
import hashlib
import json
import os
import uuid
from datetime import datetime

CHAIN_FILE = "blockchain.json"
USERS_FILE = "users.json"

# ---------- Default Demo Users ----------
DEFAULT_USERS = {
    "farmer": {"password": "farmer123", "role": "Farmer", "name": "Farmer A"},
    "wholesaler": {"password": "wholesaler123", "role": "Wholesaler", "name": "Wholesaler B"},
    "distributor": {"password": "distributor123", "role": "Distributor", "name": "Distributor C"},
    "retailer": {"password": "retailer123", "role": "Retailer", "name": "Retailer D"},
    "customer": {"password": "customer123", "role": "Customer", "name": "Customer E"}
}


# ---------- Blockchain Classes ----------
class Block:
    def __init__(self, index, timestamp, product_id, actor_role, actor_name, location, status, payment_method, details, previous_hash):
        self.index = index
        self.timestamp = timestamp
        self.product_id = product_id
        self.actor_role = actor_role
        self.actor_name = actor_name
        self.location = location
        self.status = status
        self.payment_method = payment_method
        self.details = details
        self.previous_hash = previous_hash
        self.hash = self.compute_hash()

    def compute_hash(self):
        block_string = json.dumps({
            'index': self.index,
            'timestamp': self.timestamp,
            'product_id': self.product_id,
            'actor_role': self.actor_role,
            'actor_name': self.actor_name,
            'location': self.location,
            'status': self.status,
            'payment_method': self.payment_method,
            'details': self.details,
            'previous_hash': self.previous_hash
        }, sort_keys=True).encode()
        return hashlib.sha256(block_string).hexdigest()

    def to_dict(self):
        return {
            'index': self.index,
            'timestamp': self.timestamp,
            'product_id': self.product_id,
            'actor_role': self.actor_role,
            'actor_name': self.actor_name,
            'location': self.location,
            'status': self.status,
            'payment_method': self.payment_method,
            'details': self.details,
            'previous_hash': self.previous_hash,
            'hash': self.hash
        }


class Blockchain:
    def __init__(self):
        self.chain = []
        if os.path.exists(CHAIN_FILE):
            self.load_from_file()
        else:
            self.create_genesis_block()

    def create_genesis_block(self):
        genesis = Block(0, self._now(), "GENESIS", "Network", "Genesis", "N/A", "Genesis Block", "N/A", "Initial block", "0")
        self.chain = [genesis]
        self.save_to_file()

    def _now(self):
        return datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')

    def add_block(self, product_id, actor_role, actor_name, location, status, payment_method, details):
        previous_block = self.chain[-1]
        new_index = previous_block.index + 1
        new_block = Block(new_index, self._now(), product_id, actor_role, actor_name, location, status, payment_method, details, previous_block.hash)
        new_block.hash = new_block.compute_hash()
        self.chain.append(new_block)
        self.save_to_file()
        return new_block

    def get_product_journey(self, product_id):
        return [b.to_dict() for b in self.chain if b.product_id == product_id]

    def save_to_file(self):
        with open(CHAIN_FILE, 'w') as f:
            json.dump([b.to_dict() for b in self.chain], f, indent=2)

    def load_from_file(self):
        with open(CHAIN_FILE, 'r') as f:
            data = json.load(f)
        self.chain = [Block(**{**item, "details": item.get("details", {} )}) for item in data]


# ---------- Utility ----------
def ensure_users_file():
    if not os.path.exists(USERS_FILE):
        with open(USERS_FILE, 'w') as f:
            json.dump(DEFAULT_USERS, f, indent=2)

def load_users():
    ensure_users_file()
    with open(USERS_FILE, 'r') as f:
        return json.load(f)


# ---------- Streamlit UI ----------
st.set_page_config(page_title="Blockchain Supply Chain Tracker", layout='wide')
bc = Blockchain()
users = load_users()

left, right = st.columns([3, 1])

# ------------------ LOGIN ------------------ #
with right:
    st.markdown("### 🔐 Login")
    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False
        st.session_state.user = None

    if not st.session_state.logged_in:
        username = st.text_input("Username")
        password = st.text_input("Password", type='password')
        if st.button("Login"):
            if username in users and users[username]['password'] == password:
                st.session_state.logged_in = True
                st.session_state.user = {"username": username, **users[username]}
                st.success(f"✅ Logged in as {users[username]['role']}")
            else:
                st.error("❌ Invalid credentials")
    else:
        st.write("**User:**", st.session_state.user['name'])
        st.write("**Role:**", st.session_state.user['role'])
        if st.button("Logout"):
            st.session_state.logged_in = False
            st.session_state.user = None
            st.experimental_rerun()


# ------------------ MAIN APP ------------------ #
with left:
    st.title("📦 Blockchain Supply Chain Tracker")

    actions, view = st.columns([1, 2])

    # ---------- ACTIONS ----------
    with actions:
        st.subheader("Actions")

        # Farmer creates product
        if st.session_state.get('logged_in') and st.session_state.user['role'] == 'Farmer':
            new_pid = st.text_input("Product ID", value=f"PRD-{uuid.uuid4().hex[:6].upper()}")
            prod_name = st.text_input("Product Name", value="Mango")
            origin_loc = st.text_input("Origin Location", value="Amritsar, Punjab")
            if st.button("Create Product"):
                details = {"product_name": prod_name}
                bc.add_block(new_pid, "Farmer", st.session_state.user['name'], origin_loc, "Created by Farmer", "COD", details)
                st.success(f"✅ Product {new_pid} created!")

        # Transfer/Update
        if st.session_state.get('logged_in') and st.session_state.user['role'] in ['Wholesaler', 'Distributor', 'Retailer']:
            t_pid = st.text_input("Product ID to update")
            t_loc = st.text_input("Location")
            t_status = st.selectbox("Status", ['Picked Up', 'In Transit', 'Received at Hub', 'Delivered to Retailer'])
            t_payment = st.selectbox("Payment Method", ['N/A', 'UPI', 'Credit Card', 'Cash on Delivery'])
            extra = st.text_area("Details")
            if st.button("Record Transaction"):
                bc.add_block(t_pid, st.session_state.user['role'], st.session_state.user['name'], t_loc, t_status, t_payment, {"notes": extra})
                st.success("✅ Transaction recorded")

        # Customer Details Form (NEW ✅)
        if st.session_state.get('logged_in') and st.session_state.user['role'] == 'Customer':
            st.markdown("### 🧑‍💻 Enter Customer Details")
            c_pid = st.text_input("Product ID to confirm")
            c_name = st.text_input("Customer Name")
            c_phone = st.text_input("Phone Number")
            c_email = st.text_input("Email")
            c_address = st.text_area("Delivery Address")
            c_payment = st.selectbox("Payment Method", ['UPI', 'Credit Card', 'Cash on Delivery'])
            c_status = st.selectbox("Delivery Status", ['Delivered', 'Returned', 'Pending'])

            if st.button("Submit Customer Details"):
                details = {
                    "customer_name": c_name,
                    "phone": c_phone,
                    "email": c_email,
                    "address": c_address
                }
                bc.add_block(c_pid, "Customer", c_name, c_address, c_status, c_payment, details)
                st.success(f"✅ Customer details saved for {c_pid}")

    # ---------- VIEW JOURNEY ----------
    with view:
        st.subheader("🔎 View Product Journey")
        search_pid = st.text_input("Enter Product ID")
        if st.button("View Journey"):
            journey = bc.get_product_journey(search_pid)
            if not journey:
                st.warning("No data found.")
            else:
                for b in journey:
                    st.markdown(f"**Block {b['index']} - {b['actor_role']}**")
                    st.write(f"Timestamp: {b['timestamp']}")
                    st.write(f"Location: {b['location']}")
                    st.write(f"Status: {b['status']}")
                    st.write(f"Payment: {b['payment_method']}")
                    st.write("Details:", b['details'])
                    st.code(f"Previous Hash: {b['previous_hash']}")
                    st.code(f"Hash: {b['hash']}")
                    st.markdown("---")

        # ---------- CUSTOMER SUMMARY ----------
        st.subheader("📄 Customer Summary")
        summary_pid = st.text_input("Product ID for Summary")
        if st.button("Show Summary"):
            journey = bc.get_product_journey(summary_pid)
            if not journey:
                st.warning("No data found.")
            else:
                final = journey[-1]
                first = journey[0]
                product_name = first.get('details', {}).get('product_name', 'Unknown')

                st.write(f"**Product ID:** {summary_pid}")
                st.write(f"**Product Name:** {product_name}")
                st.write(f"**Origin:** {first['location']}")
                st.write(f"**Final Location:** {final['location']}")
                st.write(f"**Status:** {final['status']}")
                st.write(f"**Payment:** {final['payment_method']}")
                st.write("**Customer Details:**")
                st.json(final['details'])
