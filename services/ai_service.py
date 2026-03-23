"""
Azure OpenAI Service Module

Handles all interactions with Azure OpenAI for:
- Abstractive summarization of journal entries
- Sentiment analysis and insights extraction
"""

import os
import logging
from openai import AzureOpenAI, APIError, APIConnectionError, RateLimitError

logger = logging.getLogger(__name__)


def _check_azure_openai_config():
    """Check if Azure OpenAI credentials are configured."""
    required_vars = ['AZURE_OPENAI_KEY', 'AZURE_OPENAI_ENDPOINT', 'AZURE_OPENAI_MODEL_NAME']
    missing = [var for var in required_vars if not os.environ.get(var)]
    if missing:
        return False, f"Missing Azure OpenAI config: {', '.join(missing)}"
    return True, None


def get_openai_client():
    """Initialize and return Azure OpenAI client. Raises error if config missing."""
    is_configured, error_msg = _check_azure_openai_config()
    if not is_configured:
        raise ValueError(error_msg)
    
    return AzureOpenAI(
        api_key=os.environ.get("AZURE_OPENAI_KEY"),
        api_version="2024-12-01-preview",
        azure_endpoint=os.environ.get("AZURE_OPENAI_ENDPOINT")
    )


def get_summary(entries_text: str, max_length: int = 150) -> str:
    """
    Generate an abstractive summary of journal entries using Azure OpenAI.
    
    Args:
        entries_text: Combined text of selected journal entries
        max_length: Maximum length of summary in characters (rough guide)
    
    Returns:
        Summary text, or fallback message if API fails
    """
    try:
        is_configured, error_msg = _check_azure_openai_config()
        if not is_configured:
            logger.warning(error_msg)
            return "⚠️ Azure OpenAI not configured. Please set AZURE_OPENAI_KEY, AZURE_OPENAI_ENDPOINT, and AZURE_OPENAI_MODEL_NAME."
        
        client = get_openai_client()
        
        prompt = f"""Summarize the following journal entries in 2-3 sentences. 
Paraphrase naturally and capture the main themes and emotions.

Journal entries:
{entries_text}

Summary:"""
        
        response = client.chat.completions.create(
            model=os.environ.get("AZURE_OPENAI_MODEL_NAME", "gpt-4o-mini"),
            messages=[
                {"role": "system", "content": "You are a thoughtful journal assistant. Create natural, paraphrased summaries."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=200
        )
        
        return response.choices[0].message.content.strip()
    
    except (APIConnectionError, RateLimitError) as e:
        logger.error(f"Azure OpenAI API error: {str(e)}")
        return f"⚠️ Service temporarily unavailable. Please try again later."
    except APIError as e:
        logger.error(f"Azure OpenAI error: {str(e)}")
        return f"⚠️ Error generating summary: {str(e)[:100]}"
    except Exception as e:
        logger.error(f"Unexpected error in get_summary: {str(e)}")
        return f"⚠️ Error generating summary. Please try again."


def get_insights(entries_text: str) -> dict:
    """
    Extract sentiment and key insights from journal entries using Azure OpenAI.
    
    Args:
        entries_text: Combined text of selected journal entries
    
    Returns:
        Dict with 'sentiment' and 'insights' keys
    """
    try:
        is_configured, error_msg = _check_azure_openai_config()
        if not is_configured:
            logger.warning(error_msg)
            return {
                "sentiment": "unknown",
                "insights": ["Azure OpenAI not configured. Cannot extract insights."]
            }
        
        client = get_openai_client()
        
        prompt = f"""Analyze these journal entries and provide:
1. Overall sentiment (positive, neutral, negative, mixed)
2. 2-3 key insights or patterns

Journal entries:
{entries_text}

Respond in this exact format:
Sentiment: [sentiment]
Insights:
- [insight 1]
- [insight 2]
- [insight 3]"""
        
        response = client.chat.completions.create(
            model=os.environ.get("AZURE_OPENAI_MODEL_NAME", "gpt-4o-mini"),
            messages=[
                {"role": "system", "content": "You are a thoughtful journal assistant. Analyze sentiment and extract key themes."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.5,
            max_tokens=300
        )
        
        result_text = response.choices[0].message.content.strip()
        
        # Parse response
        sentiment = "unknown"
        insights = []
        
        lines = result_text.split('\n')
        for line in lines:
            if line.startswith("Sentiment:"):
                sentiment = line.replace("Sentiment:", "").strip().lower()
            elif line.startswith("- "):
                insights.append(line.replace("- ", "").strip())
        
        return {
            "sentiment": sentiment,
            "insights": insights if insights else ["No specific insights extracted."]
        }
    
    except (APIConnectionError, RateLimitError) as e:
        logger.error(f"Azure OpenAI API error in insights: {str(e)}")
        return {
            "sentiment": "unknown",
            "insights": ["Service temporarily unavailable. Please try again later."]
        }
    except APIError as e:
        logger.error(f"Azure OpenAI error in insights: {str(e)}")
        return {
            "sentiment": "unknown",
            "insights": [f"Error extracting insights: {str(e)[:50]}"]
        }
    except Exception as e:
        logger.error(f"Unexpected error in get_insights: {str(e)}")
        return {
            "sentiment": "unknown",
            "insights": ["Error extracting insights. Please try again."]
        }
