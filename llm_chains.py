from langchain.chains import StuffDocumentsChain, LLMChain, ConversationalRetrievalChain
from langchain_community.embeddings import HuggingFaceInstructEmbeddings
from langchain.chains.retrieval_qa.base import RetrievalQA
from langchain.memory import ConversationBufferMemory
from langchain.prompts import PromptTemplate
from langchain_community.llms.ctransformers import CTransformers
from langchain_community.vectorstores import Chroma
from prompt_template import memory_prompt_template
import chromadb
import yaml
from utils import download_large_file
import os

model_download_path ="https://huggingface.co/TheBloke/TinyLlama-1.1B-Chat-v1.0-GGUF/resolve/main/tinyllama-1.1b-chat-v1.0.Q5_K_M.gguf?download=true"

with open("config.yaml", "r") as f:
    config = yaml.safe_load(f)

def create_llm(model_path=config['model_path']['small'], model_type=config['model_type'], model_config=config['model_config']):
    while not os.path.exists(model_path):
        print("model downloading ....")
        download_large_file(model_download_path, "tinyllama-1.1b-chat-v1.0.Q5_K_M.gguf")
    llm = CTransformers(model = model_path, model_type=model_type, config=model_config)
    return llm

def create_embeddings(embedding_path=config['embeddings_path']):
    embedding = HuggingFaceInstructEmbeddings(model_name=embedding_path)
    return embedding

def create_chat_memory(chat_history):
    return ConversationBufferMemory(memory_key="history", chat_memory=chat_history)

def create_prompt_from_template(template):
    return PromptTemplate.from_template(template)

def create_llm_chain(llm, chat_prompt, memory):
    return LLMChain(llm=llm, prompt=chat_prompt, memory=memory)

def load_normal_chain(chathistory):
    return chatChain(chathistory)

def load_vectordb(embeddings):
    persistent_client = chromadb.PersistentClient("chroma_db")
    
    langchain_chroma = Chroma(
        client=persistent_client,
        collection_name="pdfs",
        embedding_function=embeddings,
    )

    return langchain_chroma

class chatChain:
    def __init__(self, chat_history):
        self.memory = create_chat_memory(chat_history)
        llm = create_llm()
        chat_prompt = create_prompt_from_template(memory_prompt_template)
        self.llm_chain = create_llm_chain(llm, chat_prompt, self.memory)

    def run(self, user_input):
        return self.llm_chain.run(user_input = user_input,
                                  history=self.memory.chat_memory.messages,
                                  stop="<|user|>")

def load_pdf_chat_chain(chat_history):    
    return pdfChain(chat_history)

def load_retrieval_chain(llm, memory, vector_db):
    return RetrievalQA.from_llm(llm=llm, memory=memory, retriever=vector_db.as_retriever())

class pdfChain:
    def __init__(self, chat_history):
        self.memory = create_chat_memory(chat_history)
        self.vector_db = load_vectordb(create_embeddings())
        llm = create_llm()
        # chat_prompt = create_prompt_from_template(memory_prompt_template)
        self.llm_chain = load_retrieval_chain(llm, self.memory, self.vector_db)

    def run(self, user_input):
        return self.llm_chain.run(query=user_input,
                                  history=self.memory.chat_memory.messages,
                                  stop="<|user|>")
