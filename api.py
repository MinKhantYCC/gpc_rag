from fastapi import FastAPI, UploadFile, File
from pydantic import BaseModel
from typing import List, Optional, Annotated, Union
# from uuid import UUID, uuid4

from llm_chains import load_normal_chain, load_pdf_chat_chain
from db_operations import init_db, load_messages, get_all_chat_history, save_text_message
from langchain_community.chat_message_histories.sql import SQLChatMessageHistory
import sqlite3 as sql
from pdf_hundler import add_documents_to_db_api

import json
from utils import get_timestamp, load_config
import warnings
warnings.filterwarnings("ignore")

init_db()
config = load_config()
db_conn = sql.connect(config['chat_sessions_database_path'], check_same_thread=False)
cursor = db_conn.cursor()

pdf_llm = load_pdf_chat_chain()
normal_llm = load_normal_chain()

app = FastAPI()

class Prompt(BaseModel):
    session_id: Optional[str] = None
    id: Optional[int] = 0
    sender_type: str
    message: str

@app.get("/", response_model=List[Prompt])
async def get_all_session():
    print("Getting all session")
    prompts =[]
    history_list = get_all_chat_history(cursor)
    for hist in history_list:
        message_dict = json.loads(hist['message'])
        prompt = Prompt(id=hist["id"], 
                        session_id=hist["session_id"], 
                        sender_type=message_dict['type'],
                        message=message_dict['data']['content'])
        prompts.append(prompt)
    return prompts

@app.get("/{session_id}", response_model=List[Prompt])
async def get_one_session(session_id:str):
    print("Getting one session")
    prompts = []
    history = load_messages(session_id, cursor)
    for hist in history:
        prompts.append(Prompt(sender_type=hist['type'],
                              message=hist['message']))
    return prompts

@app.post("/ask/{session_id}", response_model=Prompt)
async def chat(session_id:str, prompt:Prompt, user_input:str):
    prompt.session_id = session_id
    prompt.sender_type = "ai"
    chat_history = SQLChatMessageHistory(prompt.session_id, "sqlite:///chat_sessions.db",
                                         table_name="messages")
    prompt.message = normal_llm.run(user_input.strip(), chat_history)
    chat_history.add_user_message(user_input)
    chat_history.add_ai_message(prompt.message)
    # save_text_message(db_conn, cursor, str(prompt.session_id), "human", user_input)
    # save_text_message(db_conn, cursor, str(prompt.session_id), "ai", prompt.message)
    return prompt

@app.post("/ask/", response_model=Prompt)
async def new_chat(prompt:Prompt, user_input:str):
    prompt.session_id = get_timestamp() #uuid4()
    prompt.sender_type = "ai"
    chat_history = SQLChatMessageHistory(prompt.session_id, "sqlite:///chat_sessions.db",
                                         table_name="messages")
    prompt.message = normal_llm.run(user_input.strip(), chat_history)
    chat_history.add_user_message(user_input)
    chat_history.add_ai_message(prompt.message)
    # save_text_message(db_conn, cursor, str(prompt.session_id), "human", user_input)
    # save_text_message(db_conn, cursor, str(prompt.session_id), "ai", prompt.message)
    return prompt

@app.delete("/ask/", response_model=Prompt)
async def del_chat(session_id:str, prompt:Optional[Prompt]):
    prompt.session_id = session_id
    chat_history = SQLChatMessageHistory(prompt.session_id, "sqlite:///chat_sessions.db",
                                         table_name="messages")
    chat_history.clear()
    return prompt

############### PDF Chat ##################
@app.post("/askdoc/{session_id}", response_model=Prompt)
async def chat(session_id:str, prompt:Prompt, user_input:str):
    prompt.session_id = session_id
    prompt.sender_type = "ai"
    chat_history = SQLChatMessageHistory(prompt.session_id, "sqlite:///chat_sessions.db",
                                         table_name="messages")
    prompt.message = pdf_llm.run(user_input.strip(), chat_history)
    chat_history.add_user_message(user_input)
    chat_history.add_ai_message(prompt.message)
    # save_text_message(db_conn, cursor, str(prompt.session_id), "human", user_input)
    # save_text_message(db_conn, cursor, str(prompt.session_id), "ai", prompt.message)
    return prompt

@app.post("/askdoc/", response_model=Prompt)
async def new_chat_pdf(prompt:Prompt, user_input:str):
    prompt.session_id = get_timestamp() #uuid4()
    prompt.sender_type = "ai"
    chat_history = SQLChatMessageHistory(prompt.session_id, "sqlite:///chat_sessions.db",
                                         table_name="messages")
    prompt.message = pdf_llm.run(user_input.strip(), chat_history)
    chat_history.add_user_message(user_input)
    chat_history.add_ai_message(prompt.message)
    # save_text_message(db_conn, cursor, str(prompt.session_id), "human", user_input)
    # save_text_message(db_conn, cursor, str(prompt.session_id), "ai", prompt.message)
    return prompt

@app.post("/uploaddoc/")
async def upload_file(file: Union[UploadFile, None]=None):
    if not file:
        return {"message": "No file upload"}
    file_name = file.filename
    docsBytes = await file.read()
    add_documents_to_db_api([docsBytes], file_name)
    return {"filename": file_name, "size": len(docsBytes)}

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="localhost", port=8000)
    