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

# Custom CSS for "Royal/Serif" Premium Feel
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@400;600&family=Merriweather:wght@300;400;700&display=swap');

    /* Global Typography - Serif only */
    html, body, [class*="css"] {
        font-family: 'Merriweather', serif;
        color: #e2e8f0; /* Soft metallic silver text */
    }

    /* Main Container - Deep Navy Gradient */
    .stApp {
        background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
    }

    /* Header Styling */
    h1 {
        font-family: 'Playfair Display', serif;
        font-weight: 600;
        letter-spacing: 0.02em;
        font-size: 3rem;
        color: #fbbf24; /* Muted Gold */
        margin-bottom: 0.5rem;
        text-shadow: 0 2px 4px rgba(0,0,0,0.3);
    }
    
    .subtitle {
        font-family: 'Merriweather', serif;
        font-size: 1.1rem;
        color: #94a3b8; /* Muted metallic blue-grey */
        font-style: italic;
        margin-bottom: 2.5rem;
        border-bottom: 1px solid rgba(251, 191, 36, 0.2);
        padding-bottom: 1rem;
        display: inline-block;
    }

    /* Chat Bubbles */
    .stChatMessage {
        background-color: transparent;
        border: none;
        padding: 0;
        margin-bottom: 2rem;
    }

    /* User Message - Deep Royal Blue */
    [data-testid="stChatMessage"][data-testid="user"] {
        background: linear-gradient(135deg, #1e3a8a 0%, #172554 100%);
        color: #f8fafc;
        border: 1px solid rgba(255,255,255,0.1);
        border-radius: 12px 12px 0 12px;
        padding: 16px 24px;
        margin-left: auto;
        max-width: 80%;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.3);
        font-family: 'Merriweather', serif;
    }
    
    /* Assistant Message - Glassy Navy */
    [data-testid="stChatMessage"][data-testid="assistant"] {
        background: rgba(30, 41, 59, 0.7);
        color: #e2e8f0;
        border-left: 3px solid #fbbf24; /* Gold accent border */
        border-radius: 0 12px 12px 12px;
        padding: 16px 24px;
        max-width: 85%;
        backdrop-filter: blur(10px);
    }

    /* Input Area */
    .stChatInputContainer {
        padding-bottom: 3rem;
        background: transparent;
    }
    
    .stChatInputContainer textarea {
        border-radius: 0;
        border: 1px solid #475569;
        border-top: 2px solid #fbbf24; /* Gold top border */
        padding: 16px;
        font-family: 'Merriweather', serif;
        font-size: 16px;
        background-color: #0f172a;
        color: #e2e8f0;
        transition: all 0.3s ease;
    }
    
    .stChatInputContainer textarea:focus {
        border-color: #fbbf24;
        box-shadow: 0 0 15px rgba(251, 191, 36, 0.1);
    }

    /* Citation Cards - Dark Metallic */
    .citation-card {
        margin-top: 20px;
        padding: 16px;
        background: rgba(15, 23, 42, 0.8);
        border: 1px solid #334155;
        border-left: 2px solid #94a3b8;
        font-size: 0.9rem;
        color: #cbd5e1;
    }
    
    .citation-header {
        font-family: 'Playfair Display', serif;
        font-size: 0.85rem;
        text-transform: uppercase;
        letter-spacing: 0.1em;
        color: #fbbf24; /* Gold */
        margin-bottom: 10px;
        border-bottom: 1px solid rgba(251, 191, 36, 0.2);
        padding-bottom: 4px;
    }
    
    .citation-link {
        color: #60a5fa;
        text-decoration: none;
        display: block;
        padding: 4px 0;
        transition: color 0.2s;
        font-family: 'Merriweather', serif;
    }
    
    .citation-link:hover {
        color: #fbbf24;
        text-decoration: underline;
    }
</style>
""", unsafe_allow_html=True)

# Royal Header
st.title("Optom Coach AI")
st.markdown('<div class="subtitle">Excellence in Clinical Guidance.</div>', unsafe_allow_html=True)

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
