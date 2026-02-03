import os
import time
import json
from functools import lru_cache
from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()

# Initialize Gemini Client
client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))

@lru_cache(maxsize=1)
def load_store_name():
    """Load the File Search store name from config."""
    config_path = os.path.join(os.path.dirname(__file__), 'rag_config.txt')
    if os.path.exists(config_path):
        with open(config_path, 'r') as f:
            return f.read().strip()
    raise FileNotFoundError("RAG config not found. Run rag_indexer.py first.")

@lru_cache(maxsize=1)
def load_geo_context():
    """Load geographic context mapping (town -> health board)."""
    geo_path = os.path.join(os.path.dirname(__file__), 'geo_context.json')
    if os.path.exists(geo_path):
        with open(geo_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

@lru_cache(maxsize=1)
def load_source_urls():
    """Load the pre-built mapping of document names to source URLs."""
    mapping_path = os.path.join(os.path.dirname(__file__), 'source_urls.json')
    if os.path.exists(mapping_path):
        try:
            with open(mapping_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading source URLs: {e}")
    return {}

def extract_location(query):
    """Extract potential location mentions from query."""
    import re
    # Simple pattern: "in [Location]" or "at [Location]"
    patterns = [
        r'\bin\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
        r'\bat\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
        r'working\s+in\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, query)
        if match:
            return match.group(1)
    return None

def find_health_board(location, geo_context):
    """Find health board for a given location."""
    if not location:
        return None
    
    location_lower = location.lower()
    
    # Direct match
    if location_lower in geo_context:
        return geo_context[location_lower]
    
    # Fuzzy match (simple substring)
    for town, hb in geo_context.items():
        if location_lower in town or town in location_lower:
            return hb
    
    return None

def enrich_query(query):
    """Enrich query with geographic context if location is mentioned."""
    geo_context = load_geo_context()
    if not geo_context:
        return query
    
    location = extract_location(query)
    if not location:
        return query
    
    health_board = find_health_board(location, geo_context)
    if health_board:
        enriched = f"{query}\n\n[Context: {location} is in {health_board}]"
        print(f"Query enriched with: {location} -> {health_board}")
        return enriched
    
    return query

def query_rag(query, max_retries=3):
    """
    Query the RAG system using Gemini File Search.
    
    Args:
        query: User's question
        max_retries: Number of retries for rate limit errors
    
    Returns:
        Gemini response object
    """
    store_name = load_store_name()
    
    # Enrich query with geographic context if applicable
    try:
        query = enrich_query(query)
    except Exception as e:
        print(f"Enrichment failed (continuing with original query): {e}")

    print(f"Querying Gemini with File Search (Store: {store_name})...")
    
    try:
        response = client.models.generate_content(
            model="gemini-2.5-pro", # Reverted to pro model per user request
            contents=query,
            config=types.GenerateContentConfig(
                system_instruction=(
                    "You are a highly efficient, clinical assistant who answers questions from Optometrists in Wales. "
                    "Always Provide DIRECT, actionable answers with citations where possible"
                    "1. IF ASKED FOR A LIST (e.g., 'which practices do WGOS 4?'): You MUST extract and list the names, addresses, and phone numbers from the context if available. Do NOT specific 'refer to the document'. GENERATE THE LIST. "
                    "2. MISSING DATA: If a document is referenced (e.g., 'Click here for the list') but the content isn't in the text, say: 'I see a reference to [Document Name], but the detailed list isn't in my database. Please check the source link below.' "
                    "3. WALES ONLY: Context is strictly Wales. IP = IPOS or WGOS 5 for reference."
                    "4. CITATIONS: Always use the provided context citations."
                    "5. READ THE FEEDBACK.MD: Always read the CRITICAL User Feedback - Corrections.md file for important corrections and updates before answering."
                ),
                tools=[
                    types.Tool(
                        file_search=types.FileSearch(
                            file_search_store_names=[store_name]
                        )
                    )
                ]
            )
        )
        return response
    except Exception as e:
        print(f"Error during generation: {e}")
        
        # Handle rate limit errors with exponential backoff
        if "429" in str(e) or "quota" in str(e).lower():
            for attempt in range(max_retries):
                wait_time = (2 ** attempt) * 2  # 2s, 4s, 8s
                print(f"Rate limit hit. Retrying in {wait_time}s... (Attempt {attempt + 1}/{max_retries})")
                time.sleep(wait_time)
                
                try:
                    response = client.models.generate_content(
                        model="gemini-2.5-pro",
                        contents=query,
                        config=types.GenerateContentConfig(
                            system_instruction=(
                                "You are a highly efficient, clinical assistant who answers questions from Optometrists in Wales. "
                                "Always Provide DIRECT, actionable answers with citations where possible"
                                "1. IF ASKED FOR A LIST (e.g., 'which practices do WGOS 4?'): You MUST extract and list the names, addresses, and phone numbers from the context if available. Do NOT specific 'refer to the document'. GENERATE THE LIST. "
                                "2. MISSING DATA: If a document is referenced (e.g., 'Click here for the list') but the content isn't in the text, say: 'I see a reference to [Document Name], but the detailed list isn't in my database. Please check the source link below.' "
                                "3. WALES ONLY: Context is strictly Wales. IP = IPOS or WGOS 5 for reference."
                                "4. CITATIONS: Always use the provided context citations."
                                "5. READ THE FEEDBACK.MD: Always read the CRITICAL User Feedback - Corrections.md file for important corrections and updates before answering."
                            ),
                            tools=[
                                types.Tool(
                                    file_search=types.FileSearch(
                                        file_search_store_names=[store_name]
                                    )
                                )
                            ]
                        )
                    )
                    return response
                except Exception as retry_error:
                    if attempt == max_retries - 1:
                        raise retry_error
                    continue
        
        raise e