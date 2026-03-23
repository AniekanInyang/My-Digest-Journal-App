"""
Test Topic Clustering Service

Run this to test the topic clustering functionality.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from services.topic_service import cluster_entries_with_llm


def test_topic_clustering():
    """Test topic clustering with sample entries."""
    
    # Sample journal entries
    sample_entries = [
        {
            'id': 1,
            'content': 'Had a productive day at work. Finished the project presentation and got positive feedback from my manager. Team collaboration was great.',
            'created_at': '2026-03-20T10:00:00Z'
        },
        {
            'id': 2,
            'content': 'Went for a 5km run this morning. Feeling energized and healthy. Need to keep up this exercise routine.',
            'created_at': '2026-03-19T07:00:00Z'
        },
        {
            'id': 3,
            'content': 'Date night with Sarah was wonderful. We tried that new Italian restaurant and had great conversation.',
            'created_at': '2026-03-18T19:00:00Z'
        },
        {
            'id': 4,
            'content': 'Stressed about the upcoming deadline. Too many tasks and not enough time. Need to prioritize better.',
            'created_at': '2026-03-17T15:00:00Z'
        },
        {
            'id': 5,
            'content': 'Team meeting went well. Discussed the new feature roadmap and assigned tasks. Looking forward to the challenge.',
            'created_at': '2026-03-16T11:00:00Z'
        },
        {
            'id': 6,
            'content': 'Yoga class was relaxing. Finally getting back into my wellness routine. Mental health is improving.',
            'created_at': '2026-03-15T08:00:00Z'
        },
        {
            'id': 7,
            'content': 'Argument with Sarah about household responsibilities. Need to communicate better and find a compromise.',
            'created_at': '2026-03-14T20:00:00Z'
        },
        {
            'id': 8,
            'content': 'Completed the code review today. Found some bugs but overall the team is doing solid work.',
            'created_at': '2026-03-13T14:00:00Z'
        },
        {
            'id': 9,
            'content': 'Started reading that new sci-fi novel. Love getting lost in a good book after work.',
            'created_at': '2026-03-12T21:00:00Z'
        },
        {
            'id': 10,
            'content': 'Meal prep Sunday! Cooked healthy meals for the week. Proud of staying consistent with nutrition.',
            'created_at': '2026-03-11T16:00:00Z'
        }
    ]
    
    print("Testing Topic Clustering...")
    print(f"Analyzing {len(sample_entries)} sample entries...\n")
    
    try:
        topics = cluster_entries_with_llm(sample_entries, num_topics=5)
        
        if topics:
            print(f"✅ Successfully identified {len(topics)} topics:\n")
            
            for i, topic in enumerate(topics, 1):
                print(f"{i}. {topic['emoji']} {topic['name']}")
                print(f"   Entries: {topic['count']}")
                print(f"   Keywords: {', '.join(topic['keywords'])}")
                print(f"   Entry IDs: {topic['entry_ids']}")
                print()
            
            print("✅ Topic clustering test passed!")
            return True
        else:
            print("❌ No topics returned")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    # Make sure environment variables are loaded
    from dotenv import load_dotenv
    load_dotenv()
    
    # Check if Azure OpenAI is configured
    if not os.environ.get('AZURE_OPENAI_KEY'):
        print("❌ AZURE_OPENAI_KEY not found in environment")
        print("Please make sure .env file is configured")
        sys.exit(1)
    
    success = test_topic_clustering()
    sys.exit(0 if success else 1)
