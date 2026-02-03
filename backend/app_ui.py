import streamlit as st
import os
import sys

# Add current directory to path so we can import backend modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from feedback_logger import log_feedback
from rag_chat import query_rag, load_store_name, load_source_urls

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
        color: white !important; /* Force white text */
        border-radius: 12px 12px 0 12px;
        padding: 16px 22px;
        margin-left: auto;
        max-width: 80%;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        font-family: 'Merriweather', serif !important;
    }
    
    [data-testid="stChatMessage"][data-testid="user"] p,
    [data-testid="stChatMessage"][data-testid="user"] div,
    [data-testid="stChatMessage"][data-testid="user"] span {
         color: white !important;
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
    
    /* Disabled Input when waiting for feedback */
    .stChatInputContainer textarea:disabled {
        background-color: #e2e8f0;
        cursor: not-allowed;
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
        padding: 6px 0;
        transition: all 0.2s;
        font-family: 'Merriweather', serif !important;
    }
    
    .citation-link:hover {
        color: #1e3a8a;
        text-decoration: underline;
        padding-left: 4px;
    }

    /* Pulsing Text Animation */
    @keyframes pulse {
        0% { opacity: 0.3; color: #94a3b8; }
        50% { opacity: 1; color: #1d1d1f; }
        100% { opacity: 0.3; color: #94a3b8; }
    }
    
    .pulsing-text {
        font-family: 'Merriweather', serif !important;
        font-style: italic;
        font-size: 0.95rem;
        display: inline-block;
        vertical-align: top;
        margin-top: -5px;
        animation: pulse 2.0s infinite ease-in-out;
    }
    
    /* Feedback Container */
    .feedback-container {
        padding: 1rem;
        background-color: #f1f5f9;
        border-radius: 8px;
        border: 1px solid #cbd5e1;
        margin-bottom: 1rem;
        text-align: center;
    }
</style>
""", unsafe_allow_html=True)

# Minimal Header
st.title("OptometryWales.AI")
st.markdown('<p class="subtitle">The intelligent R.A.G AI assistant for Welsh optometrists.</p>', unsafe_allow_html=True)

# Initialize Session State
if "messages" not in st.session_state:
    st.session_state.messages = []
if "pending_feedback" not in st.session_state:
    st.session_state.pending_feedback = False
if "feedback_state" not in st.session_state:
    st.session_state.feedback_state = None # "positive" or "negative_pending"
if "last_q_a" not in st.session_state:
    st.session_state.last_q_a = None # Tuple (question, answer)

# Display chat messages
for message in st.session_state.messages:
    role = message["role"]
    avatar = "🧑" if role == "user" else "🤖"
    with st.chat_message(role, avatar=avatar):
        st.markdown(message["content"])
        if "citations" in message and message["citations"]:
            st.markdown(f'''
                <div class="citation-card">
                    <div class="citation-header">References</div>
                    {message["citations"]}
                </div>
            ''', unsafe_allow_html=True)

# Feedback Handling logic
if st.session_state.pending_feedback:
    q, a = st.session_state.last_q_a
    
    # If we haven't clicked a button yet (or reset)
    if st.session_state.feedback_state is None:
        st.markdown("### Mandatory: Rate Answer To Train AI")
        col1, col2, col3 = st.columns([1, 1, 8])
        with col1:
            if st.button("👍", use_container_width=True):
                log_feedback(q, a, "positive")
                st.session_state.pending_feedback = False
                st.rerun()
        with col2:
            if st.button("👎", use_container_width=True):
                st.session_state.feedback_state = "negative_pending"
                st.rerun()
        with col3:
            pass  # Empty column for spacing
                
    # If we clicked thumb down, show text area
    elif st.session_state.feedback_state == "negative_pending":
        st.warning("We're sorry the answer wasn't helpful.")
        correction = st.text_area(
            "What answer/info were you expecting instead? Your feedback will improve the AI for yourself and other optometrists.",
            key="feedback_text"
        )
        
        if st.button("Submit Feedback"):
            if correction and len(correction.strip()) > 5:
                # Log to DB
                log_feedback(q, a, "negative", expected_answer=correction)
                
                # Append to Markdown File for RAG Learning
                try:
                    feedback_file = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'clean_knowledge', 'User Feedback - Corrections.md')
                    with open(feedback_file, "a", encoding="utf-8") as f:
                        f.write(f"\\n\\n## Correction [Date: {os.popen('date /t').read().strip()}]\\n")
                        f.write(f"**Question:** {q}\\n")
                        f.write(f"**AI Answer:** {a}\\n")
                        f.write(f"**User Correction:** {correction}\\n")
                        f.write("---\\n")
                except Exception as e:
                    print(f"Error saving to markdown: {e}")
                    
                st.success("Thank you! Your feedback has been recorded and will learn from this.")
                import time
                time.sleep(1.5)
                st.session_state.pending_feedback = False
                st.session_state.feedback_state = None
                st.rerun()
            else:
                st.error("Please provide a bit more detail so we can learn.")

# Input (Disabled if waiting for feedback)
prompt = st.chat_input("Ask about WGOS, referral pathways, or clinical protocols...", disabled=st.session_state.pending_feedback)

if prompt:
    # Add user message to chat
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user", avatar="🧑"):
        st.markdown(prompt)

    # Generate response
    with st.chat_message("assistant", avatar="🤖"):
        # Custom "Thinking" Placeholder
        placeholder = st.empty()
        placeholder.markdown('<div class="pulsing-text">Thinking...</div>', unsafe_allow_html=True)
            
        store_name = load_store_name()
        if not store_name:
            st.error("RAG Store not found. Please wait for indexing to complete.")
            st.stop()
        
        # Backend RAG call
        response = query_rag(prompt, store_name)
        
        # Remove "Thinking..." once done
        placeholder.empty()
        
        # Display response
        if response and response.text:
            response_text = response.text
            citations = ""
            
            # Extract citations
            if response.candidates and hasattr(response.candidates[0], 'grounding_metadata'):
                gm = response.candidates[0].grounding_metadata
                if gm and hasattr(gm, 'grounding_chunks') and gm.grounding_chunks:
                    url_map = load_source_urls()  # Load pre-built mapping
                    sources = {}  # {title: url}
                    
                    def normalize_key(filename):
                        return filename.replace('.md', '').replace('.pdf', '').lower().strip()
                    
                    for chunk in gm.grounding_chunks:
                        if hasattr(chunk, 'retrieved_context'):
                            ctx = chunk.retrieved_context
                            title = ctx.title if hasattr(ctx, 'title') else 'Unknown Document'
                            # Try exact match first, then normalized
                            url = url_map.get(title) or url_map.get(normalize_key(title))
                            sources[title] = url
                    
                    if sources:
                        citations = "".join([
                            f'<a href="{url}" target="_blank" class="citation-link">📄 {title}</a>' 
                            if url else f'<div class="citation-link">📄 {title}</div>'
                            for title, url in sources.items()
                        ])

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
            
            # Set Feedback State
            st.session_state.last_q_a = (prompt, response_text)
            st.session_state.pending_feedback = True
            st.rerun() # Rerun to show buttons and disable input
            
        else:
            st.error("Sorry, I couldn't find an answer to that. Please try rephrasing.")
