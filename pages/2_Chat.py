import streamlit as st
import os
from pymongo import MongoClient
from langchain_mongodb import MongoDBAtlasVectorSearch
from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI
from langchain_classic.chains import create_retrieval_chain
from langchain_classic.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage, AIMessage

# 1. Page Config & CSS
st.set_page_config(page_title="Adviser | Chat", layout="centered", initial_sidebar_state="collapsed")

st.markdown("""
<style>
    [data-testid="stSidebarNav"] {display: none !important;}
    .stChatMessage { padding: 1rem; border-radius: 15px; margin-bottom: 10px; }
    [data-testid="stChatMessageAssistant"] { background-color: #2C666E25 !important; border: 1px solid #2C666E40 !important; }
    [data-testid="stChatMessageUser"] { background-color: #F0EDEE !important; border: 1px solid #E0E0E0 !important; }
</style>
""", unsafe_allow_html=True)

# Security Check
if not st.session_state.get('logged_in'):
    st.warning("Please Login.")
    st.stop()

user_id = st.session_state.user_id

# 2. Database Setup
client = MongoClient(os.getenv("MONGO_URI"))
db = client["LevelAdviser"]
embeddings_coll = db["embeddings"]
vault_coll = db["vault"]
history_coll = db["chat_history"] # NEW COLLECTION FOR PERSISTENCE

# 3. LOAD HISTORY FROM MONGODB (The "LocalStorage" equivalent)
if "messages" not in st.session_state:
    st.session_state.messages = []
    # Fetch last 20 messages for this specific user from Atlas
    saved_messages = list(history_coll.find({"userid": user_id}).sort("timestamp", 1).limit(20))
    for msg in saved_messages:
        st.session_state.messages.append({"role": msg["role"], "content": msg["content"]})

# 4. SIDEBAR
with st.sidebar:
    st.title("🎓 Menu")
    st.write(f"Student: **{user_id}**")
    st.divider()
    if st.button("🗨️ Chat", use_container_width=True): st.switch_page("pages/2_Chat.py")
    if st.button("📁 Documents", use_container_width=True): st.switch_page("pages/1_Documents.py")
    if st.button("👤 Profile", use_container_width=True): st.switch_page("pages/3_Profile.py")
    if st.button("🗺️ Roadmap", use_container_width=True): st.switch_page("pages/4_Roadmap.py")
    if st.button("Logout", use_container_width=True):
        st.session_state.logged_in = False
        st.switch_page("app.py")

st.title("🤖 Intelligent Level Adviser")

# 5. CHAT LOGIC
user_docs_count = vault_coll.count_documents({"userid": user_id})

if user_docs_count == 0:
    st.warning("No documents found. Please upload a handbook.")
else:
    # Display History
    for m in st.session_state.messages:
        with st.chat_message(m["role"]):
            st.markdown(m["content"])

    prompt = st.chat_input("Ask me about your level or courses...")

    if prompt:
        # Save User Message to Session and MongoDB
        st.session_state.messages.append({"role": "user", "content": prompt})
        history_coll.insert_one({"userid": user_id, "role": "user", "content": prompt, "timestamp": os.times()[4]})
        
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                try:
                    model = GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-001", output_dimensionality=768)
                    vector_store = MongoDBAtlasVectorSearch(embeddings_coll, model, index_name="vector_index")
                    retriever = vector_store.as_retriever(search_kwargs={"pre_filter": {"userid": user_id}, "k": 10})
                    
                    llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0)

                    # --- CONTEXTUAL PROMPT (The "Memory" Part) ---
                    # We add a MessagesPlaceholder to hold previous chat history
                    contextual_prompt = ChatPromptTemplate.from_messages([
                        ("system", "You are an Academic Adviser. Use the chat history and context to answer: {context}"),
                        MessagesPlaceholder(variable_name="chat_history"),
                        ("human", "{input}"),
                    ])

                    # Prepare History for the AI (Convert session strings to Message Objects)
                    chat_history_objs = []
                    for m in st.session_state.messages[-6:]: # Pass only last 6 messages for efficiency
                        if m["role"] == "user": chat_history_objs.append(HumanMessage(content=m["content"]))
                        else: chat_history_objs.append(AIMessage(content=m["content"]))

                    chain = create_retrieval_chain(retriever, create_stuff_documents_chain(llm, contextual_prompt))
                    response = chain.invoke({"input": prompt, "chat_history": chat_history_objs})
                    
                    ans = response["answer"]
                    st.markdown(ans)

                    # Save AI Message to Session and MongoDB
                    st.session_state.messages.append({"role": "assistant", "content": ans})
                    history_coll.insert_one({"userid": user_id, "role": "assistant", "content": ans, "timestamp": os.times()[4]})
                    
                    st.rerun()
                
                except Exception as e:
                    st.error(f"Error: {str(e)}")