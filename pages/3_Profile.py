import streamlit as st
import os
import cloudinary
import cloudinary.uploader
from pymongo import MongoClient

# 1. Page Config
st.set_page_config(page_title="Adviser | Profile", layout="centered", initial_sidebar_state="collapsed")

# 2. CSS Configuration
st.markdown("""
<style>
    [data-testid="stSidebarNav"] {display: none !important;}
    .profile-container {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        text-align: center;
    }
    .profile-pic {
        width: 150px;
        height: 150px;
        border-radius: 50%;
        object-fit: cover;
        border: 3px solid #2C666E;
        margin-bottom: 10px;
    }
</style>
""", unsafe_allow_html=True)

# Security Check
if not st.session_state.get('logged_in'):
    st.warning("Unauthorized. Please Login.")
    st.stop()

user_id = st.session_state.user_id

# Database & Cloudinary Connection
client = MongoClient(os.getenv("MONGO_URI"))
db = client["LevelAdviser"]
users_col = db["users"]

cloudinary.config(
    cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
    api_key=os.getenv("CLOUDINARY_API_KEY"),
    api_secret=os.getenv("CLOUDINARY_API_SECRET")
)

# Initialize Edit Mode in Session State
if "edit_mode" not in st.session_state:
    st.session_state.edit_mode = False

# Fetch fresh user data
user_data = users_col.find_one({"username": user_id})

# --- UI START ---
st.title("👤 My Academic Profile")
st.divider()

# Profile Image Section (Circle)
st.markdown('<div class="profile-container">', unsafe_allow_html=True)
current_pic = user_data.get("profile_pic", "https://res.cloudinary.com/demo/image/upload/d_avatar.png/avatar.jpg")
st.markdown(f'<img src="{current_pic}" class="profile-pic">', unsafe_allow_html=True)

# Upload Button (Modal/Dialog)
@st.dialog("Upload New Profile Photo")
def upload_dialog():
    uploaded_file = st.file_uploader("Choose image", type=["jpg", "png", "jpeg"])
    if st.button("Confirm Upload", type="primary"):
        if uploaded_file:
            with st.spinner("Updating photo..."):
                res = cloudinary.uploader.upload(uploaded_file, folder="profiles")
                users_col.update_one({"username": user_id}, {"$set": {"profile_pic": res['secure_url']}})
                st.rerun()

if st.button("Upload Profile Image"):
    upload_dialog()
st.markdown('</div>', unsafe_allow_html=True)

st.divider()

# 3. SIDEBAR
with st.sidebar:
    st.title("🎓 Menu")
    st.write(f"Student: **{user_id}**")
    st.divider()
    if st.button("🗨️ Chat", use_container_width=True):
        st.switch_page("pages/2_Chat.py")
    if st.button("📁 Documents", use_container_width=True):
        st.switch_page("pages/1_Documents.py")
    if st.button("👤 Profile", use_container_width=True):
        st.switch_page("pages/3_Profile.py")
    if st.button("🗺️ Roadmap", use_container_width=True):
        st.switch_page("pages/4_Roadmap.py")
    if st.button("Logout", use_container_width=True):
        st.session_state.clear()
        st.switch_page("app.py")

# --- PROFILE DETAILS SECTION ---
if not st.session_state.edit_mode:
    # VIEW MODE
    st.write(f"**Full Name:** {user_data.get('full_name', 'Not set')}")
    st.write(f"**Student ID:** {user_id}")
    st.write(f"**Department:** {user_data.get('department', 'Not set')}")
    st.write(f"**Current Level:** {user_data.get('level', 'Not set')}")
    st.write(f"**CGPA:** {user_data.get('cgpa', '0.00')}")
    
    if st.button("Edit Profile", use_container_width=True):
        st.session_state.edit_mode = True
        st.rerun()
else:
    # EDIT MODE
    with st.form("edit_profile_form"):
        new_name = st.text_input("Full Name", value=user_data.get("full_name", ""))
        
        dept_options = [
            "Accounting", "Agricultural and Bio-Resources", "Agricultural Economics and Extension",
            "Agricultural Education", "Animal and Environmental Biology", "Animal Production and Health",
            "Banking and Finance", "Biochemistry", "Biology Education", "Business Administration",
            "Business Education", "Chemistry Education", "Civil Engineering", "Computer Engineering",
            "Computer Sciences", "Criminology and Security Studies", "Crop Science and Horticulture",
            "Demography and Social Statistics", "Economics and Development Studies", "Educational Foundation",
            "Educational Management", "Electrical and Electronics Engineering", "English and Literary Studies",
            "English Education", "Fishery and Aquaculture", "Food Science and Technology", "General Studies",
            "Geology", "Geophysics", "History and International Relations", "Hospitality and Tourism Management",
            "Industrial Chemistry", "Library and Information Science", "Linguistics and languages",
            "Mass Communication", "Mathematics", "Mathematics Education", "Mechanical Engineering",
            "Mechatronics Engineering", "Metallurgical and Materials Engineering", "Microbiology",
            "Peace and Conflict Resolution", "Physics", "Plant Science and Biotechnology", "Political Science",
            "Psychology", "Public Administration", "Sociology", "Soil Science", "Theater and Media Arts",
            "Water Resources Management and Agrometrology", "Software Engineering", "Cybersecurity",
            "Information Technology"
        ]
        curr_dept = user_data.get("department", "")
        dept_idx = dept_options.index(curr_dept) if curr_dept in dept_options else 0
        new_dept = st.selectbox("Department", options=dept_options, index=dept_idx)
        
        level_options = ["100", "200", "300", "400", "500"]
        curr_lvl = user_data.get("level", "")
        lvl_idx = level_options.index(curr_lvl) if curr_lvl in level_options else 0
        new_lvl = st.selectbox("Current Level", options=level_options, index=lvl_idx)
        
        new_cgpa = st.number_input("CGPA", min_value=0.0, max_value=5.0, value=float(user_data.get("cgpa", 0.0) or 0.0), step=0.01)
        
        if st.form_submit_button("Update Profile", type="primary", use_container_width=True):
            users_col.update_one(
                {"username": user_id},
                {"$set": {
                    "full_name": new_name,
                    "department": new_dept,
                    "level": new_lvl,
                    "cgpa": new_cgpa,
                    "profile_setup_complete": True  # <--- THIS IS THE MISSING TRIGGER
                }}
            )
            st.session_state.edit_mode = False
            st.success("Profile Updated!")
            st.rerun()