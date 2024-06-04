import json
from datetime import datetime
from langchain.schema.messages import HumanMessage, AIMessage
import requests

def save_chat_history_json(chat_history, file_path):
    with open(file_path, 'w') as f:
        json_data = [message.dict() for message in chat_history]
        json.dump(json_data, f)

def load_chat_history_json(file_path):
    with open(file_path, 'r') as f:
        json_data = json.load(f)
        messages = [HumanMessage(**message) if message['type']=="human" else AIMessage(**message) for message in json_data]
        return messages
    
def get_timestamp():
    return datetime.now().strftime("%Y-%m-%d%H-%M-%S")

def download_large_file(url, destination):
    try:
        with requests.get(url, stream=True) as response:
            response.raise_for_status()
            with open(destination, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
        print("File downloaded successfully!")
    except requests.exceptions.RequestException as e:
        print("Error downloading the file:", e)