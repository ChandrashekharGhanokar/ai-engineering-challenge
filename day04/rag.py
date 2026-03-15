import pdfplumber
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_ollama import OllamaEmbeddings, OllamaLLM
from langchain_community.vectorstores import FAISS
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnableLambda


def extract_text(pdf_file) -> str:
    """Extract all text from a PDF file object."""
    with pdfplumber.open(pdf_file) as pdf:
        return "\n".join(page.extract_text() or "" for page in pdf.pages)


def split_text(text: str) -> list:
    """Split text into overlapping chunks."""
    splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
    return splitter.create_documents([text])


def build_vectorstore(chunks):
    """Embed chunks with Ollama and store in FAISS."""
    embeddings = OllamaEmbeddings(model="nomic-embed-text")
    return FAISS.from_documents(chunks, embeddings)


def build_qa_chain(vectorstore):
    """Build a retrieval chain using pure LCEL (langchain_core only, Python 3.14-safe)."""
    llm = OllamaLLM(model="llama3.2")
    retriever = vectorstore.as_retriever(search_kwargs={"k": 3})
    prompt = ChatPromptTemplate.from_template(
        "Answer the question based on the context below.\n\n"
        "Context: {context}\n\nQuestion: {input}\n\nAnswer:"
    )

    def run(inputs):
        question = inputs["input"]
        docs = retriever.invoke(question)
        context_str = "\n\n".join(doc.page_content for doc in docs)
        answer = (prompt | llm | StrOutputParser()).invoke(
            {"context": context_str, "input": question}
        )
        return {"answer": answer, "context": docs}

    return RunnableLambda(run)
