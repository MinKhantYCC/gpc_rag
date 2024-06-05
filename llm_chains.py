from langchain.chains.llm import LLMChain
from langchain_community.embeddings import HuggingFaceInstructEmbeddings
from langchain.chains.retrieval_qa.base import RetrievalQA
from langchain.memory import ConversationBufferMemory
from langchain.prompts import PromptTemplate
from langchain_community.llms.ctransformers import CTransformers
from langchain_community.vectorstores import Chroma

from langchain.chains.retrieval import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import ChatPromptTemplate

from prompt_template import memory_prompt_template, pdf_chat_prompt
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
    # persistent_client = chromadb.PersistentClient("chroma_db")
    
    langchain_chroma = Chroma(
        # client=persistent_client,
        persist_directory="chroma_db",
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
    return pdfChatChain(chat_history)

def load_retrieval_chain(llm, vector_db):
    return RetrievalQA.from_llm(llm=llm, retriever=vector_db.as_retriever(search_kwargs={"k": config["chat_config"]["number_of_retrieved_documents"]}), verbose=True)

from operator import itemgetter
def create_pdf_chat_runnable(llm, vector_db, prompt):
    runnable = (
        {
        "context": itemgetter("human_input") | vector_db.as_retriever(search_kwargs={"k": config["chat_config"]["number_of_retrieved_documents"]}),
        "human_input": itemgetter("human_input"),
        "history" : itemgetter("history"),
        }
    | prompt | llm.bind(stop=["Human:"]) 
    )
    return runnable

class pdfChatChain:

    def __init__(self, chat_history):
        vector_db = load_vectordb(create_embeddings())
        llm = create_llm()
        #llm = load_ollama_model()
        prompt = create_prompt_from_template(pdf_chat_prompt)
        self.llm_chain = create_pdf_chat_runnable(llm, vector_db, prompt)

    def run(self, user_input, chat_history):
        print("Pdf chat chain is running...")
        memory = create_chat_memory(chat_history)
        return self.llm_chain.invoke(input={"human_input" : user_input, "history" : memory.chat_memory.messages})
