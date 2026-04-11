import streamlit as st
import os
from langchain_groq import ChatGroq 
from langchain_community.embeddings import HuggingFaceEmbeddings 
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_classic.chains import RetrievalQA 
from tinydb import TinyDB

# --- 1. INITIAL SETUP ---
# This sets the page title and the local JSON database for attendance
st.set_page_config(page_title="Learner's FREE AI Hub", layout="wide")
db = TinyDB('attendance_db.json')

# Sidebar for the API Key and status updates...
with st.sidebar:
    st.title("⚙️ Configuration")
    api_key = st.text_input("Enter Groq API Key", type="password")
    if api_key:
        os.environ["GROQ_API_KEY"] = api_key
    st.info("Status: Running on Free Tier 💸")
    st.divider()
    st.write("First-year ECE Project")

# --- 2. THE AI LOGIC --

@st.cache_resource # This ensures the 100MB model stays in RAM and doesn't reload
def get_embeddings():
    # This runs LOCALLY on your laptop for free using HuggingFace
    return HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

def process_pdf(uploaded_file):
    # Save the uploaded file temporarily to disk
    with open("temp.pdf", "wb") as f:
        f.write(uploaded_file.getvalue())
    
    # 1. Load the PDF
    loader = PyPDFLoader("temp.pdf")
    pages = loader.load()
    
    # 2. Chunking: Breaking text into 1000-character pieces
    splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
    docs = splitter.split_documents(pages)
    
    # 3. Vectorization: Converting text to math and storing in FAISS
    vector_db = FAISS.from_documents(docs, get_embeddings())
    return vector_db

# --- 3. THE DASHBOARD UI ---
st.title("🤖 RAG Study Assistant (Free Edition)")

tab1, tab2 = st.tabs(["💬 Chatbot", "📝 Attendance"])

with tab1:
    if not api_key:
        st.warning("👈 Get your FREE key at console.groq.com to start.")
    
    file = st.file_uploader("Upload your lecture PDF", type="pdf")
    
    if file and api_key:
        # We store the 'brain' in st.session_state so it survives screen refreshes
        if 'vs' not in st.session_state:
            with st.spinner("Analyzing PDF locally (First run may take a minute)..."):
                st.session_state.vs = process_pdf(file)
                st.success("PDF Indexed for Free!")

        # Chat interface
        user_q = st.chat_input("Ask a question about your notes...")
        if user_q:
            # Connect to Groq's Llama 3 model
            qa = RetrievalQA.from_chain_type(
                llm=ChatGroq(model_name="llama-3.1-8b-instant"),
                chain_type="stuff",
                retriever=st.session_state.vs.as_retriever()
            )
            
            # Get the answer from the PDF
            with st.spinner("Thinking..."):
                answer = qa.invoke(user_q)["result"]
            
            # Display the conversation
            st.chat_message("user").write(user_q)
            st.chat_message("assistant").write(answer)

with tab2:
    st.header("📝 Quick Attendance Logger")
    st.write("Log your study sessions or team attendance here.")
    
    col1, col2 = st.columns(2)
    with col1:
        student_id = st.text_input("Student ID (e.g., ECE-001)")
    with col2:
        status = st.selectbox("Status", ["Present", "Late"])
        
    if st.button("Submit Attendance"):
        if student_id:
            db.insert({'id': student_id, 'status': status})
            st.success(f"Successfully logged attendance for {student_id}!")
        else:
            st.error("Please enter a Student ID.")

    st.divider()
    st.subheader("Recent Logs")
    # Show the last 5 entries in the database
    logs = db.all()
    if logs:
        st.table(logs[-5:])
    else:
        st.write("No logs found yet.")