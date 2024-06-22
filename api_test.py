import requests
from pydantic import BaseModel
from typing import Optional
import json

url = "http://localhost:8000"

class Prompt(BaseModel):
    sender_type: str
    message: str
    session_id: Optional[str] = None
    id: Optional[int] = 0
#####################################################################################

##############################
######## Common Chat #########
##############################

# check if an empty database is created
print("Testing on a clear database....", end="")
response = requests.get(f"{url}/")
assert response.content != b"[]", "\nEmpty list should return"
print("Success")
print("#"*20, "\n")

# common chat in a new session
print("Testing on a new chat creation....", end="")
prompt = Prompt(sender_type="human", message="string")
data = prompt.model_dump()
user_input = "What is docker?"
response = requests.post(f"{url}/ask/?user_input={user_input}", json=data)
assert response.status_code == 200, "\nShould return status code 200"
print("Success")
print("#"*20, "\n")

# check if data is stored
previous_session_id = json.loads(response.content)['session_id']
print("Testing on saving chat session into database....", end="")
response = requests.get(f"{url}/?session_id={previous_session_id}")
assert response.content != b"[]", "\nPrevious chat history should be returned"
print("Success")
print("#"*20, "\n")

# common chat in the previous session
print("Testing on the previous chat session...", end="")
user_input = "What is the different between it and a virtual machine?"
response = requests.post(f"{url}/ask/{previous_session_id}?user_input={user_input}", json=data)
assert response.status_code == 200, "\nShould return status code 200"
print("Success")
print("#"*20, "\n")

# delete the previos chat session from the database
print("Testing on deleting the previous chat session...", end="")
prompt = Prompt(sender_type="human", message="string")
data = prompt.model_dump()
response = requests.delete(f"{url}/ask/?session_id={previous_session_id}", json=data)
assert response.status_code == 200, "\nShould return status code 200"
print("Success")
print("#"*20, "\n")
#####################################################################################

##############################
######### PDF Chat ###########
##############################

# upload Document Files
print("Testing on uploading pdf....", end="")
with open("StockMarket.pdf", "rb") as file:
    files = {"file": (file.name, file, "multipart/form-data")}
    response = requests.post(f"{url}/uploaddoc/", files=files)
assert response.status_code == 200, "\nShould return status code 200"
print("Success")
print("#"*20, "\n")

# ask data from document with pdf chat in a new session
print("Testing on a new session with doc chat....", end="")
prompt = Prompt(sender_type="human", message="string")
data = prompt.model_dump()
user_input = "What is stock market?"
response = requests.post(f"{url}/askdoc/?user_input={user_input}", json=data)
assert response.status_code == 200, "\nShould return status code 200"
print("Success")
print("#"*20, "\n")

# ask data from document with pdf chat in the previous session
previous_session_id = json.loads(response.content)['session_id']
print("Testing on the previous chat session with doc chat...", end="")
user_input = "List their types."
response = requests.post(f"{url}/askdoc/{previous_session_id}?user_input={user_input}", json=data)
assert response.status_code == 200, "\nShould return status code 200"
print("Success")
print("#"*20, "\n")
#####################################################################################