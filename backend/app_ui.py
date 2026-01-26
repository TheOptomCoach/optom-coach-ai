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

# Custom CSS for premium "Apple-like" feel
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&display=swap');

    /* Global Typography */
    html, body, [class*="css"] {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
        color: #1d1d1f;
    }

    /* Main Container */
    .stApp {
        background-color: #ffffff;
    }

    /* Header Styling */
    h1 {
        font-weight: 600;
        letter-spacing: -0.02em;
        font-size: 2.5rem;
        color: #1d1d1f;
        margin-bottom: 0.5rem;
    }
    
    .subtitle {
        font-size: 1.1rem;
        color: #86868b;
        font-weight: 400;
        margin-bottom: 2rem;
    }

    /* Chat Bubbles - Apple Message Style */
    .stChatMessage {
        background-color: transparent;
        border: none;
        padding: 0;
        margin-bottom: 1.5rem;
    }

    /* User Message */
    [data-testid="stChatMessage"][data-testid="user"] {
        background-color: #007aff;
        color: white;
        border-radius: 18px 18px 0 18px;
        padding: 12px 18px;
        margin-left: auto;
        max-width: 80%;
        box-shadow: 0 2px 4px rgba(0,122,255,0.1);
    }
    
    /* Assistant Message */
    [data-testid="stChatMessage"][data-testid="assistant"] {
        background-color: #f2f2f7;
        color: #1d1d1f;
        border-radius: 18px 18px 18px 0;
        padding: 16px 20px;
        max-width: 85%;
    }

    /* Input Area */
    .stChatInputContainer {
        padding-bottom: 3rem;
    }
    
    .stChatInputContainer textarea {
        border-radius: 24px;
        border: 1px solid #d2d2d7;
        padding: 12px 16px;
        font-size: 16px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.03);
        background-color: #fbfbfd;
    }
    
    .stChatInputContainer textarea:focus {
        border-color: #007aff;
        background-color: #ffffff;
        box-shadow: 0 0 0 4px rgba(0,122,255,0.1);
    }

    /* Citation Cards */
    .citation-card {
        margin-top: 16px;
        padding: 12px 16px;
        background: #ffffff;
        border: 1px solid #e5e5ea;
        border-radius: 12px;
        font-size: 0.85rem;
        color: #1d1d1f;
        box-shadow: 0 2px 8px rgba(0,0,0,0.02);
    }
    
    .citation-header {
        font-size: 0.75rem;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        color: #86868b;
        font-weight: 600;
        margin-bottom: 8px;
    }
    
    .citation-link {
        color: #007aff;
        text-decoration: none;
        display: block;
        padding: 2px 0;
        transition: opacity 0.2s;
    }
    
    .citation-link:hover {
        opacity: 0.7;
    }
</style>
""", unsafe_allow_html=True)

# Minimal Header
st.title("Optom Coach AI")
st.markdown('<p class="subtitle">Your intelligent clinical assistant for Wales.</p>', unsafe_allow_html=True)

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if "citations" in message and message["citations"]:
            st.markdown(f'''
                <div class="citation-card">
                    <div class="citation-header">References</div>
                    {message["citations"]}
                </div>
            ''', unsafe_allow_html=True)

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
                            citations = "".join([f'<div class="citation-link">{s}</div>' for s in sources])

                st.markdown(response_text)
                if citations:
                    st.markdown(f'''
                        <div class="citation-card">
                            <div class="citation-header">References</div>
                            {citations}
                        </div>
                    ''', unsafe_allow_html=True)
                
                st.session_state.messages.append({
                    "role": "assistant", 
                    "content": response_text,
                    "citations": citations
                })
            else:
                st.error("Sorry, I couldn't find an answer to that.")
