"""
News API Client for Financial News Collection

Handles data retrieval from multiple news sources including
NewsAPI, Alpha Vantage, and financial news feeds.
"""

import os
import asyncio
import aiohttp
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass
import logging
import feedparser
from bs4 import BeautifulSoup
import json

logger = logging.getLogger(__name__)


@dataclass
class NewsArticle:
    """News article data structure"""
    title: str
    description: str
    content: Optional[str]
    source: str
    url: str
    published_at: datetime
    author: Optional[str] = None
    sentiment_score: Optional[float] = None
    symbols: Optional[List[str]] = None
    

class NewsClient:
    """
    Client for fetching financial news from multiple sources
    """
    
    def __init__(
        self,
        newsapi_key: Optional[str] = None,
        alphavantage_key: Optional[str] = None
    ):
        """
        Initialize news client
        
        Args:
            newsapi_key: NewsAPI.org API key
            alphavantage_key: Alpha Vantage API key
        """
        self.newsapi_key = newsapi_key or os.getenv("NEWSAPI_KEY")
        self.alphavantage_key = alphavantage_key or os.getenv("ALPHAVANTAGE_KEY")
        
        # API endpoints
        self.newsapi_url = "https://newsapi.org/v2"
        self.alphavantage_url = "https://www.alphavantage.co/query"
        
        # Financial news RSS feeds
        self.rss_feeds = {
            'reuters': 'https://feeds.reuters.com/reuters/businessNews',
            'bloomberg': 'https://feeds.bloomberg.com/markets/news.rss',
            'wsj': 'https://feeds.a.dj.com/rss/WSJcomUSBusiness.xml',
            'ft': 'https://www.ft.com/markets?format=rss',
            'cnbc': 'https://www.cnbc.com/id/10001147/device/rss/rss.html',
            'marketwatch': 'https://feeds.marketwatch.com/marketwatch/topstories/'
        }
        
        # Financial news sources for NewsAPI
        self.news_sources = [
            'bloomberg', 'business-insider', 'cnbc', 'financial-times',
            'fortune', 'the-wall-street-journal', 'reuters'
        ]
        
    async def get_market_news(
        self,
        keywords: Optional[List[str]] = None,
        hours_back: int = 24,
        max_articles: int = 100
    ) -> List[NewsArticle]:
        """
        Get recent market news articles
        
        Args:
            keywords: Keywords to filter articles
            hours_back: Hours to look back
            max_articles: Maximum articles to retrieve
            
        Returns:
            List of NewsArticle objects
        """
        articles = []
        
        # Fetch from multiple sources concurrently
        tasks = [
            self._fetch_newsapi_articles(keywords, hours_back),
            self._fetch_rss_articles(hours_back),
            self._fetch_alphavantage_news()
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for result in results:
            if isinstance(result, list):
                articles.extend(result)
            elif isinstance(result, Exception):
                logger.error(f"Error fetching news: {result}")
        
        # Sort by published date and limit
        articles.sort(key=lambda x: x.published_at, reverse=True)
        
        return articles[:max_articles]
    
    async def _fetch_newsapi_articles(
        self,
        keywords: Optional[List[str]] = None,
        hours_back: int = 24
    ) -> List[NewsArticle]:
        """Fetch articles from NewsAPI"""
        if not self.newsapi_key:
            logger.warning("NewsAPI key not configured")
            return []
        
        try:
            articles = []
            
            # Build query
            if keywords:
                query = ' OR '.join(keywords)
            else:
                query = 'stock market OR trading OR finance OR economy'
            
            # Date range
            from_date = (datetime.utcnow() - timedelta(hours=hours_back)).isoformat()
            
            # API parameters
            params = {
                'apiKey': self.newsapi_key,
                'q': query,
                'sources': ','.join(self.news_sources),
                'from': from_date,
                'sortBy': 'popularity',
                'pageSize': 50
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.newsapi_url}/everything",
                    params=params
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        for article in data.get('articles', []):
                            news_article = NewsArticle(
                                title=article['title'],
                                description=article['description'] or '',
                                content=article['content'],
                                source=article['source']['name'],
                                url=article['url'],
                                published_at=datetime.fromisoformat(
                                    article['publishedAt'].replace('Z', '+00:00')
                                ),
                                author=article.get('author')
                            )
                            articles.append(news_article)
            
            logger.info(f"Fetched {len(articles)} articles from NewsAPI")
            return articles
            
        except Exception as e:
            logger.error(f"Error fetching NewsAPI articles: {e}")
            return []
    
    async def _fetch_rss_articles(self, hours_back: int = 24) -> List[NewsArticle]:
        """Fetch articles from RSS feeds"""
        articles = []
        cutoff_time = datetime.utcnow() - timedelta(hours=hours_back)
        
        async def fetch_feed(source: str, url: str):
            try:
                feed = feedparser.parse(url)
                
                for entry in feed.entries[:20]:  # Limit per feed
                    # Parse published date
                    if hasattr(entry, 'published_parsed'):
                        published = datetime.fromtimestamp(
                            feedparser._parse_date(entry.published).timestamp()
                        )
                    else:
                        published = datetime.utcnow()
                    
                    # Skip old articles
                    if published < cutoff_time:
                        continue
                    
                    # Extract content
                    content = entry.get('summary', '')
                    if hasattr(entry, 'content'):
                        content = entry.content[0].value if entry.content else content
                    
                    news_article = NewsArticle(
                        title=entry.title,
                        description=BeautifulSoup(
                            entry.get('summary', ''), 
                            'html.parser'
                        ).get_text()[:500],
                        content=BeautifulSoup(content, 'html.parser').get_text(),
                        source=source.upper(),
                        url=entry.link,
                        published_at=published,
                        author=entry.get('author')
                    )
                    articles.append(news_article)
                    
            except Exception as e:
                logger.error(f"Error fetching RSS feed {source}: {e}")
        
        # Fetch all feeds concurrently
        tasks = [fetch_feed(source, url) for source, url in self.rss_feeds.items()]
        await asyncio.gather(*tasks)
        
        logger.info(f"Fetched {len(articles)} articles from RSS feeds")
        return articles
    
    async def _fetch_alphavantage_news(self) -> List[NewsArticle]:
        """Fetch news sentiment from Alpha Vantage"""
        if not self.alphavantage_key:
            logger.warning("Alpha Vantage key not configured")
            return []
        
        try:
            articles = []
            
            params = {
                'function': 'NEWS_SENTIMENT',
                'apikey': self.alphavantage_key,
                'topics': 'technology,finance',
                'time_from': (datetime.utcnow() - timedelta(hours=24)).strftime('%Y%m%dT%H%M')
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(self.alphavantage_url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        for item in data.get('feed', [])[:30]:
                            # Parse time
                            time_str = item['time_published']
                            published = datetime.strptime(
                                time_str[:14], 
                                '%Y%m%dT%H%M%S'
                            )
                            
                            news_article = NewsArticle(
                                title=item['title'],
                                description=item.get('summary', '')[:500],
                                content=item.get('summary', ''),
                                source=item['source'],
                                url=item['url'],
                                published_at=published,
                                sentiment_score=float(item.get('overall_sentiment_score', 0))
                            )
                            
                            # Extract ticker symbols
                            tickers = [
                                t['ticker'] for t in item.get('ticker_sentiment', [])
                            ]
                            news_article.symbols = tickers
                            
                            articles.append(news_article)
            
            logger.info(f"Fetched {len(articles)} articles from Alpha Vantage")
            return articles
            
        except Exception as e:
            logger.error(f"Error fetching Alpha Vantage news: {e}")
            return []
    
    async def get_symbol_news(
        self,
        symbol: str,
        hours_back: int = 24
    ) -> List[NewsArticle]:
        """
        Get news articles for a specific symbol
        
        Args:
            symbol: Stock symbol
            hours_back: Hours to look back
            
        Returns:
            List of NewsArticle objects
        """
        # Search for symbol-specific news
        keywords = [symbol, f"${symbol}"]
        
        # Add company name variations if known
        company_keywords = {
            'AAPL': ['Apple', 'iPhone', 'Tim Cook'],
            'MSFT': ['Microsoft', 'Windows', 'Azure'],
            'GOOGL': ['Google', 'Alphabet', 'Android'],
            'AMZN': ['Amazon', 'AWS', 'Bezos'],
            'TSLA': ['Tesla', 'Elon Musk', 'EV'],
            'META': ['Meta', 'Facebook', 'Zuckerberg'],
            'NVDA': ['Nvidia', 'GPU', 'AI chips']
        }
        
        if symbol in company_keywords:
            keywords.extend(company_keywords[symbol])
        
        articles = await self.get_market_news(
            keywords=keywords,
            hours_back=hours_back
        )
        
        # Filter to ensure relevance
        relevant_articles = []
        for article in articles:
            title_lower = article.title.lower()
            desc_lower = article.description.lower() if article.description else ''
            
            # Check if symbol or related keywords appear
            if any(kw.lower() in title_lower or kw.lower() in desc_lower 
                   for kw in keywords):
                article.symbols = [symbol]
                relevant_articles.append(article)
        
        return relevant_articles
    
    async def get_breaking_news(self) -> List[NewsArticle]:
        """Get breaking financial news from the last hour"""
        return await self.get_market_news(
            keywords=['breaking', 'alert', 'urgent', 'just in'],
            hours_back=1,
            max_articles=20
        )