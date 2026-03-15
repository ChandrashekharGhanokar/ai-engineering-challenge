import streamlit as st
from rag import extract_text, split_text, build_vectorstore, build_qa_chain

st.title("PDF Q&A Bot")
st.caption("Powered by local RAG — Ollama + FAISS")

uploaded_file = st.file_uploader("Upload a PDF", type="pdf")

if uploaded_file:
    if "qa_chain" not in st.session_state or st.session_state.get("pdf_name") != uploaded_file.name:
        with st.spinner("Processing PDF..."):
            text = extract_text(uploaded_file)
            chunks = split_text(text)
            vectorstore = build_vectorstore(chunks)
            st.session_state.qa_chain = build_qa_chain(vectorstore)
            st.session_state.pdf_name = uploaded_file.name
            st.session_state.chunk_count = len(chunks)
        st.success(f"Ready! Split into {st.session_state.chunk_count} chunks.")
    else:
        st.info(f"Using cached index — {st.session_state.chunk_count} chunks.")

    question = st.text_input("Ask a question about the PDF")

    if question:
        with st.spinner("Thinking..."):
            result = st.session_state.qa_chain.invoke({"input": question})

        st.markdown("### Answer")
        st.write(result["answer"])

        with st.expander("Source chunks"):
            for i, doc in enumerate(result["context"], 1):
                st.markdown(f"**Chunk {i}**")
                st.text(doc.page_content)
