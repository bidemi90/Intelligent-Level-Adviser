# 🎓 Intelligent Level Adviser

An AI-powered academic assistant built with **Streamlit**, **LangChain**, and **Google Gemini**. This system allows students to upload their department handbooks and receive personalized academic guidance, automated roadmaps, and context-aware chat support.

## 🚀 Key Features

* **Intelligent Chat (RAG)**: Ask complex questions about course requirements, prerequisites, or department policies. The AI answers based strictly on the uploaded PDF handbooks.
* **Persistent Memory**: Chat history is stored in **MongoDB Atlas**, allowing you to refresh the page and continue your conversation exactly where you left off.
* **High-Context Indexing**: Uses optimized text splitting (1500 chunk size, 300 overlap) to ensure the AI understands the relationship between course titles and their descriptions.
* **Dynamic Roadmaps**: Generates a personalized academic strategy and curriculum overview based on your current Level and CGPA.
* **Cloud Integration**: Securely stores profile images and handbooks using **Cloudinary**.
* **Secure Authentication**: Student-ID based login system with encrypted passwords.

## 🛠️ Tech Stack

* **Frontend**: Streamlit
* **AI/LLM**: Google Gemini 1.5 Flash (via LangChain)
* **Embeddings**: Google Generative AI Embeddings (768d)
* **Database**: MongoDB Atlas (Vector Search & Document Storage)
* **Cloud Storage**: Cloudinary (Media & PDFs)
* **Orchestration**: LangChain

## 📋 Prerequisites

Before running the project, ensure you have:

* Python 3.10+
* A MongoDB Atlas Cluster (with a Vector Search index named `vector_index`)
* A Google Gemini API Key
* A Cloudinary Account

## ⚙️ Installation

1. **Clone the repository**:
```bash
git clone https://github.com/your-username/intelligent-level-adviser.git
cd intelligent-level-adviser

```


2. **Create and activate a virtual environment**:
```bash
python -m venv venv
.\venv\Scripts\activate

```


3. **Install dependencies**:
```bash
pip install -r requirements.txt
pip install tf-keras  # Required for Keras 2/3 compatibility in Transformers

```


4. **Configure Environment Variables**:
Create a `.env` file in the root directory:
```env
MONGO_URI=your_mongodb_atlas_connection_string
GOOGLE_API_KEY=your_gemini_api_key
CLOUDINARY_CLOUD_NAME=your_name
CLOUDINARY_API_KEY=your_key
CLOUDINARY_API_SECRET=your_secret

```



## 📂 Project Structure

```text
├── .streamlit/
│   └── config.toml         # Custom Streamlit server settings
├── pages/
│   ├── 1_Documents.py      # PDF Upload & Vector Indexing
│   ├── 2_Chat.py           # Context-aware AI Chat
│   ├── 3_Profile.py        # Student Academic Profile
│   └── 4_Roadmap.py        # AI Strategy Generator
├── app.py                  # Login & Authentication Entry Point
├── .env                    # Environment secrets (Git-ignored)
├── requirements.txt        # Project dependencies
└── README.md               # You are here!

```

## 🛡️ Guardrails & Optimization

* **Profile Lock**: Users cannot generate roadmaps until their academic profile (Level, CGPA, Dept) is complete.
* **Memory Efficiency**: The chat system passes a sliding window of the last 6 messages to the LLM to balance context awareness with API performance.
* **Cleanup Logic**: Automated `finally` blocks ensure temporary PDF files are purged from the server after indexing.

To elevate your repository's professionalism and provide clear guidance for others who might view or contribute to your project, I have drafted the **Contributions**, **License**, and **Security** sections for your `README.md`.

---

### 🤝 Contributing

Contributions are what make the open-source community such an amazing place to learn, inspire, and create. Any contributions you make are **greatly appreciated**.

1. **Fork the Project**
2. **Create your Feature Branch** (`git checkout -b feature/AmazingFeature`)
3. **Commit your Changes** (`git commit -m 'Add some AmazingFeature'`)
4. **Push to the Branch** (`git push origin feature/AmazingFeature`)
5. **Open a Pull Request**

### 📜 License

Distributed under the **MIT License**. This is a permissive license that is short and to the point. It lets people do nearly anything they want with your code as long as they provide attribution back to you and don't hold you liable.

> [!NOTE]
> See `LICENSE` in the root directory for more information.

### 🛡️ Security & Privacy

* **Data Encryption**: User passwords are encrypted using **SHA-256** hashing before being stored in MongoDB.
* **Environment Isolation**: Sensitive API keys and database URIs are never hardcoded and are managed strictly through `.env` files.
* **Session Management**: Secure Streamlit session states ensure that users can only access their own academic documents and chat history.

---

### 🧩 System Architecture

To help developers understand how the data flows from a student's PDF upload to the final AI response, here is a high-level overview of the **RAG (Retrieval-Augmented Generation)** pipeline implemented in this project:

1. **Document Ingestion**: PDFs are processed, split into high-context chunks, and embedded into 768-dimensional vectors.
2. **Vector Storage**: These embeddings are stored in a **MongoDB Atlas Vector Search** index.
3. **Contextual Retrieval**: When a student asks a question, the system retrieves the top 10 most relevant chunks based on the user's specific ID.
4. **Augmented Response**: Gemini 1.5 Flash uses the retrieved context and the persistent chat history to generate a precise, academic answer.

