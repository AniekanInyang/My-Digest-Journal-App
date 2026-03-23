"""
RAG Service Module

Handles semantic search and retrieval-augmented generation for journal entries.
Uses ChromaDB for local vector storage and Azure OpenAI for embeddings and chat.
"""

import os
import logging
from typing import List, Dict, Optional
from datetime import datetime
import chromadb
from chromadb.config import Settings
from openai import AzureOpenAI

logger = logging.getLogger(__name__)

# Initialize ChromaDB client
chroma_client = chromadb.Client(Settings(
    persist_directory="./chroma_db",
    anonymized_telemetry=False
))

# Collection name for journal entries
COLLECTION_NAME = "journal_entries"


def get_openai_client():
    """Initialize and return Azure OpenAI client."""
    return AzureOpenAI(
        api_key=os.environ.get("AZURE_OPENAI_KEY"),
        api_version="2024-12-01-preview",
        azure_endpoint=os.environ.get("AZURE_OPENAI_ENDPOINT")
    )


def get_embedding(text: str) -> List[float]:
    """
    Generate embedding vector for text using Azure OpenAI.
    
    Args:
        text: Text to embed
        
    Returns:
        List of floats representing the embedding vector
    """
    try:
        client = get_openai_client()
        response = client.embeddings.create(
            input=text,
            model="text-embedding-ada-002"
        )
        return response.data[0].embedding
    except Exception as e:
        logger.error(f"Error generating embedding: {e}")
        raise


def initialize_collection():
    """Initialize or get the ChromaDB collection for journal entries."""
    try:
        collection = chroma_client.get_or_create_collection(
            name=COLLECTION_NAME,
            metadata={"description": "Journal entries with semantic search"}
        )
        return collection
    except Exception as e:
        logger.error(f"Error initializing collection: {e}")
        raise


def add_entry_to_vector_db(entry_id: str, content: str, date: str, metadata: Optional[Dict] = None):
    """
    Add a journal entry to the vector database.
    
    Args:
        entry_id: Unique identifier for the entry
        content: Entry text content
        date: Entry date (ISO format string)
        metadata: Optional additional metadata
    """
    try:
        collection = initialize_collection()
        
        # Prepare metadata
        entry_metadata = {
            "date": date,
            "added_at": datetime.utcnow().isoformat()
        }
        if metadata:
            entry_metadata.update(metadata)
        
        # Generate embedding
        embedding = get_embedding(content)
        
        # Add to collection
        collection.add(
            ids=[entry_id],
            embeddings=[embedding],
            documents=[content],
            metadatas=[entry_metadata]
        )
        
        logger.info(f"Added entry {entry_id} to vector database")
        return True
        
    except Exception as e:
        logger.error(f"Error adding entry to vector DB: {e}")
        return False


def search_entries(query: str, n_results: int = 5) -> List[Dict]:
    """
    Search journal entries using semantic similarity.
    
    Args:
        query: Natural language search query
        n_results: Number of results to return
        
    Returns:
        List of matching entries with content, date, and similarity score
    """
    try:
        collection = initialize_collection()
        
        # Generate query embedding
        query_embedding = get_embedding(query)
        
        # Search
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results
        )
        
        # Format results
        formatted_results = []
        if results and results['ids'] and len(results['ids']) > 0:
            for i in range(len(results['ids'][0])):
                formatted_results.append({
                    'id': results['ids'][0][i],
                    'content': results['documents'][0][i],
                    'date': results['metadatas'][0][i].get('date', ''),
                    'distance': results['distances'][0][i] if 'distances' in results else None
                })
        
        return formatted_results
        
    except Exception as e:
        logger.error(f"Error searching entries: {e}")
        return []


def chat_with_journal(query: str, context_entries: List[Dict]) -> str:
    """
    Generate a conversational response based on journal entries.
    
    Args:
        query: User's question
        context_entries: Relevant journal entries from semantic search
        
    Returns:
        AI-generated response based on journal context
    """
    try:
        client = get_openai_client()
        
        # Build context from entries
        context_text = "\n\n".join([
            f"Date: {entry['date']}\n{entry['content']}"
            for entry in context_entries
        ])
        
        # System prompt
        system_prompt = """You are a helpful assistant that answers questions based on the user's personal journal entries. 
Your responses should:
- Be warm, supportive, and insightful
- Reference specific journal entries when relevant
- Help the user gain self-awareness and perspective
- Maintain privacy and confidentiality
- If the journal entries don't contain relevant information, acknowledge this honestly"""
        
        # User prompt with context
        user_prompt = f"""Based on these journal entries:

{context_text}

Please answer this question: {query}"""
        
        # Generate response
        response = client.chat.completions.create(
            model=os.environ.get("AZURE_OPENAI_MODEL_NAME", "gpt-4o-mini"),
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.7,
            max_tokens=500
        )
        
        return response.choices[0].message.content
        
    except Exception as e:
        logger.error(f"Error in chat: {e}")
        return "I apologize, but I encountered an error while processing your question. Please try again."


def delete_entry_from_vector_db(entry_id: str) -> bool:
    """
    Delete a journal entry from the vector database.
    
    Args:
        entry_id: Unique identifier for the entry
        
    Returns:
        True if successful, False otherwise
    """
    try:
        collection = initialize_collection()
        collection.delete(ids=[entry_id])
        logger.info(f"Deleted entry {entry_id} from vector database")
        return True
    except Exception as e:
        logger.error(f"Error deleting entry from vector DB: {e}")
        return False


def get_collection_stats() -> Dict:
    """
    Get statistics about the vector database collection.
    
    Returns:
        Dictionary with collection statistics
    """
    try:
        collection = initialize_collection()
        count = collection.count()
        return {
            "total_entries": count,
            "collection_name": COLLECTION_NAME
        }
    except Exception as e:
        logger.error(f"Error getting collection stats: {e}")
        return {"total_entries": 0, "collection_name": COLLECTION_NAME}
