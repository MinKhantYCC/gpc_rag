import streamlit as st
from llm_chains import load_normal_chain, load_pdf_chat_chain
from langchain_community.chat_message_histories import StreamlitChatMessageHistory
from pdf_hundler import add_documents_to_db
import yaml
import os
from db_operations import save_text_message, load_messages, init_db, delete_chat_history
from db_operations import get_all_chat_history_ids, close_db_connection, load_last_k_text_messages
import sqlite3 as sql
from utils import get_timestamp
import warnings
warnings.filterwarnings("ignore")

init_db()

with open("config.yaml", "r") as f:
    config = yaml.safe_load(f)

def clear_input_field():
    st.session_state.user_question = st.session_state.user_input
    st.session_state.user_input = ""

def set_send_input():
    st.session_state.send_input = True
    clear_input_field()

@st.cache_resource
def load_chain():
    if st.session_state.pdf_chat == True:
        return load_pdf_chat_chain()
    return load_normal_chain()

def delete_chat_session_history():
    delete_chat_history(st.session_state.session_key)
    st.session_state.session_index_tracker = "new_session"
    st.session_state.session_key = "new_session"

def save_chat_history():
    if st.session_state.history != []:
        if st.session_state.session_key == "new_session":
            st.session_state.new_session_key = get_timestamp()
            histories = st.session_state.history[-2:]
            for hist in histories:
                if not isinstance(hist, dict):
                    hist = hist.dict()
                if 'type' in hist.keys():
                    save_text_message(st.session_state.new_session_key, hist['type'], hist['content'])
                else:
                    save_text_message(st.session_state.new_session_key, hist['sender_type'], hist['content'])
        else:
            histories = st.session_state.history[-2:]
            for hist in histories:
                if not isinstance(hist, dict):
                    hist = hist.dict()
                if 'type' in hist.keys():
                    save_text_message(st.session_state.session_key, hist['type'], hist['content'])
                else:
                    save_text_message(st.session_state.session_key, hist['sender_type'], hist['content'])

def track_index():
    st.session_state.session_index_tracker = st.session_state.session_key

def clear_cache():
    st.cache_resource.clear()
    st.cache_data.clear()

def toggle_pdf_chat():
    st.session_state.pdf_chat = True
    st.session_state.uploaded = True
    clear_cache()

def main():
    st.title("Private Assistant")
    chat_container = st.container()
    
    if "send_input" not in st.session_state:
        st.session_state.uploaded = False
        st.session_state.session_key = "new_session"
        st.session_state.send_input = False
        st.session_state.user_question = ""
        st.session_state.new_session_key = None
        st.session_state.session_index_tracker = "new_session"
        st.session_state.db_conn = sql.connect(config['chat_sessions_database_path'], check_same_thread=False)
    if st.session_state.session_key == "new_session" and st.session_state.new_session_key != None:
        st.session_state.session_index_tracker = st.session_state.new_session_key
        st.session_state.new_session_key = None
    
    st.sidebar.title("Chat Sessions")
    
    chat_sessions = ["new_session"] + get_all_chat_history_ids()#os.listdir(config['chat_history_path'])

    index = chat_sessions.index(st.session_state.session_index_tracker)
    st.sidebar.selectbox("Select a chat session", chat_sessions, key="session_key", index=index, on_change=track_index)
    st.sidebar.toggle("PDF Chat", key="pdf_chat", value=False)
    upload_pdf = st.sidebar.file_uploader("Upload pdf file", accept_multiple_files=True,
                                          type=['pdf', 'txt'], key="pdf_upload",
                                          on_change=toggle_pdf_chat)
    st.sidebar.button("Delete Chat Session", on_click=delete_chat_session_history)
    st.sidebar.button("Clear Cache", on_click=clear_cache)

    if upload_pdf and st.session_state.uploaded:
        with st.spinner("Processing pdf...."):
            add_documents_to_db(upload_pdf)
    st.session_state.uploaded = False

    if st.session_state.session_key != "new_session":
        st.session_state.history = load_messages(st.session_state.session_key)
    else:
        st.session_state.history = []

    chat_history = StreamlitChatMessageHistory(key="history")
    llm_chain = load_chain()
    user_input = st.text_input("Type your message here: ", key="user_input")

    send_button = st.button("Send", key="send_button", on_click=set_send_input)

    if send_button or st.session_state.send_input:
        if st.session_state.user_question != "":
            with chat_container:
                llm_response = llm_chain.run(st.session_state.user_question, chat_history)
                chat_history.add_user_message(st.session_state.user_question)
                chat_history.add_ai_message("" if llm_response is None else llm_response)
                save_chat_history()
                st.session_state.user_question = ""
    with chat_container:
            for msg in chat_history.messages:
                if not isinstance(msg, dict):
                    msg = msg.dict()
                if "type" in msg:
                    st.chat_message(msg['type']).write(msg['content'])
                else:
                    st.chat_message(msg['sender_type']).write(msg['content'])
    if (st.session_state.session_key == "new_session") and (st.session_state.new_session_key != None):
        st.rerun()
    
if __name__ == "__main__":
    main()