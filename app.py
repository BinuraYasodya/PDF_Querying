import streamlit as st
from dotenv import load_dotenv
from PyPDF2 import PdfReader
from langchain.text_splitter import CharacterTextSplitter
#from langchain.embeddings import OpenAIEmbeddings
from langchain_community.embeddings import OpenAIEmbeddings
#from langchain_openai import OpenAIEmbeddings
## Faiss embeddings store locally
from langchain_community.vectorstores import FAISS
from langchain.memory import ConversationBufferMemory
from langchain.chains.conversational_retrieval.base import ConversationalRetrievalChain
#from langchain_community.chat_models import ChatOpenAI
from htmlTemplates import css, bot_template, user_template
from langchain_openai import ChatOpenAI




def get_pdf_text(pdf_docs):
    text = ""
    for pdf in pdf_docs:
        pdf_reader = PdfReader(pdf)
        for page in pdf_reader.pages:
            text += page.extract_text()
    return text


def get_text_chunks(raw_text):
    text_splitter = CharacterTextSplitter(
        separator="\n",
        chunk_size = 1000,
        chunk_overlap = 200,
        length_function = len
    )
    
    chunks = text_splitter.split_text(raw_text)
    return chunks


def get_vector_store(text_chunks):
    text_embeddings = OpenAIEmbeddings()
    vectorstore = FAISS.from_texts(texts=text_chunks, embedding=text_embeddings)
    return vectorstore


def get_conversation_chain(vector_store):
    llm = ChatOpenAI()
    memory = ConversationBufferMemory(memory_key='chat_history', return_messages=True)
    conversation_chain = ConversationalRetrievalChain.from_llm(
        llm=llm,
        retriever=vector_store.as_retriever(),
        memory=memory

    )
    return conversation_chain


def handle_user_input(input_qustion):
    response = st.session_state.conversation.invoke({'question': input_qustion})
    st.session_state.chat_history = response['chat_history']

    for i, message in enumerate( st.session_state.chat_history):
        if i % 2 == 0:
            st.write(user_template.replace("{{MSG}}",message.content), unsafe_allow_html=True)
        else:
            st.write(bot_template.replace("{{MSG}}",message.content), unsafe_allow_html=True)


def main():
    load_dotenv()
    st.set_page_config(page_title="Chat with multiple PDFs", page_icon=":books:")

    st.write(css,unsafe_allow_html=True)

    if 'conversation' not in st.session_state:
        st.session_state.conversation = None

    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = None
    


    st.header("Chat with multiple PDFs :books:")

    input_qustion = st.text_input("Ask a question about your documents:")
    if input_qustion:
        handle_user_input(input_qustion)


    with st.sidebar:
        st.subheader("Your documents")
        pdf_docs = st.file_uploader("Upload your PDFs here and click on 'process'", accept_multiple_files=True)

        submit = st.button("Process")

        if submit:
            with st.spinner("Processing"):

                ## get the pdf text
                raw_text = get_pdf_text(pdf_docs)

                ## get the text chunks
                text_chunks = get_text_chunks(raw_text)


                ## create the vector store
                vector_store = get_vector_store(text_chunks)


                ## create conversation chain
                st.session_state.conversation = get_conversation_chain(vector_store)






if __name__ == '__main__':
    main()