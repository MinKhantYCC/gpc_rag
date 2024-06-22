import streamlit as st
import requests
from utils import load_config, get_timestamp
from pydantic import BaseModel
from typing import Optional
import json

config = load_config()
url = "http://localhost:8000"

class Prompt(BaseModel):
    sender_type: str
    message: str
    session_id: Optional[str] = None
    id: Optional[int] = 0

prompt = Prompt(sender_type="human", message="string")
data = prompt.model_dump()

def clear_input_field():
    st.session_state.user_question = st.session_state.user_input
    st.session_state.user_input = ""

def set_send_input():
    st.session_state.send_input = True
    clear_input_field()

def delete_chat_session_history():
    requests.delete(f"{url}/ask/{st.session_state.session_key}")
    st.session_state.session_index_tracker = "new_session"
    st.session_state.session_key = "new_session"

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

    if st.session_state.session_key == "new_session" and st.session_state.new_session_key != None:
        st.session_state.session_index_tracker = st.session_state.new_session_key
        st.session_state.new_session_key = None

    st.sidebar.title("Chat Sessions")
    print("Loading all sessions")
    session_info = json.loads(requests.get(f"{url}/").content)
    sessions_ids = list(set([info['session_id'] for info in session_info]))
    chat_sessions = ["new_session"] + sessions_ids

    index = chat_sessions.index(st.session_state.session_index_tracker)

    st.sidebar.selectbox("Select a chat session", chat_sessions, key="session_key", index=index, on_change=track_index)
    st.sidebar.toggle("PDF Chat", key="pdf_chat", value=False)
    upload_pdf = st.sidebar.file_uploader("Upload pdf file", accept_multiple_files=False,
                                          type=['pdf', 'txt'], key="pdf_upload",
                                          on_change=toggle_pdf_chat)
    st.sidebar.button("Delete Chat Session", on_click=delete_chat_session_history)
    st.sidebar.button("Clear Cache", on_click=clear_cache)

    if upload_pdf and st.session_state.uploaded:
        with st.spinner("Processing pdf...."):
            files = {"file": (upload_pdf.name, upload_pdf, "multipart/form-data")}
            requests.post(f"{url}/uploaddoc/", files=files)
    st.session_state.uploaded = False

    user_input = st.text_input("Type your message here: ", key="user_input")

    send_button = st.button("Send", key="send_button", on_click=set_send_input)

    if send_button or st.session_state.send_input:
        if st.session_state.user_question != "":
            with chat_container:
                if st.session_state.session_key != "new_session":
                    print("Asking in a session already exist")
                    if not upload_pdf or not st.session_state.pdf_chat:
                        response = requests.post(f"{url}/ask/{st.session_state.session_key}?user_input={st.session_state.user_question.strip()}\
                                                 &session_id={st.session_state.session_key}", json=data)
                    else:
                        response = requests.post(f"{url}/askdoc/{st.session_state.session_key}?user_input={st.session_state.user_question.strip()}\
                                                 &session_id={st.session_state.session_key}", json=data)
                    st.session_state.send_input = False
                else:
                    print("Asking in a new session")
                    if not upload_pdf or not st.session_state.pdf_chat:
                        response = requests.post(f"{url}/ask/?user_input={st.session_state.user_question.strip()}", json=data)
                    else:
                        response = requests.post(f"{url}/askdoc/?user_input={st.session_state.user_question.strip()}", json=data)
                    if response.status_code == 200:
                        st.session_state.new_session_key = json.loads(response.content)['session_id']
                    st.session_state.send_input = False

    with chat_container:
        print("Getting chat history in one session")
        if st.session_state.session_key != "new_session":
            chat_history = requests.get(f"{url}/{st.session_state.session_key}")
            if chat_history.content != b'[]':
                messages = json.loads(chat_history.content)
                for msg in messages:
                    st.chat_message(msg['sender_type']).write(msg['message'])
    # if st.session_state.session_key == "new_session":

    if (st.session_state.session_key == "new_session") and (st.session_state.new_session_key != None):
        st.rerun()

if __name__ == "__main__":
    main()