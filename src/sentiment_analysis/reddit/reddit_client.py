"""
Reddit API Client for WSB and Financial Subreddits

Handles data collection from Reddit's financial communities
including WallStreetBets, stocks, options, and investing.
"""

import os
import praw
import asyncpraw
from typing import List, Dict, Optional, Set
from datetime import datetime, timedelta
from dataclasses import dataclass
import logging
import re
import asyncio
from collections import defaultdict

logger = logging.getLogger(__name__)


@dataclass
class RedditPost:
    """Reddit post/comment data structure"""
    id: str
    title: Optional[str]
    body: str
    author: str
    score: int
    created_utc: datetime
    subreddit: str
    num_comments: Optional[int] = None
    is_comment: bool = False
    parent_id: Optional[str] = None
    awards: Optional[int] = None
    upvote_ratio: Optional[float] = None
    

class RedditClient:
    """
    Client for Reddit API focused on financial subreddits
    """
    
    def __init__(
        self,
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None,
        user_agent: Optional[str] = None
    ):
        """
        Initialize Reddit client
        
        Args:
            client_id: Reddit app client ID
            client_secret: Reddit app client secret
            user_agent: User agent string
        """
        self.client_id = client_id or os.getenv("REDDIT_CLIENT_ID")
        self.client_secret = client_secret or os.getenv("REDDIT_CLIENT_SECRET")
        self.user_agent = user_agent or "HydraX Sentiment Analyzer v1.0"
        
        if not self.client_id or not self.client_secret:
            logger.warning("Reddit credentials not configured")
            self.reddit = None
            self.async_reddit = None
        else:
            # Initialize synchronous client
            self.reddit = praw.Reddit(
                client_id=self.client_id,
                client_secret=self.client_secret,
                user_agent=self.user_agent
            )
            
            # Initialize async client
            self.async_reddit = asyncpraw.Reddit(
                client_id=self.client_id,
                client_secret=self.client_secret,
                user_agent=self.user_agent
            )
        
        # Financial subreddits to monitor
        self.financial_subreddits = [
            'wallstreetbets', 'stocks', 'investing', 'options',
            'SecurityAnalysis', 'StockMarket', 'Daytrading',
            'pennystocks', 'RobinHood', 'algotrading', 'Forex',
            'CryptoCurrency', 'SPACs', 'thetagang', 'Vitards'
        ]
        
        # WSB-specific slang and terms
        self.wsb_terms = {
            'yolo': 'high risk trade',
            'diamond hands': 'holding position',
            'paper hands': 'selling early',
            'tendies': 'profits',
            'fd': 'risky options',
            'guh': 'major loss',
            'moon': 'price increase',
            'rocket': 'rapid growth',
            'ape': 'retail investor',
            'smooth brain': 'inexperienced',
            'dd': 'due diligence',
            'gain porn': 'profit posts',
            'loss porn': 'loss posts',
            'theta gang': 'options sellers',
            'bear': 'pessimistic',
            'bull': 'optimistic',
            'stonks': 'stocks',
            'hodl': 'hold position',
            'to the moon': 'expecting rise',
            'bag holder': 'holding losses',
            'pump and dump': 'manipulation'
        }
        
        # Stock ticker pattern
        self.ticker_pattern = re.compile(r'\b[A-Z]{1,5}\b')
        self.option_pattern = re.compile(r'[A-Z]{1,5}\s+\d+[cp]\s*\d+/?(?:\d+)?')
        
    async def get_wsb_posts(
        self,
        time_filter: str = 'day',
        limit: int = 100,
        min_score: int = 10
    ) -> List[RedditPost]:
        """
        Get top posts from WallStreetBets
        
        Args:
            time_filter: Time filter (hour, day, week, month)
            limit: Maximum posts to retrieve
            min_score: Minimum score to include
            
        Returns:
            List of RedditPost objects
        """
        if not self.async_reddit:
            logger.error("Reddit client not initialized")
            return []
        
        posts = []
        
        try:
            subreddit = await self.async_reddit.subreddit("wallstreetbets")
            
            # Get hot posts
            async for submission in subreddit.hot(limit=limit//2):
                if submission.score >= min_score:
                    post = RedditPost(
                        id=submission.id,
                        title=submission.title,
                        body=submission.selftext,
                        author=str(submission.author) if submission.author else '[deleted]',
                        score=submission.score,
                        created_utc=datetime.fromtimestamp(submission.created_utc),
                        subreddit='wallstreetbets',
                        num_comments=submission.num_comments,
                        awards=submission.total_awards_received,
                        upvote_ratio=submission.upvote_ratio
                    )
                    posts.append(post)
            
            # Get top posts from time period
            async for submission in subreddit.top(time_filter=time_filter, limit=limit//2):
                if submission.score >= min_score:
                    post = RedditPost(
                        id=submission.id,
                        title=submission.title,
                        body=submission.selftext,
                        author=str(submission.author) if submission.author else '[deleted]',
                        score=submission.score,
                        created_utc=datetime.fromtimestamp(submission.created_utc),
                        subreddit='wallstreetbets',
                        num_comments=submission.num_comments,
                        awards=submission.total_awards_received,
                        upvote_ratio=submission.upvote_ratio
                    )
                    posts.append(post)
            
            logger.info(f"Retrieved {len(posts)} WSB posts")
            
        except Exception as e:
            logger.error(f"Error fetching WSB posts: {e}")
        finally:
            await self.async_reddit.close()
        
        return posts
    
    async def get_trending_tickers(
        self,
        subreddits: Optional[List[str]] = None,
        hours_back: int = 24,
        min_mentions: int = 5
    ) -> Dict[str, Dict]:
        """
        Get trending stock tickers from Reddit
        
        Args:
            subreddits: Subreddits to scan (default: financial subreddits)
            hours_back: Hours to look back
            min_mentions: Minimum mentions to be considered trending
            
        Returns:
            Dictionary of ticker data with mention counts and sentiment
        """
        if not self.async_reddit:
            return {}
        
        subreddits = subreddits or ['wallstreetbets', 'stocks', 'options']
        ticker_data = defaultdict(lambda: {
            'mentions': 0,
            'score': 0,
            'posts': [],
            'sentiment': {'bullish': 0, 'bearish': 0, 'neutral': 0}
        })
        
        # Common words to exclude (not tickers)
        exclude_words = {
            'USA', 'CEO', 'FDA', 'IPO', 'ETF', 'NYSE', 'GDP', 'API',
            'USD', 'EUR', 'GBP', 'CNN', 'CNBC', 'WSB', 'DD', 'YOLO',
            'IMO', 'FOMO', 'FUD', 'ATH', 'LOL', 'WTF', 'IDK', 'TBH'
        }
        
        try:
            cutoff_time = datetime.utcnow() - timedelta(hours=hours_back)
            
            for sub_name in subreddits:
                subreddit = await self.async_reddit.subreddit(sub_name)
                
                # Get new posts
                async for submission in subreddit.new(limit=200):
                    if datetime.fromtimestamp(submission.created_utc) < cutoff_time:
                        break
                    
                    # Extract tickers from title and body
                    text = f"{submission.title} {submission.selftext}"
                    tickers = self._extract_tickers(text, exclude_words)
                    
                    for ticker in tickers:
                        ticker_data[ticker]['mentions'] += 1
                        ticker_data[ticker]['score'] += submission.score
                        ticker_data[ticker]['posts'].append({
                            'id': submission.id,
                            'title': submission.title[:100],
                            'score': submission.score,
                            'subreddit': sub_name
                        })
                        
                        # Basic sentiment from title
                        sentiment = self._get_basic_sentiment(submission.title)
                        ticker_data[ticker]['sentiment'][sentiment] += 1
                
                # Also check hot posts
                async for submission in subreddit.hot(limit=50):
                    if datetime.fromtimestamp(submission.created_utc) < cutoff_time:
                        continue
                    
                    text = f"{submission.title} {submission.selftext}"
                    tickers = self._extract_tickers(text, exclude_words)
                    
                    for ticker in tickers:
                        if ticker not in ticker_data:
                            ticker_data[ticker]['mentions'] += 1
                            ticker_data[ticker]['score'] += submission.score
            
            # Filter by minimum mentions
            trending = {
                ticker: data 
                for ticker, data in ticker_data.items() 
                if data['mentions'] >= min_mentions
            }
            
            # Sort by mentions
            sorted_trending = dict(
                sorted(trending.items(), key=lambda x: x[1]['mentions'], reverse=True)
            )
            
            logger.info(f"Found {len(sorted_trending)} trending tickers")
            
        except Exception as e:
            logger.error(f"Error getting trending tickers: {e}")
            sorted_trending = {}
        finally:
            await self.async_reddit.close()
        
        return sorted_trending
    
    async def get_dd_posts(
        self,
        hours_back: int = 48,
        min_length: int = 500
    ) -> List[RedditPost]:
        """
        Get Due Diligence (DD) posts
        
        Args:
            hours_back: Hours to look back
            min_length: Minimum post length
            
        Returns:
            List of DD posts
        """
        if not self.async_reddit:
            return []
        
        dd_posts = []
        cutoff_time = datetime.utcnow() - timedelta(hours=hours_back)
        
        try:
            # Search for DD posts
            subreddit = await self.async_reddit.subreddit("wallstreetbets+stocks+investing")
            
            # Search for DD flair
            async for submission in subreddit.search(
                "flair:DD OR flair:'Due Diligence' OR title:DD",
                time_filter='week',
                limit=50
            ):
                if datetime.fromtimestamp(submission.created_utc) < cutoff_time:
                    continue
                
                if len(submission.selftext) >= min_length:
                    post = RedditPost(
                        id=submission.id,
                        title=submission.title,
                        body=submission.selftext,
                        author=str(submission.author) if submission.author else '[deleted]',
                        score=submission.score,
                        created_utc=datetime.fromtimestamp(submission.created_utc),
                        subreddit=str(submission.subreddit),
                        num_comments=submission.num_comments,
                        awards=submission.total_awards_received,
                        upvote_ratio=submission.upvote_ratio
                    )
                    dd_posts.append(post)
            
            logger.info(f"Found {len(dd_posts)} DD posts")
            
        except Exception as e:
            logger.error(f"Error fetching DD posts: {e}")
        finally:
            await self.async_reddit.close()
        
        return dd_posts
    
    async def get_daily_discussion(
        self,
        subreddit_name: str = "wallstreetbets"
    ) -> List[RedditPost]:
        """
        Get comments from daily discussion thread
        
        Args:
            subreddit_name: Subreddit to check
            
        Returns:
            List of comments from daily thread
        """
        if not self.async_reddit:
            return []
        
        comments = []
        
        try:
            subreddit = await self.async_reddit.subreddit(subreddit_name)
            
            # Find daily discussion thread
            daily_thread = None
            async for submission in subreddit.hot(limit=10):
                if "daily" in submission.title.lower() and "discussion" in submission.title.lower():
                    daily_thread = submission
                    break
            
            if daily_thread:
                # Get top comments
                await daily_thread.comments.replace_more(limit=0)
                
                for comment in daily_thread.comments.list()[:200]:
                    if hasattr(comment, 'body') and comment.score > 5:
                        comment_post = RedditPost(
                            id=comment.id,
                            title=None,
                            body=comment.body,
                            author=str(comment.author) if comment.author else '[deleted]',
                            score=comment.score,
                            created_utc=datetime.fromtimestamp(comment.created_utc),
                            subreddit=subreddit_name,
                            is_comment=True,
                            parent_id=comment.parent_id
                        )
                        comments.append(comment_post)
            
            logger.info(f"Retrieved {len(comments)} daily discussion comments")
            
        except Exception as e:
            logger.error(f"Error fetching daily discussion: {e}")
        finally:
            await self.async_reddit.close()
        
        return comments
    
    def _extract_tickers(self, text: str, exclude_words: Set[str]) -> List[str]:
        """Extract stock tickers from text"""
        # Find potential tickers
        potential_tickers = self.ticker_pattern.findall(text)
        
        # Filter out common words and single letters
        tickers = []
        for ticker in potential_tickers:
            if (len(ticker) > 1 and 
                ticker not in exclude_words and
                not ticker.isdigit()):
                tickers.append(ticker)
        
        # Also check for explicit $ mentions
        dollar_tickers = re.findall(r'\$([A-Z]{1,5})\b', text)
        tickers.extend(dollar_tickers)
        
        return list(set(tickers))
    
    def _get_basic_sentiment(self, text: str) -> str:
        """Get basic sentiment from text"""
        text_lower = text.lower()
        
        bullish_terms = ['calls', 'moon', 'buy', 'long', 'bullish', 'pump', 'squeeze']
        bearish_terms = ['puts', 'dump', 'sell', 'short', 'bearish', 'crash', 'drill']
        
        bullish_count = sum(1 for term in bullish_terms if term in text_lower)
        bearish_count = sum(1 for term in bearish_terms if term in text_lower)
        
        if bullish_count > bearish_count:
            return 'bullish'
        elif bearish_count > bullish_count:
            return 'bearish'
        else:
            return 'neutral'
    
    async def stream_mentions(
        self,
        tickers: List[str],
        callback,
        subreddits: Optional[List[str]] = None
    ):
        """
        Stream real-time mentions of specific tickers
        
        Args:
            tickers: List of tickers to monitor
            callback: Async function to process each mention
            subreddits: Subreddits to monitor
        """
        if not self.async_reddit:
            return
        
        subreddits = subreddits or ['wallstreetbets', 'stocks', 'options']
        subreddit_str = '+'.join(subreddits)
        
        try:
            subreddit = await self.async_reddit.subreddit(subreddit_str)
            
            # Monitor new submissions
            async for submission in subreddit.stream.submissions():
                text = f"{submission.title} {submission.selftext}"
                
                for ticker in tickers:
                    if ticker in text or f"${ticker}" in text:
                        await callback(submission, ticker)
            
        except Exception as e:
            logger.error(f"Error in stream: {e}")
        finally:
            await self.async_reddit.close()