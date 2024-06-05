from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema.document import Document
from llm_chains import load_vectordb, create_embeddings
from langchain_community.document_loaders import PyPDFLoader
import pypdfium2

def get_pdf_texts(pdf_bytes):
    return [extract_text_from_pdf(pdf_byte.getvalue()) for pdf_byte in pdf_bytes]

def extract_text_from_pdf(pdf_byte):
    texts = []
    pdf_file = pypdfium2.PdfDocument(pdf_byte)
    for page_number in range(len(pdf_file)):
        page = pdf_file.get_page(page_number)
        text_page = page.get_textpage()
        text_range = text_page.get_text_range()
        texts.append(text_range)
    return "\n".join(texts)

def get_text_chunks(texts):
    splitter = RecursiveCharacterTextSplitter(chunk_size=1024, chunk_overlap=50,
                                             separators=["\n", "\n\n"],)
    return splitter.split_text(texts)

def get_document_chunks(text_list):
    documents = []
    for text in text_list:
        for chunk in get_text_chunks(text):
            documents.append(Document(page_content=chunk))
    return documents

def add_documents_to_db(pdf_bytes):
    print("Adding Document to DB...")
    texts = get_pdf_texts(pdf_bytes)
    documents = get_document_chunks(texts)
    vector_db = load_vectordb(create_embeddings())
    vector_db.add_documents(documents)

