"""
Topic Clustering Service Module

Handles on-demand topic classification of journal entries using Azure OpenAI.
Analyzes entries to identify main themes and topics.
"""

import os
import json
import logging
from typing import List, Dict, Optional
from openai import AzureOpenAI

logger = logging.getLogger(__name__)


def get_openai_client():
    """Initialize and return Azure OpenAI client."""
    return AzureOpenAI(
        api_key=os.environ.get("AZURE_OPENAI_KEY"),
        api_version="2024-12-01-preview",
        azure_endpoint=os.environ.get("AZURE_OPENAI_ENDPOINT")
    )


def cluster_entries_with_llm(entries: List[Dict], num_topics: int = 7) -> List[Dict]:
    """
    Analyze journal entries and identify main topics/themes using GPT-4o-mini.
    
    Args:
        entries: List of entry dictionaries with 'id', 'content', 'created_at'
        num_topics: Maximum number of topics to identify (default 7)
        
    Returns:
        List of topic dictionaries with:
        - name: topic name
        - emoji: relevant emoji
        - entry_ids: list of entry IDs belonging to this topic
        - count: number of entries in this topic
        - keywords: list of relevant keywords
    """
    if len(entries) < 3:
        logger.warning("Not enough entries to cluster (minimum 3 required)")
        return []
    
    try:
        client = get_openai_client()
        
        # Prepare entry summaries for analysis
        # Limit to first 100 entries and 300 chars each to stay within token limits
        entry_summaries = []
        for i, entry in enumerate(entries[:100]):
            content_preview = entry.get('content', '')[:300]
            date = entry.get('created_at', 'Unknown date')
            entry_summaries.append({
                'index': i,
                'id': entry.get('id'),
                'date': date,
                'preview': content_preview
            })
        
        # Create the prompt
        prompt = f"""Analyze these {len(entry_summaries)} journal entries and identify the main topics/themes.

Each entry has:
- index: position in the list (0-based)
- id: unique identifier
- date: when it was written
- preview: excerpt from the entry

Return a JSON object with a "topics" array. Each topic should have:
- name: clear topic name (e.g., "Work & Career", "Health & Fitness")
- emoji: single relevant emoji
- entry_indices: array of indices (numbers) of entries belonging to this topic
- count: number of entries in this topic
- keywords: array of 3-5 relevant keywords

Guidelines:
- Identify {min(num_topics, len(entry_summaries))} meaningful topics maximum
- Don't create topics with less than 2 entries
- Each entry can belong to multiple topics if relevant
- Use clear, specific topic names
- Choose emojis that represent the topic well

Entries:
{json.dumps(entry_summaries, indent=2)}

Return ONLY valid JSON in this exact format:
{{
  "topics": [
    {{
      "name": "Work & Career",
      "emoji": "💼",
      "entry_indices": [0, 3, 7],
      "count": 3,
      "keywords": ["work", "meetings", "projects"]
    }}
  ]
}}"""

        # Call GPT-4o-mini for fast, cost-effective analysis
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": "You are a helpful assistant that analyzes journal entries and identifies topics. Always return valid JSON."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            response_format={"type": "json_object"},
            temperature=0.7,
            max_tokens=2000
        )
        
        # Parse response
        result = json.loads(response.choices[0].message.content)
        topics = result.get('topics', [])
        
        # Convert entry indices to actual entry IDs
        for topic in topics:
            indices = topic.get('entry_indices', [])
            topic['entry_ids'] = [
                entry_summaries[idx]['id'] 
                for idx in indices 
                if idx < len(entry_summaries)
            ]
            # Update count to match actual entry_ids length
            topic['count'] = len(topic['entry_ids'])
            # Remove the indices field as we don't need it anymore
            topic.pop('entry_indices', None)
        
        # Filter out topics with no entries
        topics = [t for t in topics if t.get('count', 0) > 0]
        
        # Sort by count (most entries first)
        topics.sort(key=lambda x: x.get('count', 0), reverse=True)
        
        logger.info(f"Successfully identified {len(topics)} topics from {len(entries)} entries")
        return topics
        
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse LLM response as JSON: {e}")
        return []
    except Exception as e:
        logger.error(f"Error clustering entries: {e}")
        return []


def get_topic_entry_ids(topics: List[Dict], topic_name: str) -> List:
    """
    Get list of entry IDs for a specific topic.
    
    Args:
        topics: List of topic dictionaries from cluster_entries_with_llm
        topic_name: Name of the topic to get entries for
        
    Returns:
        List of entry IDs belonging to this topic
    """
    for topic in topics:
        if topic.get('name') == topic_name:
            return topic.get('entry_ids', [])
    return []


def filter_entries_by_topic(entries: List[Dict], topic_entry_ids: List) -> List[Dict]:
    """
    Filter entries to only include those belonging to a specific topic.
    
    Args:
        entries: List of all entry dictionaries
        topic_entry_ids: List of entry IDs belonging to the topic
        
    Returns:
        Filtered list of entries
    """
    return [e for e in entries if e.get('id') in topic_entry_ids]
