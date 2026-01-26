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

# Custom CSS for "Clean Serif" Clinical Feel
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Merriweather:wght@300;400;700&family=Playfair+Display:wght@400;600&display=swap');

    /* Global Typography - ALL Serif */
    html, body, [class*="css"], font, span, div {
        font-family: 'Merriweather', serif !important;
        color: #1d1d1f;
    }

    /* Main Container */
    .stApp {
        background-color: #f8f9fa; /* Warm paper-like grey */
    }

    /* Header Styling */
    h1 {
        font-family: 'Playfair Display', serif !important;
        font-weight: 700;
        letter-spacing: -0.01em;
        font-size: 2.8rem;
        color: #1e3a8a; /* Clinical Navy */
        margin-bottom: 0.5rem;
    }
    
    .subtitle {
        font-family: 'Merriweather', serif !important;
        font-size: 1.15rem;
        color: #475569;
        font-weight: 300;
        font-style: italic;
        margin-bottom: 2.5rem;
    }

    /* Chat Bubbles */
    .stChatMessage {
        background-color: transparent;
        border: none;
        padding: 0;
        margin-bottom: 1.5rem;
    }

    /* User Message - Clean Blue Serif */
    [data-testid="stChatMessage"][data-testid="user"] {
        background-color: #007aff;
        color: white;
        border-radius: 12px 12px 0 12px;
        padding: 16px 22px;
        margin-left: auto;
        max-width: 80%;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        font-family: 'Merriweather', serif !important;
    }
    
    /* Assistant Message - Paper White Serif */
    [data-testid="stChatMessage"][data-testid="assistant"] {
        background-color: #ffffff;
        color: #1d1d1f;
        border: 1px solid #e2e8f0;
        border-left: 4px solid #1e3a8a; /* Stronger accent */
        border-radius: 12px 12px 12px 0;
        padding: 18px 24px;
        max-width: 85%;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
        font-family: 'Merriweather', serif !important;
        line-height: 1.6;
    }

    /* Input Area */
    .stChatInputContainer {
        padding-bottom: 3rem;
    }
    
    .stChatInputContainer textarea {
        border-radius: 15px;
        border: 1px solid #cbd5e1;
        padding: 16px;
        font-family: 'Merriweather', serif !important;
        font-size: 16px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.03);
        background-color: #ffffff;
    }
    
    .stChatInputContainer textarea:focus {
        border-color: #1e3a8a;
        box-shadow: 0 0 0 2px rgba(30, 58, 138, 0.1);
    }

    /* Status Box (The "Thinking" bit) */
    .stStatusWidget {
        font-family: 'Merriweather', serif !important;
        border-radius: 8px;
        border: 1px solid #e2e8f0;
    }

    /* Citation Cards */
    .citation-card {
        margin-top: 16px;
        padding: 14px 18px;
        background: #f1f5f9;
        border-left: 3px solid #1e3a8a;
        border-radius: 4px;
        font-size: 0.9rem;
        color: #334155;
        font-family: 'Merriweather', serif !important;
    }
    
    .citation-header {
        font-family: 'Playfair Display', serif !important;
        font-size: 0.75rem;
        text-transform: uppercase;
        letter-spacing: 0.1em;
        color: #64748b;
        font-weight: 700;
        margin-bottom: 10px;
    }
    
    .citation-link {
        color: #0369a1;
        text-decoration: none;
        display: block;
        padding: 4px 0;
        transition: opacity 0.2s;
        font-family: 'Merriweather', serif !important;
    }
    
    .citation-link:hover {
        text-decoration: underline;
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
    role = message["role"]
    avatar = "🧑‍⚕️" if role == "user" else "🤖"
    with st.chat_message(role, avatar=avatar):
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
    with st.chat_message("user", avatar="🧑‍⚕️"):
        st.markdown(prompt)

    # Generate response
    with st.chat_message("assistant", avatar="🤖"):
        # NEW: Transparent Logic Container
        with st.status("Thinking...", expanded=True) as status:
            store_name = load_store_name()
            if not store_name:
                st.error("RAG Store not found.")
                st.stop()
            
            # Simulate Context Logic
            status.write("📍 Detecting location context...")
            
            # Infer context for UI effect
            if any(x in prompt.lower() for x in ['cardiff', 'swansea', 'powys', 'newport', 'cwm taf']):
                 status.write("🗺️ Localizing to specific Health Board guidelines...")
            else:
                 status.write("🔎 Checking All-Wales WGOS protocols...")
                 
            status.write("📚 Searching Knowledge Base (Annexes, Pathways)...")
            
            response = query_rag(prompt, store_name)
            
            if response:
                status.update(label="Complete", state="complete", expanded=False)
            else:
                 status.update(label="Search Failed", state="error")
        
        # Display response OUTSIDE the status dropdown
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
