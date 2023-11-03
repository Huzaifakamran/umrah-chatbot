import streamlit as st
from pypdf import PdfReader
from langchain.text_splitter import CharacterTextSplitter
from langchain.embeddings import OpenAIEmbeddings
from langchain.vectorstores import FAISS
from langchain.memory import ConversationBufferMemory
from langchain.chains import ConversationalRetrievalChain
from langchain.chat_models import ChatOpenAI
from htmlTemplates import css,bot_template,user_template
import os

OPENAI_API_KEY = st.secrets["OPENAI_API_KEY"]

def get_pdf_text(pdf_docs):
    text = ""
    for pdf in pdf_docs:
        pdf_reader = PdfReader(pdf)
        for page in pdf_reader.pages:
            text += page.extract_text()
    return text

def get_text_chunks(text):
    text_splitter = CharacterTextSplitter(
        separator="\n",
        chunk_size = 1000,
        chunk_overlap = 200,
        length_function = len
    )
    chunks = text_splitter.split_text(text)
    return chunks

def store_vectorize_data(chunks,embeddings):
    vectorstore = FAISS.from_texts(texts=chunks,embedding=embeddings)
    vectorstore.save_local("data")
    return vectorstore

def get_vectors_from_db(embeddings):
    new_db = FAISS.load_local("data", embeddings)
    return new_db

def get_conversation_chain(vectorstore):
    llm = ChatOpenAI()
    memory = ConversationBufferMemory(memory_key='chat_history',return_messages=True)
    conversation_chain = ConversationalRetrievalChain.from_llm(
        llm=llm,
        retriever=vectorstore.as_retriever(),
        memory = memory
    )
    return conversation_chain

def handle_userinput(user_input):
    response = st.session_state.conversation({'question':user_input})
    st.session_state.chat_history = response['chat_history']

    for i,message in enumerate(st.session_state.chat_history):
        if i % 2 == 0:
            st.write(user_template.replace("{{MSG}}",message.content),unsafe_allow_html=True)
        else:
            st.write(bot_template.replace("{{MSG}}",message.content),unsafe_allow_html=True)

def main():
    st.set_page_config(page_title="Chat With Your PDFS",page_icon=":books:")

    st.write(css,unsafe_allow_html=True)

    if "conversation" not in st.session_state:
        st.session_state.conversation = None
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = None

    st.header("Chat With You PDFS :books:")
    user_question = st.text_input("Ask a question about your documents:")

    # st.write(user_template.replace("{{MSG}}","Hello from user"),unsafe_allow_html=True)
    # st.write(bot_template.replace("{{MSG}}","Hello from bot"),unsafe_allow_html=True)

    if user_question:
        embeddings = OpenAIEmbeddings()
        new_db = get_vectors_from_db(embeddings)
        st.session_state.conversation = get_conversation_chain(new_db)
        handle_userinput(user_question)
                
if __name__ == '__main__':
    main()