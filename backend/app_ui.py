import streamlit as st
import os
import sys

# Add current directory to path so we can import backend modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from rag_chat import query_rag, load_store_name

# Page Config
st.set_page_config(
    page_title="Optom Coach AI",
    page_icon="👁️",
    layout="centered"
)

# Custom CSS for premium look
st.markdown("""
<style>
    .stChatInputContainer {
        border-radius: 20px;
        border: 1px solid #ddd;
    }
    .stChatMessage {
        border-radius: 10px;
        padding: 10px;
    }
    h1 {
        color: #2D3748;
    }
    .citation-box {
        background-color: #F7FAFC;
        border-left: 4px solid #3182CE;
        padding: 10px;
        margin-top: 10px;
        font-size: 0.9em;
        color: #4A5568;
    }
</style>
""", unsafe_allow_html=True)

# Header
st.title("👁️ Optom Coach AI")
st.caption("Your clinical assistant for Welsh Optometry Guidelines (WGOS, Health Boards)")

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if "citations" in message and message["citations"]:
            st.markdown(f'<div class="citation-box">📚 <b>Sources:</b><br>{message["citations"]}</div>', unsafe_allow_html=True)

# Input
if prompt := st.chat_input("Ask about WGOS, referral pathways, or clinical protocols..."):
    # Add user message to chat
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Generate response
    with st.chat_message("assistant"):
        with st.spinner("Searching guidelines..."):
            store_name = load_store_name()
            if not store_name:
                st.error("RAG Store not found. Please run indexer first.")
                st.stop()
            
            response = query_rag(prompt, store_name)
            
            if response and response.text:
                response_text = response.text
                citations = ""
                
                # Extract citations
                if response.candidates and hasattr(response.candidates[0], 'grounding_metadata'):
                    gm = response.candidates[0].grounding_metadata
                    if gm and hasattr(gm, 'grounding_chunks') and gm.grounding_chunks:
                        sources = set()
                        for chunk in gm.grounding_chunks:
                            if hasattr(chunk, 'retrieved_context'):
                                ctx = chunk.retrieved_context
                                title = ctx.title if hasattr(ctx, 'title') else 'Unknown Document'
                                sources.add(title)
                        if sources:
                            citations = "<br>".join([f"• {s}" for s in sources])

                st.markdown(response_text)
                if citations:
                    st.markdown(f'<div class="citation-box">📚 <b>Sources:</b><br>{citations}</div>', unsafe_allow_html=True)
                
                st.session_state.messages.append({
                    "role": "assistant", 
                    "content": response_text,
                    "citations": citations
                })
            else:
                st.error("Sorry, I couldn't find an answer to that.")