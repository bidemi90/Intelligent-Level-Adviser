import streamlit as st
import os
import uuid
import time
import cloudinary
import cloudinary.uploader
from pymongo import MongoClient
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_mongodb import MongoDBAtlasVectorSearch
from langchain_cohere import CohereEmbeddings

# Layout configuration
st.set_page_config(page_title="Adviser | Documents", layout="centered", initial_sidebar_state="collapsed")

if not st.session_state.get('logged_in'):
    st.switch_page("app.py")

user_id = st.session_state.user_id

# Service configuration
cloudinary.config(
    cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
    api_key=os.getenv("CLOUDINARY_API_KEY"),
    api_secret=os.getenv("CLOUDINARY_API_SECRET")
)

client = MongoClient(os.getenv("MONGO_URI"))
db = client["LevelAdviser"]
vault_col = db["vault"]
embeddings_col = db["embeddings"]

# Custom CSS for Navigation
st.markdown("""
    <style>
        [data-testid="stSidebarNav"] {display: none !important;}
    </style>
""", unsafe_allow_html=True)

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

st.title("📁 Document Management")

with st.expander("➕ Upload New Handbook (PDF)", expanded=True):
    uploaded_file = st.file_uploader("Select PDF file", type="pdf")
    if st.button("Upload & Index Document", type="primary"):
        if uploaded_file:
            doc_id = str(uuid.uuid4())[:8]
            temp_file_path = f"temp_{doc_id}.pdf"
            
            try:
                with st.spinner("Uploading to cloud..."):
                    res = cloudinary.uploader.upload(uploaded_file, folder="level_adviser")
                
                with st.spinner("Generating High-Context Embeddings..."):
                    # Create the physical temp file
                    with open(temp_file_path, "wb") as f:
                        f.write(uploaded_file.getbuffer())
                    
                    loader = PyPDFLoader(temp_file_path)
                    data = loader.load()
                    
                    text_splitter = RecursiveCharacterTextSplitter(
                        chunk_size=1000, 
                        chunk_overlap=200,
                        separators=["\n\n", "\n", ". ", " ", ""]
                    )
                    chunks = text_splitter.split_documents(data)
                    
                    for chunk in chunks:
                        chunk.metadata.update({"userid": user_id, "doc_id": doc_id})
                    
                    # --- COHERE API INTEGRATION ---
                    model = CohereEmbeddings(
                        model="embed-english-v3.0",
                        cohere_api_key=os.getenv("COHERE_API_KEY")
                    )
                    
                    MongoDBAtlasVectorSearch.from_documents(
                        documents=chunks,
                        embedding=model,
                        collection=embeddings_col,
                        index_name="vector_index"
                    )
                    
                    vault_col.insert_one({
                        "userid": user_id, "doc_id": doc_id,
                        "filename": uploaded_file.name, "url": res['secure_url'],
                        "public_id": res['public_id'], "upload_date": time.strftime("%Y-%m-%d %H:%M:%S")
                    })
                    
                    st.success(f"Document '{uploaded_file.name}' indexed successfully!")
                    st.rerun()

            except Exception as e:
                st.error(f"Ingestion Error: {str(e)}")

            finally:
                # --- GUARANTEED CLEANUP ---
                if os.path.exists(temp_file_path):
                    os.remove(temp_file_path)

st.subheader("Indexed Documents")
user_docs = list(vault_col.find({"userid": user_id}))

if not user_docs:
    st.info("No documents currently indexed.")
else:
    for doc in user_docs:
        container = st.container(border=True)
        col1, col2, col3 = container.columns([5, 2, 2])
        with col1:
            st.write(f"📄 **{doc['filename']}**")
        with col2:
            st.link_button("View Source", doc['url'], use_container_width=True)
        with col3:
            if st.button("Delete", key=f"del_{doc['doc_id']}", use_container_width=True):
                cloudinary.uploader.destroy(doc['public_id'])
                vault_col.delete_one({"doc_id": doc['doc_id']})
                embeddings_col.delete_many({"doc_id": doc['doc_id']})
                st.rerun()