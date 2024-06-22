memory_prompt_template = """<|system|>You are an AI chatbot having a conversation with human. Answer his questions.
{history}</s>
<|user|>
{user_input}</s>
<|assistant|>
"""

pdf_chat_prompt = """<|system|> Answer the user question based on the given context. Also consider the chat history. 
If you can't find the answer in the context, say you don't have any information concerned with the user question.
Chat history: {history}
Context: {context}</s>
<|user|>
Question: {human_input}</s>
<|assistant|>Answer:"""