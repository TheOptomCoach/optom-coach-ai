import os
import sys
from dotenv import load_dotenv
from google import genai
from google.genai import types

# Load environment variables
load_dotenv()

api_key = os.getenv("GOOGLE_API_KEY")
if not api_key:
    raise ValueError("GOOGLE_API_KEY not found in .env file")

client = genai.Client(api_key=api_key)

import json

def load_store_name():
    config_path = os.path.join(os.path.dirname(__file__), 'rag_config.txt')
    if not os.path.exists(config_path):
        print("Error: rag_config.txt not found. Please run rag_indexer.py first.")
        return None
    with open(config_path, 'r') as f:
        return f.read().strip()

def load_geo_context():
    """Load the mapping of Town/Practice -> Cluster -> Health Board from split files"""
    # Go up one level from backend/ to find geographic_context_part_*.json
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    geo_data = {}
    
    # Try loading from split files first (deployment style)
    part_files = [f for f in os.listdir(base_dir) if f.startswith('geographic_context_part_') and f.endswith('.json')]
    
    if part_files:
        print(f"Loading {len(part_files)} geographic context parts...")
        for pf in part_files:
            try:
                with open(os.path.join(base_dir, pf), 'r', encoding='utf-8') as f:
                    geo_data.update(json.load(f))
            except Exception as e:
                print(f"Error loading {pf}: {e}")
        return geo_data

    # Fallback to single file (legacy/local dev)
    json_path = os.path.join(base_dir, 'geographic_context.json')
    if os.path.exists(json_path):
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading geo context: {e}")
            return {}
            
    print("Warning: No geographic_context files found.")
    return {}

def enrich_query_with_context(query, geo_map):
    """
    Scans the query for known locations and appends context instructions.
    """
    query_lower = query.lower()
    
    # Simple keyword matching (could be improved with fuzzy matching later)
    # We sort keys by length descending to match "Tenby Surgery" before "Tenby"
    sorted_keys = sorted(geo_map.keys(), key=len, reverse=True)
    
    found_location = None
    context_entry = None
    
    for key in sorted_keys:
        if key.lower() in query_lower:
            found_location = key
            context_entry = geo_map[key]
            break
    
    if context_entry:
        hb = context_entry.get('health_board', 'Unknown HB')
        cluster = context_entry.get('cluster', 'Unknown Cluster')
        
        enrichment = (
            f"\\n\\nIMPORTANT CONTEXT: The user is asking about '{found_location}'. "
            f"This location is in '{cluster}' Cluster, within '{hb}'. "
            f"You MUST prioritize Guidelines, Pathways, and Documents specific to '{hb}' "
            f"or All Wales guidelines. Do not use guidelines from other Health Boards unless explicitly relevant."
        )
        print(f"  [Context Detected] Location: {found_location} -> {hb}")
        return query + enrichment
    
    return query

def query_rag(query, store_name):
    """
    Queries Gemini File Search and returns the full response object.
    """
    # Auto-enrich query with geo context
    try:
        geo_map = load_geo_context()
        query = enrich_query_with_context(query, geo_map)
    except Exception as e:
        print(f"Enrichment failed (continuing with original query): {e}")

    print(f"Querying Gemini with File Search (Store: {store_name})...")
    
    try:
        response = client.models.generate_content(
            model="gemini-1.5-flash", # Updated to stable model name if needed, or keep preview
            contents=query,
            config=types.GenerateContentConfig(
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
        return None

def print_response(response):
    """
    Helper to print response to console (for CLI usage).
    """
    if not response:
        return

    print("\\n--- Response ---\\n")
    print(response.text)
    
    # Show citations if available
    if response.candidates and hasattr(response.candidates[0], 'grounding_metadata'):
        gm = response.candidates[0].grounding_metadata
        if gm and hasattr(gm, 'grounding_chunks') and gm.grounding_chunks:
            print("\\n--- Sources ---")
            for chunk in gm.grounding_chunks:
                if hasattr(chunk, 'retrieved_context'):
                    ctx = chunk.retrieved_context
                    print(f"  - {ctx.title if hasattr(ctx, 'title') else 'Unknown'}")

def main():
    if len(sys.argv) < 2:
        print("Usage: python rag_chat.py \\"Your question here\\"")
        return

    query = sys.argv[1]
    store_name = load_store_name()
    
    if store_name:
        # Load context
        geo_map = load_geo_context()
        enriched_query = enrich_query_with_context(query, geo_map)
        
        response = query_rag(enriched_query, store_name)
        print_response(response)

if __name__ == "__main__":
    main()