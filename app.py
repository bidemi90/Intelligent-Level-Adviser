import streamlit as st
import hashlib
import os
import re
from pymongo import MongoClient
from dotenv import load_dotenv

# Initialize Configuration
load_dotenv()
st.set_page_config(page_title="Academic Adviser | Login", layout="centered")

# Hide Sidebar on Auth Page
st.markdown(
    """
    <style>
        [data-testid="stSidebarNav"] {display: none;}
    </style>
    """,
    unsafe_allow_html=True,
)

# Database Connection
client = MongoClient(os.getenv("MONGO_URI"))
db = client["LevelAdviser"]
users_col = db["users"]

# Helper Functions
def hash_password(password):
    return hashlib.sha256(str.encode(password)).hexdigest()

def validate_password(password):
    if len(password) < 8:
        return False, "Password must be at least 8 characters long."
    if not re.search(r"[A-Za-z]", password):
        return False, "Password must contain at least one letter."
    if not re.search(r"[0-9]", password):
        return False, "Password must contain at least one number."
    return True, "Valid"

# Session State Initialization
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

# Authentication UI
if not st.session_state.logged_in:
    st.title("🎓 Intelligent Level Adviser")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        tab1, tab2 = st.tabs(["Login", "Register"])
        
        # --- LOGIN TAB ---
        with tab1:
            with st.form("login_form", clear_on_submit=False):
                l_user = st.text_input("Student ID")
                l_pass = st.text_input("Password", type="password")
                submit_login = st.form_submit_button("Sign In", use_container_width=True)
                
                if submit_login:
                    user = users_col.find_one({"username": l_user, "password": hash_password(l_pass)})
                    if user:
                        st.session_state.logged_in = True
                        st.session_state.user_id = l_user
                        st.session_state.full_name = user.get("full_name", "")
                        st.switch_page("pages/2_Chat.py")
                    else:
                        st.error("Invalid Student ID or Password")

        # --- REGISTER TAB ---
        with tab2:
            with st.form("register_form", clear_on_submit=True):
                r_name = st.text_input("Full Name")
                r_user = st.text_input("Student ID")
                r_pass = st.text_input("Password", type="password")
                r_pass_confirm = st.text_input("Confirm Password", type="password")
                submit_reg = st.form_submit_button("Create Account", use_container_width=True)
                
                if submit_reg:
                    if not r_name or not r_user or not r_pass:
                        st.error("All fields are required.")
                    elif r_pass != r_pass_confirm:
                        st.error("Passwords do not match.")
                    else:
                        is_valid, msg = validate_password(r_pass)
                        if not is_valid:
                            st.error(msg)
                        elif users_col.find_one({"username": r_user}): 
                            st.error("Student ID already exists in the system.")
                        else:
                            # Insert new user with profile schema placeholders
                            new_user_data = {
                                "username": r_user,
                                "full_name": r_name,
                                "password": hash_password(r_pass),
                                "department": "",
                                "level": "",
                                "cgpa": "",
                                "profile_setup_complete": False
                            }
                            users_col.insert_one(new_user_data)
                            st.success("Account created successfully. Proceed to Login.")

else:
    st.switch_page("pages/2_Chat.py")