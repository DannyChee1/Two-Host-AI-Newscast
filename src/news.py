import requests
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import re


class NewsAPIError(Exception):
    pass


def fetch_news(
    api_key: str,
    topics: List[str],
    region: str = 'us',
    max_stories: int = 5,
    hours_back: int = 24
) -> List[Dict]:

    to_date = datetime.now()
    from_date = to_date - timedelta(hours=hours_back)
    from_str = from_date.strftime('%Y-%m-%dT%H:%M:%S')
    
    all_articles = []
    
    for topic in topics:
        articles = _fetch_by_topic(api_key, topic, region, from_str)
        all_articles.extend(articles)
    
    if not all_articles:
        print("No articles found for provided topics, trying top headlines...")
        all_articles = _fetch_top_headlines(api_key, region)
    
    if not all_articles:
        raise NewsAPIError("No news articles found. Check your API key or try different topics.")
       
    articles = deduplicate_articles(all_articles)

    articles = sorted(articles, key=lambda x: x.get('publishedAt', ''), reverse=True)
    
    articles = articles[:max_stories]
    
    stories = []
    for idx, article in enumerate(articles):
        story = {
            'id': idx,
            'title': article.get('title', 'Untitled'),
            'url': article.get('url', ''),
            'source': article.get('source', {}).get('name', 'Unknown Source'),
            'summary': _create_summary(article),
            'publishedAt': article.get('publishedAt', '')
        }
        stories.append(story)
    
    print(f"   Selected {len(stories)} stories for podcast")
    
    return stories


def _fetch_by_topic(api_key: str, topic: str, region: str, from_date: str) -> List[Dict]:
    url = 'https://newsapi.org/v2/everything'
    
    params = {
        'apiKey': api_key,
        'q': topic,
        'from': from_date,
        'language': 'en',
        'sortBy': 'publishedAt',
        'pageSize': 20
    }
    
    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if data.get('status') == 'ok':
            return data.get('articles', [])
        else:
            print(f"   Warning: API returned status '{data.get('status')}' for topic '{topic}'")
            return []
    
    except requests.exceptions.RequestException as e:
        print(f"   Warning: Failed to fetch articles for topic '{topic}': {e}")
        return []


def _fetch_top_headlines(api_key: str, region: str) -> List[Dict]:
    url = 'https://newsapi.org/v2/top-headlines'
    
    params = {
        'apiKey': api_key,
        'country': region,
        'pageSize': 20
    }
    
    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if data.get('status') == 'ok':
            return data.get('articles', [])
        else:
            error_msg = data.get('message', 'Unknown error')
            raise NewsAPIError(f"NewsAPI error: {error_msg}")
    
    except requests.exceptions.RequestException as e:
        raise NewsAPIError(f"Failed to connect to NewsAPI: {e}")


def deduplicate_articles(articles: List[Dict]) -> List[Dict]:
    seen_urls = set()
    seen_titles = set()
    unique_articles = []
    
    for article in articles:
        url = article.get('url', '')
        title = article.get('title', '')
        
        if not title or not url:
            continue
        
        normalized_title = re.sub(r'[^a-z0-9\s]', '', title.lower())
        normalized_title = ' '.join(normalized_title.split())

        if url in seen_urls:
            continue

        is_duplicate = False
        for seen_title in seen_titles:
            if _titles_similar(normalized_title, seen_title):
                is_duplicate = True
                break
        
        if is_duplicate:
            continue

        seen_urls.add(url)
        seen_titles.add(normalized_title)
        unique_articles.append(article)

    return unique_articles


def _titles_similar(title1: str, title2: str, threshold: float = 0.8) -> bool:
    words1 = set(title1.split())
    words2 = set(title2.split())

    if not words1 or not words2:
        return False

    intersection = len(words1.intersection(words2))
    union = len(words1.union(words2))
    similarity = intersection / union if union > 0 else 0

    return similarity >= threshold


def _create_summary(article: Dict) -> str:
    description = article.get('description', '')
    content = article.get('content', '')
    title = article.get('title', '')
    
    if description and len(description.strip()) > 20:
        summary = description.strip()
    elif content and len(content.strip()) > 20:
        summary = re.sub(r'\[\+\d+\s+chars?\]', '', content).strip()
    else:
        summary = title

    sentences = re.split(r'(?<=[.!?])\s+', summary)
    summary = ' '.join(sentences[:2])
    
    if summary and not summary[-1] in '.!?':
        summary += '.'
    
    return summary


def validate_news_data(stories: List[Dict]) -> bool:
    if not stories:
        raise ValueError("No news stories provided")
    
    if len(stories) < 3:
        print(f"   Warning: Only {len(stories)} stories (recommended: 3-6)")
    
    required_fields = ['id', 'title', 'url', 'source', 'summary']
    
    for story in stories:
        for field in required_fields:
            if field not in story:
                raise ValueError(f"Story {story.get('id', '?')} missing required field: {field}")
            if not story[field] and field != 'id':
                raise ValueError(f"Story {story.get('id', '?')} has empty field: {field}")
    
    return True