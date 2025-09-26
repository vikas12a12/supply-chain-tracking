# app.py
# Streamlit: Blockchain-based Supply Chain Tracker (demo, corrected)
# Run: streamlit run app.py

import streamlit as st
import hashlib
import json
import os
import uuid
from datetime import datetime

# ---------- Files ----------
CHAIN_FILE = "blockchain.json"
USERS_FILE = "users.json"

# ---------- Demo users ----------
DEFAULT_USERS = {
    "farmer": {"password": "farmer123", "role": "Farmer", "name": "Farmer A"},
    "wholesaler": {"password": "wholesaler123", "role": "Wholesaler", "name": "Wholesaler B"},
    "distributor": {"password": "distributor123", "role": "Distributor", "name": "Distributor C"},
    "retailer": {"password": "retailer123", "role": "Retailer", "name": "Retailer D"},
    "customer": {"password": "customer123", "role": "Customer", "name": "Customer E"}
}

# ---------- Blockchain implementation ----------
class Block:
    def __init__(self, index, timestamp, product_id, actor_role, actor_name, location,
                 status, payment_method, details, previous_hash):
        # core fields
        self.index = index
        self.timestamp = timestamp
        self.product_id = product_id
        self.actor_role = actor_role
        self.actor_name = actor_name
        self.location = location
        self.status = status
        self.payment_method = payment_method
        # details should be a serializable object (dict/string)
        self.details = details if details is not None else {}
        self.previous_hash = previous_hash
        # compute hash on creation (will be overwritten when loading from file)
        self.hash = self.compute_hash()

    def compute_hash(self):
        # build a canonical representation and hash it
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
        block_string = json.dumps(block_content, sort_keys=True, separators=(',', ':')).encode()
        return hashlib.sha256(block_string).hexdigest()

    def to_dict(self):
        return {
            "index": self.index,
            "timestamp": self.timestamp,
            "product_id": self.product_id,
            "actor_role": self.actor_role,
            "actor_name": self.actor_name,
            "location": self.location,
            "status": self.status,
            "payment_method": self.payment_method,
            "details": self.details,
            "previous_hash": self.previous_hash,
            "hash": self.hash
        }


class Blockchain:
    def __init__(self, chain_file=CHAIN_FILE):
        self.chain_file = chain_file
        self.chain = []
        if os.path.exists(self.chain_file):
            try:
                self.load_from_file()
            except Exception:
                # if loading fails, start fresh
                self.create_genesis_block()
        else:
            self.create_genesis_block()

    def _now(self):
        return datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")

    def create_genesis_block(self):
        genesis = Block(
            index=0,
            timestamp=self._now(),
            product_id="GENESIS",
            actor_role="Network",
            actor_name="Genesis",
            location="N/A",
            status="Genesis Block",
            payment_method="N/A",
            details={"note": "Initial genesis block"},
            previous_hash="0"
        )
        genesis.hash = genesis.compute_hash()
        self.chain = [genesis]
        self.save_to_file()

    def add_block(self, product_id, actor_role, actor_name, location, status, payment_method, details):
        previous = self.chain[-1]
        new_index = previous.index + 1
        new_block = Block(
            index=new_index,
            timestamp=self._now(),
            product_id=product_id,
            actor_role=actor_role,
            actor_name=actor_name,
            location=location,
            status=status,
            payment_method=payment_method,
            details=details,
            previous_hash=previous.hash
        )
        new_block.hash = new_block.compute_hash()
        self.chain.append(new_block)
        self.save_to_file()
        return new_block

    def is_chain_valid(self):
        # Walk the chain and verify the hashes and links
        for i in range(1, len(self.chain)):
            current = self.chain[i]
            previous = self.chain[i - 1]
            if current.previous_hash != previous.hash:
                return False, f"Broken link: block {i-1} -> {i}"
            expected_hash = current.compute_hash()
            if current.hash != expected_hash:
                return False, f"Hash mismatch at block {i}"
        return True, "Chain is valid"

    def get_product_journey(self, product_id):
        return [b.to_dict() for b in self.chain if b.product_id == product_id]

    def save_to_file(self):
        try:
            with open(self.chain_file, "w") as f:
                json.dump([b.to_dict() for b in self.chain], f, indent=2)
        except Exception as e:
            raise IOError(f"Failed to save chain to {self.chain_file}: {e}")

    def load_from_file(self):
        with open(self.chain_file, "r") as f:
            data = json.load(f)
        self.chain = []
        for item in data:
            # ensure keys exist with safe defaults
            idx = item.get("index", 0)
            ts = item.get("timestamp", self._now())
            pid = item.get("product_id", "")
            arole = item.get("actor_role", "")
            aname = item.get("actor_name", "")
            loc = item.get("location", "")
            status = item.get("status", "")
            pay = item.get("payment_method", "")
            details = item.get("details", {})
            prev = item.get("previous_hash", "0")
            stored_hash = item.get("hash", None)

            b = Block(idx, ts, pid, arole, aname, loc, status, pay, details, prev)
            # preserve stored hash (so we can detect tampering later)
            if stored_hash:
                b.hash = stored_hash
            else:
                b.hash = b.compute_hash()
            self.chain.append(b)


# ---------- Utilities: users ----------
def ensure_users_file():
    if not os.path.exists(USERS_FILE):
        with open(USERS_FILE, "w") as f:
            json.dump(DEFAULT_USERS, f, indent=2)


def load_users():
    ensure_users_file()
    with open(USERS_FILE, "r") as f:
        return json.load(f)


def save_users(users):
    with open(USERS_FILE, "w") as f:
        json.dump(users, f, indent=2)


# ---------- Streamlit app ----------
st.set_page_config(page_title="Blockchain Supply Chain Tracker", layout="wide")
st.title("📦 Blockchain Supply Chain Tracker (Demo)")

# Initialize objects
bc = Blockchain()
users = load_users()

# Session state defaults
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.user = None

# Layout: left main, right login
left_col, right_col = st.columns([3, 1])

with right_col:
    st.markdown("### 🔐 Login (right)")
    if not st.session_state.logged_in:
        username = st.text_input("Username", key="login_username")
        password = st.text_input("Password", type="password", key="login_password")
        if st.button("Login", key="login_button"):
            if username and (username in users) and users[username]["password"] == password:
                st.session_state.logged_in = True
                st.session_state.user = {"username": username, **users[username]}
                st.success(f"Logged in as {users[username]['role']}: {users[username]['name']}")
            else:
                st.error("Invalid credentials (demo). Try: farmer/farmer123, customer/customer123, etc.")
    else:
        st.write("**User:**", st.session_state.user.get("name"))
        st.write("**Role:**", st.session_state.user.get("role"))
        if st.button("Logout", key="logout_button"):
            st.session_state.logged_in = False
            st.session_state.user = None
            st.experimental_rerun()

with left_col:
    # Chain health
    valid, message = bc.is_chain_valid()
    if valid:
        st.success(f"Chain status: {message}")
    else:
        st.error(f"Chain status: {message}")

    # Action & view columns
    actions_col, view_col = st.columns([1, 2])

    # ---------- Actions ----------
    with actions_col:
        st.subheader("Actions")

        # Farmer: create product
        if st.session_state.logged_in and st.session_state.user.get("role") == "Farmer":
            st.markdown("**Create new product**")
            new_pid = st.text_input("Product ID", value=f"PRD-{uuid.uuid4().hex[:6].upper()}", key="create_pid")
            prod_name = st.text_input("Product Name", value="Mango", key="create_prod_name")
            origin_loc = st.text_input("Origin Location", value="Amritsar, Punjab", key="create_origin")
            if st.button("Create Product", key="create_product_btn"):
                if not new_pid.strip():
                    st.error("Product ID required.")
                else:
                    details = {"product_name": prod_name}
                    block = bc.add_block(new_pid.strip(), "Farmer", st.session_state.user.get("name"), origin_loc, "Created", "COD", details)
                    st.success(f"Product {new_pid} created in block {block.index}")

        # Wholesaler/Distributor/Retailer: update product
        if st.session_state.logged_in and st.session_state.user.get("role") in ["Wholesaler", "Distributor", "Retailer"]:
            st.markdown("**Update / Transfer Product**")
            t_pid = st.text_input("Product ID to update", key="update_pid")
            t_loc = st.text_input("Location", key="update_loc")
            t_status = st.selectbox("Status", ["Picked Up", "In Transit", "Received at Hub", "Delivered to Retailer", "Quality Checked"], key="update_status")
            t_payment = st.selectbox("Payment Method", ["N/A", "UPI", "Credit Card", "Cash on Delivery"], key="update_payment")
            extra = st.text_area("Details (notes)", key="update_notes")
            if st.button("Record Transaction", key="record_tx_btn"):
                if not t_pid.strip():
                    st.error("Product ID required.")
                else:
                    details = {"notes": extra}
                    block = bc.add_block(t_pid.strip(), st.session_state.user.get("role"), st.session_state.user.get("name"), t_loc, t_status, t_payment, details)
                    st.success(f"Recorded update for {t_pid} in block {block.index}")

        # Customer: detailed form
        if st.session_state.logged_in and st.session_state.user.get("role") == "Customer":
            st.markdown("### Customer: Enter details & confirm delivery")
            c_pid = st.text_input("Product ID to confirm", key="cust_pid")
            c_name = st.text_input("Customer Name", value=st.session_state.user.get("name", ""), key="cust_name")
            c_phone = st.text_input("Phone Number", key="cust_phone")
            c_email = st.text_input("Email", key="cust_email")
            c_address = st.text_area("Delivery Address", key="cust_address")
            c_payment = st.selectbox("Payment Method", ["UPI", "Credit Card", "Cash on Delivery"], key="cust_payment")
            c_status = st.selectbox("Delivery Status", ["Delivered", "Returned", "Pending"], key="cust_status")
            if st.button("Submit Customer Details", key="cust_submit_btn"):
                if not c_pid.strip():
                    st.error("Product ID required.")
                elif not c_name.strip():
                    st.error("Customer name required.")
                else:
                    details = {
                        "customer_name": c_name.strip(),
                        "phone": c_phone.strip(),
                        "email": c_email.strip(),
                        "address": c_address.strip()
                    }
                    block = bc.add_block(c_pid.strip(), "Customer", c_name.strip(), c_address.strip() or "Unknown", c_status, c_payment, details)
                    st.success(f"Customer details saved for {c_pid} in block {block.index}")

        st.markdown("---")
        st.markdown("**Utilities**")
        # Download chain button
        if st.button("Export chain to JSON (save & prepare download)", key="export_prep_btn"):
            # save file (already saved on add_block) to ensure freshest
            bc.save_to_file()
            st.success(f"Saved chain to {CHAIN_FILE}")
        # Provide a direct download button
        try:
            chain_json_str = json.dumps([b.to_dict() for b in bc.chain], indent=2)
            st.download_button("Download chain JSON", data=chain_json_str, file_name="blockchain_export.json", mime="application/json", key="download_chain_btn")
        except Exception:
            # In some environments download_button might fail quietly; ignore
            pass

        if st.button("Reset chain to genesis (Danger)", key="reset_chain_btn"):
            bc.create_genesis_block()
            st.success("Chain reset to genesis. All previous blocks removed.")

    # ---------- View & Summary ----------
    with view_col:
        st.subheader("🔎 View Product Journey")
        search_pid = st.text_input("Enter Product ID to view", key="view_search_pid")
        if st.button("View Journey", key="view_journey_btn"):
            if not search_pid.strip():
                st.error("Enter a Product ID.")
            else:
                journey = bc.get_product_journey(search_pid.strip())
                if not journey:
                    st.warning("No records found for this Product ID.")
                else:
                    st.markdown(f"### Journey for **{search_pid.strip()}**")
                    for b in journey:
                        st.markdown(f"**Block {b['index']} — {b['actor_role']} ({b['actor_name']})**")
                        st.write(f"- Timestamp: {b['timestamp']}")
                        st.write(f"- Location: {b['location']}")
                        st.write(f"- Status: {b['status']}")
                        st.write(f"- Payment: {b['payment_method']}")
                        st.write("- Details:")
                        st.json(b.get("details", {}))
                        st.code(f"Previous Hash: {b['previous_hash']}")
                        st.code(f"Hash: {b['hash']}")
                        st.markdown("---")

        st.subheader("📄 Customer Summary (separate)")
        summary_pid = st.text_input("Product ID for customer summary", key="summary_pid")
        if st.button("Show Customer Summary", key="summary_btn"):
            if not summary_pid.strip():
                st.error("Enter a Product ID.")
            else:
                journey = bc.get_product_journey(summary_pid.strip())
                if not journey:
                    st.warning("No records found for this Product ID.")
                else:
                    first = journey[0]
                    final = journey[-1]
                    product_name = first.get("details", {}).get("product_name", "Unknown")
                    st.markdown(f"### Final Customer Summary for **{summary_pid.strip()}**")
                    st.write(f"**Product ID:** {summary_pid.strip()}")
                    st.write(f"**Product Name:** {product_name}")
                    st.write(f"**Origin:** {first.get('location','Unknown')}")
                    st.write(f"**Final Location:** {final.get('location','Unknown')}")
                    st.write(f"**Delivery Status:** {final.get('status','Unknown')}")
                    st.write(f"**Final Payment Method:** {final.get('payment_method','Unknown')}")
                    st.markdown("**Customer Details (from final block):**")
                    st.json(final.get("details", {}))

    st.markdown("---")
    st.subheader("Blockchain Explorer")
    if st.checkbox("Show full chain", key="show_full_chain"):
        for b in bc.chain:
            st.write(f"Index {b.index} | Product: {b.product_id} | Actor: {b.actor_role} ({b.actor_name}) | Time: {b.timestamp}")
            st.code(f"Prev: {b.previous_hash}")
            st.code(f"Hash: {b.hash}")
            st.markdown("---")

    st.caption("Demo accounts — farmer/farmer123, wholesaler/wholesaler123, distributor/distributor123, retailer/retailer123, customer/customer123")
