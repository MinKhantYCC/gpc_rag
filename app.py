import streamlit as st
from llm_chains import load_normal_chain, load_pdf_chat_chain
from langchain_community.chat_message_histories import StreamlitChatMessageHistory
from pdf_hundler import add_documents_to_db
import yaml
import os
from utils import save_chat_history_json, load_chat_history_json, get_timestamp
import warnings
warnings.filterwarnings("ignore")

with open("config.yaml", "r") as f:
    config = yaml.safe_load(f)

def clear_input_field():
    st.session_state.user_question = st.session_state.user_input
    st.session_state.user_input = ""

def set_send_input():
    st.session_state.send_input = True
    clear_input_field()

def load_chain(chat_history):
    if st.session_state.pdf_chat == True:
        return load_pdf_chat_chain(chat_history)
    return load_normal_chain(chat_history)

def save_chat_history():
    if st.session_state.history != []:
        if st.session_state.session_key == "new_session":
            st.session_state.new_session_key = get_timestamp()+".json"
            save_chat_history_json(st.session_state.history, config['chat_history_path']+st.session_state.new_session_key)
        else:
            save_chat_history_json(st.session_state.history, config['chat_history_path']+st.session_state.session_key)

def track_index():
    st.session_state.session_index_tracker = st.session_state.session_key

def toggle_pdf_chat():
    st.session_state.pdf_chat = True
    st.session_state.uploaded = True

def main():
    st.title("Multimodal Chat Apps")
    chat_container = st.container()
    st.sidebar.title("Chat Sessions")
    
    chat_sessions = ["new_session"] + os.listdir(config['chat_history_path'])
    
    if "send_input" not in st.session_state:
        st.session_state.uploaded = False
        st.session_state.session_key = "new_session"
        st.session_state.send_input = False
        st.session_state.user_question = ""
        st.session_state.new_session_key = None
        st.session_state.session_index_tracker = "new_session"
    if st.session_state.session_key == "new_session" and st.session_state.new_session_key != None:
        st.session_state.session_index_tracker = st.session_state.new_session_key
        st.session_state.new_session_key = None
    
    index = chat_sessions.index(st.session_state.session_index_tracker)
    st.sidebar.selectbox("Select a chat session", chat_sessions, key="session_key", index=index, on_change=track_index)
    st.sidebar.toggle("PDF Chat", key="pdf_chat", value=False)
    upload_pdf = st.sidebar.file_uploader("Upload pdf file", accept_multiple_files=True,
                                          type=['pdf'], key="pdf_upload",
                                          on_change=toggle_pdf_chat)

    if upload_pdf and st.session_state.uploaded:
        with st.spinner("Processing pdf...."):
            add_documents_to_db(upload_pdf)
    st.session_state.uploaded = False

    if st.session_state.session_key != "new_session":
        st.session_state.history = load_chat_history_json(config['chat_history_path']+st.session_state.session_key)
    else:
        st.session_state.history = []

    chat_history = StreamlitChatMessageHistory(key="history")
    llm_chain = load_chain(chat_history)
    user_input = st.text_input("Type your message here: ", key="user_input", on_change=set_send_input)

    send_button = st.button("Send", key="send_button")

    if send_button or st.session_state.send_input:
        if st.session_state.user_question != "":
            with chat_container:
                if st.session_state.pdf_chat:
                    # st.chat_message("user").write(st.session_state.user_question)
                    llm_response = llm_chain.run(st.session_state.user_question, chat_history)
                    chat_history.add_user_message(st.session_state.user_question)
                    chat_history.add_ai_message(llm_response)
                    # st.chat_message("Bot").write(llm_response)
                else:
                    llm_response = llm_chain.run(st.session_state.user_question)
                st.session_state.user_question = ""
    with chat_container:
        if chat_history.messages != []:
            st.write("Chat History")
            for msg in chat_history.messages:
                st.chat_message(msg.type).write(msg.content)

    save_chat_history()
    
if __name__ == "__main__":
    main()