import streamlit as st
import os
from pymongo import MongoClient
from langchain_mongodb import MongoDBAtlasVectorSearch
from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough

# 1. Page Config
st.set_page_config(page_title="Adviser | Roadmap", layout="wide", initial_sidebar_state="collapsed")

# Hide default sidebar nav
st.markdown(
    """
    <style>
        [data-testid="stSidebarNav"] {display: none !important;}
        /* Card styling for the dual panels */
        .roadmap-card {
            background-color: #FFFFFF;
            padding: 20px;
            border-radius: 10px;
            border: 1px solid #E0E0E0;
            box-shadow: 2px 2px 10px rgba(0,0,0,0.05);
            height: 100%;
        }
    </style>
    """,
    unsafe_allow_html=True,
)

# Security Check
if not st.session_state.get('logged_in'):
    st.warning("Please Login.")
    st.stop()

user_id = st.session_state.user_id

# Database Setup
client = MongoClient(os.getenv("MONGO_URI"))
db = client["LevelAdviser"]
users_col = db["users"]
embeddings_coll = db["embeddings"]

# Fetch User Profile
user_data = users_col.find_one({"username": user_id})

# 2. SIDEBAR (Matching your unified layout)
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
        st.session_state.logged_in = False
        st.switch_page("app.py")

st.title("🗺️ Academic Roadmap & Strategy")

# 3. PROFILE VERIFICATION
if not user_data or not user_data.get("profile_setup_complete"):
    st.warning("Profile Incomplete")
    st.info("You must complete your Academic Profile to generate a roadmap.")
    if st.button("Go to Profile", type="primary"):
        st.switch_page("pages/3_Profile.py")
    st.stop()

# Extract Profile Variables
dept = user_data.get("department", "Unknown")
level = user_data.get("level", "100")
cgpa = float(user_data.get("cgpa", 0.0))

# 4. THE HUD (Heads-Up Display)
st.subheader("Current Status")
c1, c2, c3 = st.columns(3)
c1.metric("Department", dept)
c2.metric("Level", level)
c3.metric("Current CGPA", f"{cgpa:.2f}")

# Calculate rough degree progress based on level
level_progress_map = {"100": 20, "200": 40, "300": 60, "400": 80, "500": 100}
progress_val = level_progress_map.get(level, 0)
st.progress(progress_val, text=f"Estimated Degree Progress: {progress_val}%")
st.divider()

# 5. GENERATOR ENGINE
if st.button("Generate My Academic Strategy", type="primary", use_container_width=True):
    with st.spinner("Analyzing curriculum and calculating strategy based on your CGPA..."):
        try:
            # Setup Retriever
            model = GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-001", output_dimensionality=768)
            vector_store = MongoDBAtlasVectorSearch(embeddings_coll, model, index_name="vector_index")
            retriever = vector_store.as_retriever(search_kwargs={"pre_filter": {"userid": user_id}, "k": 12})
            
            llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0.1)
            
            # Formatting Context Helper
            def format_docs(docs):
                return "\n\n".join(doc.page_content for doc in docs)
            
            # Highly specific prompt instructing the AI to output two distinct sections
            system_prompt = """
            You are an expert Academic Adviser. 
            Student Profile: Department of {dept}, {level} Level. Current CGPA: {cgpa}.
            
            Using ONLY the provided Context, generate an academic strategy. 
            You MUST format your output exactly as two sections separated by the exact word "===SPLIT===".
            
            Part 1 (Before SPLIT): List the mandatory and elective courses for this specific level.
            Part 2 (After SPLIT): Provide personalized, actionable advice based strictly on their CGPA of {cgpa}. 
            (e.g. If low, how to recover. If high, how to maintain and prep for projects).
            
            Context: {context}
            """
            
            prompt = ChatPromptTemplate.from_template(system_prompt)
            
            # Build Chain
            chain = (
                {"context": retriever | format_docs, "dept": lambda x: dept, "level": lambda x: level, "cgpa": lambda x: cgpa}
                | prompt
                | llm
                | StrOutputParser()
            )
            
            # Execute query searching for courses specifically for their level/dept
            query = f"What are the courses for {dept} students in {level} level?"
            response_text = chain.invoke(query)
            
            # 6. DUAL-PANEL RENDER
            if "===SPLIT===" in response_text:
                curriculum, strategy = response_text.split("===SPLIT===")
                
                col_left, col_right = st.columns(2)
                
                with col_left:
                    st.markdown('<div class="roadmap-card">', unsafe_allow_html=True)
                    st.subheader("📚 Required Curriculum")
                    st.markdown(curriculum.strip())
                    st.markdown('</div>', unsafe_allow_html=True)
                    
                with col_right:
                    st.markdown('<div class="roadmap-card">', unsafe_allow_html=True)
                    st.subheader("🎯 Adviser's Strategy")
                    st.markdown(strategy.strip())
                    st.markdown('</div>', unsafe_allow_html=True)
            else:
                # Fallback if AI forgets to split
                st.info("Academic Plan:")
                st.markdown(response_text)
                
        except Exception as e:
            st.error(f"Generation Error: {str(e)}")
            st.info("Note: If you receive a RESOURCE_EXHAUSTED error, your Free API quota is used up for the minute.")