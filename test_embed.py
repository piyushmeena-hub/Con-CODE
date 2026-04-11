import os
os.environ["OBJC_DISABLE_INITIALIZE_FORK_SAFETY"] = "YES"
os.environ["GRPC_ENABLE_FORK_SUPPORT"] = "0"
os.environ["TOKENIZERS_PARALLELISM"] = "false"
os.environ["OMP_NUM_THREADS"] = "1"
from langchain_community.embeddings import HuggingFaceEmbeddings
print("Starting...")
emb = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
print("Loaded model!")
