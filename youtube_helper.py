"""
YouTube API Helper for fetching educational videos
"""

import os
import requests
from dotenv import load_dotenv, find_dotenv
from typing import List, Dict, Optional

# Load environment variables
load_dotenv(find_dotenv())


def search_youtube_videos(query: str, max_results: int = 5) -> List[Dict]:
    """
    Search for educational YouTube videos based on a query.
    
    Args:
        query (str): Search query (topic/concept to find videos for)
        max_results (int): Maximum number of videos to return (default: 5)
    
    Returns:
        List[Dict]: List of video information dictionaries
    """
    try:
        # Get YouTube API key from environment
        youtube_api_key = os.getenv("YOUTUBE_API_KEY")
        
        if not youtube_api_key:
            print("Warning: YOUTUBE_API_KEY not found. Using fallback method.")
            return search_youtube_fallback(query, max_results)
        
        # YouTube Data API v3 endpoint
        search_url = "https://www.googleapis.com/youtube/v3/search"
        
        # Search parameters
        params = {
            'part': 'snippet',
            'q': f"{query} tutorial explanation",
            'type': 'video',
            'maxResults': max_results,
            'key': youtube_api_key,
            'videoCategoryId': '27',  # Education category
            'order': 'relevance',
            'safeSearch': 'strict',
            'videoDefinition': 'high',
        }
        
        # Make API request
        response = requests.get(search_url, params=params)
        response.raise_for_status()
        data = response.json()
        
        videos = []
        video_ids = []
        
        # Extract video information
        for item in data.get('items', []):
            video_id = item['id'].get('videoId')
            if video_id:
                video_ids.append(video_id)
                snippet = item['snippet']
                
                video_info = {
                    'video_id': video_id,
                    'title': snippet.get('title', ''),
                    'description': snippet.get('description', ''),
                    'channel_name': snippet.get('channelTitle', ''),
                    'thumbnail_url': snippet.get('thumbnails', {}).get('high', {}).get('url', ''),
                    'url': f"https://www.youtube.com/watch?v={video_id}",
                }
                videos.append(video_info)
        
        # Get additional video details (duration, view count)
        if video_ids:
            videos = enrich_video_details(videos, video_ids, youtube_api_key)
        
        return videos
        
    except Exception as e:
        print(f"Error searching YouTube: {str(e)}")
        return search_youtube_fallback(query, max_results)


def enrich_video_details(videos: List[Dict], video_ids: List[str], api_key: str) -> List[Dict]:
    """
    Enrich video information with duration and statistics.
    """
    try:
        videos_url = "https://www.googleapis.com/youtube/v3/videos"
        params = {
            'part': 'contentDetails,statistics',
            'id': ','.join(video_ids),
            'key': api_key,
        }
        
        response = requests.get(videos_url, params=params)
        response.raise_for_status()
        data = response.json()
        
        # Create a mapping of video_id to details
        details_map = {}
        for item in data.get('items', []):
            video_id = item['id']
            duration = item.get('contentDetails', {}).get('duration', '')
            view_count = item.get('statistics', {}).get('viewCount', 0)
            
            details_map[video_id] = {
                'duration': parse_duration(duration),
                'view_count': int(view_count) if view_count else 0,
            }
        
        # Enrich videos with details
        for video in videos:
            video_id = video['video_id']
            if video_id in details_map:
                video.update(details_map[video_id])
        
        return videos
        
    except Exception as e:
        print(f"Error enriching video details: {str(e)}")
        return videos


def parse_duration(duration: str) -> str:
    """
    Parse ISO 8601 duration format (PT1H2M10S) to readable format (1:02:10).
    """
    import re

    if not duration:
        return ""

    match = re.match(r'PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?', duration)
    if not match:
        return ""

    hours, minutes, seconds = match.groups()
    hours = int(hours) if hours else 0
    minutes = int(minutes) if minutes else 0
    seconds = int(seconds) if seconds else 0

    if hours > 0:
        return f"{hours}:{minutes:02d}:{seconds:02d}"
    else:
        return f"{minutes}:{seconds:02d}"


def search_youtube_fallback(query: str, max_results: int = 5) -> List[Dict]:
    """
    Fallback method that scrapes YouTube search results without API.
    Uses web scraping to get actual video recommendations.
    """
    try:
        import re
        from urllib.parse import quote_plus

        # Clean and format the query
        search_query = f"{query} tutorial"
        encoded_query = quote_plus(search_query)
        search_url = f"https://www.youtube.com/results?search_query={encoded_query}"

        # Make request to YouTube search
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(search_url, headers=headers, timeout=10)
        response.raise_for_status()

        # Extract video data from the page
        videos = []

        # Find all video IDs in the response
        video_id_pattern = r'"videoId":"([a-zA-Z0-9_-]{11})"'
        title_pattern = r'"title":{"runs":\[{"text":"([^"]+)"}]'
        channel_pattern = r'"ownerText":{"runs":\[{"text":"([^"]+)"'

        video_ids = re.findall(video_id_pattern, response.text)
        titles = re.findall(title_pattern, response.text)
        channels = re.findall(channel_pattern, response.text)

        # Combine the data (limit to max_results)
        for i in range(min(len(video_ids), max_results)):
            if i < len(video_ids):
                video_id = video_ids[i]
                title = titles[i] if i < len(titles) else f"Video about {query}"
                channel = channels[i] if i < len(channels) else "Educational Channel"

                videos.append({
                    'video_id': video_id,
                    'title': title,
                    'description': f"Educational video about {query}",
                    'channel_name': channel,
                    'thumbnail_url': f"https://i.ytimg.com/vi/{video_id}/hqdefault.jpg",
                    'url': f"https://www.youtube.com/watch?v={video_id}",
                    'duration': '',
                    'view_count': 0,
                })

        return videos if videos else _get_fallback_search_link(query)

    except Exception as e:
        print(f"Error in fallback YouTube search: {str(e)}")
        return _get_fallback_search_link(query)


def _get_fallback_search_link(query: str) -> List[Dict]:
    """
    Last resort: Generate a YouTube search link.
    """
    from urllib.parse import quote_plus
    search_query = f"{query} tutorial"
    encoded_query = quote_plus(search_query)

    return [{
        'video_id': 'search',
        'title': f"Search YouTube for: {query}",
        'description': f"Click to search for educational videos about {query}",
        'channel_name': 'YouTube Search',
        'thumbnail_url': 'https://www.youtube.com/img/desktop/yt_1200.png',
        'url': f"https://www.youtube.com/results?search_query={encoded_query}",
        'duration': '',
        'view_count': 0,
    }]


def get_curated_channels_for_topic(topic: str) -> List[str]:
    """
    Return a list of recommended educational YouTube channels based on topic.
    This can be used to filter search results or suggest channels.
    """
    topic_lower = topic.lower()

    # General educational channels
    general_channels = [
        "Khan Academy",
        "Crash Course",
        "TED-Ed",
        "Kurzgesagt",
    ]

    # Topic-specific channels
    if any(keyword in topic_lower for keyword in ['math', 'calculus', 'algebra', 'geometry']):
        return general_channels + ["3Blue1Brown", "PatrickJMT", "Professor Leonard"]

    elif any(keyword in topic_lower for keyword in ['physics', 'mechanics', 'quantum']):
        return general_channels + ["Physics Girl", "MinutePhysics", "PBS Space Time"]

    elif any(keyword in topic_lower for keyword in ['chemistry', 'organic', 'biochem']):
        return general_channels + ["NileRed", "Professor Dave Explains", "The Organic Chemistry Tutor"]

    elif any(keyword in topic_lower for keyword in ['programming', 'coding', 'python', 'java', 'javascript']):
        return ["freeCodeCamp", "Traversy Media", "Programming with Mosh", "The Net Ninja", "Corey Schafer"]

    elif any(keyword in topic_lower for keyword in ['biology', 'anatomy', 'genetics']):
        return general_channels + ["Amoeba Sisters", "Professor Dave Explains", "Ninja Nerd"]

    elif any(keyword in topic_lower for keyword in ['history', 'world war', 'ancient']):
        return ["Crash Course", "History Matters", "OverSimplified", "Extra Credits"]

    elif any(keyword in topic_lower for keyword in ['economics', 'finance', 'business']):
        return ["Economics Explained", "The Plain Bagel", "Patrick Boyle", "Khan Academy"]

    else:
        return general_channels


