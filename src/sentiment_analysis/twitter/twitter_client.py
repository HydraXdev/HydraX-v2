"""
Twitter/X API Client for FinTwit Data Collection

Handles authentication and data retrieval from Twitter/X API v2
"""

import os
import tweepy
from typing import List, Dict, Optional
from datetime import datetime, timedelta
import logging
from dataclasses import dataclass
import asyncio
import aiohttp

logger = logging.getLogger(__name__)


@dataclass
class Tweet:
    """Tweet data structure"""
    id: str
    text: str
    author_id: str
    author_username: str
    created_at: datetime
    metrics: Dict[str, int]
    entities: Optional[Dict] = None
    context_annotations: Optional[List[Dict]] = None
    
    
class TwitterClient:
    """
    Client for interacting with Twitter/X API v2
    """
    
    def __init__(self, bearer_token: Optional[str] = None):
        """
        Initialize Twitter client
        
        Args:
            bearer_token: Twitter API bearer token
        """
        self.bearer_token = bearer_token or os.getenv("TWITTER_BEARER_TOKEN")
        if not self.bearer_token:
            raise ValueError("Twitter bearer token not provided")
            
        # Initialize client
        self.client = tweepy.Client(bearer_token=self.bearer_token)
        
        # FinTwit influencers and cashtags to track
        self.fintwit_accounts = [
            "jimcramer", "ReformedBroker", "StockCats", "MarketWatch",
            "WSJmarkets", "Benzinga", "SquawkCNBC", "unusual_whales",
            "DeItaone", "FirstSquawk", "LiveSquawk", "Fxhedgers",
            "zerohedge", "SJosephBurns", "OptionsHawk", "AllstarCharts"
        ]
        
        self.trading_cashtags = [
            "$SPY", "$QQQ", "$IWM", "$DIA", "$VIX", "$GLD", "$TLT",
            "$AAPL", "$MSFT", "$AMZN", "$GOOGL", "$TSLA", "$NVDA",
            "$JPM", "$BAC", "$XLF", "$XLE", "$XLK", "$XLV"
        ]
        
    async def get_fintwit_tweets(
        self, 
        symbols: Optional[List[str]] = None,
        hours_back: int = 1,
        max_results: int = 100
    ) -> List[Tweet]:
        """
        Get recent tweets from FinTwit influencers
        
        Args:
            symbols: Specific symbols to filter for
            hours_back: Hours to look back
            max_results: Maximum tweets to retrieve
            
        Returns:
            List of Tweet objects
        """
        try:
            # Build query
            query_parts = []
            
            # Add account filters
            if self.fintwit_accounts:
                account_query = " OR ".join([f"from:{acc}" for acc in self.fintwit_accounts])
                query_parts.append(f"({account_query})")
            
            # Add symbol filters
            if symbols:
                symbol_query = " OR ".join(symbols)
                query_parts.append(f"({symbol_query})")
            else:
                # Use default cashtags
                symbol_query = " OR ".join(self.trading_cashtags)
                query_parts.append(f"({symbol_query})")
            
            # Combine queries
            query = " ".join(query_parts)
            
            # Add filters
            query += " -is:retweet -is:reply lang:en"
            
            # Time range
            start_time = datetime.utcnow() - timedelta(hours=hours_back)
            
            # Search tweets
            tweets = self.client.search_recent_tweets(
                query=query,
                start_time=start_time,
                max_results=max_results,
                tweet_fields=['created_at', 'author_id', 'public_metrics', 
                             'entities', 'context_annotations'],
                user_fields=['username', 'verified', 'public_metrics'],
                expansions=['author_id']
            )
            
            # Process results
            tweet_list = []
            
            if tweets.data:
                # Create user lookup
                users = {user.id: user for user in tweets.includes.get('users', [])}
                
                for tweet in tweets.data:
                    author = users.get(tweet.author_id, None)
                    
                    tweet_obj = Tweet(
                        id=tweet.id,
                        text=tweet.text,
                        author_id=tweet.author_id,
                        author_username=author.username if author else "unknown",
                        created_at=tweet.created_at,
                        metrics=tweet.public_metrics,
                        entities=tweet.entities,
                        context_annotations=tweet.context_annotations
                    )
                    tweet_list.append(tweet_obj)
            
            logger.info(f"Retrieved {len(tweet_list)} FinTwit tweets")
            return tweet_list
            
        except Exception as e:
            logger.error(f"Error fetching FinTwit tweets: {e}")
            return []
    
    async def get_market_sentiment_tweets(
        self,
        keywords: List[str] = None,
        hours_back: int = 1
    ) -> List[Tweet]:
        """
        Get tweets related to market sentiment
        
        Args:
            keywords: Keywords to search for
            hours_back: Hours to look back
            
        Returns:
            List of Tweet objects
        """
        try:
            # Default sentiment keywords
            if not keywords:
                keywords = [
                    "market sentiment", "bullish", "bearish", "risk on", "risk off",
                    "market crash", "market rally", "fed", "inflation", "recession",
                    "stocks", "options", "volatility", "vix spike", "market fear"
                ]
            
            # Build query
            keyword_query = " OR ".join([f'"{kw}"' for kw in keywords])
            query = f"({keyword_query}) -is:retweet lang:en"
            
            # Time range
            start_time = datetime.utcnow() - timedelta(hours=hours_back)
            
            # Search tweets
            tweets = self.client.search_recent_tweets(
                query=query,
                start_time=start_time,
                max_results=100,
                tweet_fields=['created_at', 'author_id', 'public_metrics', 'entities'],
                user_fields=['username', 'verified', 'public_metrics'],
                expansions=['author_id']
            )
            
            # Process results
            tweet_list = []
            
            if tweets.data:
                users = {user.id: user for user in tweets.includes.get('users', [])}
                
                for tweet in tweets.data:
                    # Filter by engagement (likes + retweets)
                    engagement = tweet.public_metrics['like_count'] + \
                                tweet.public_metrics['retweet_count']
                    
                    # Only include tweets with some engagement
                    if engagement > 5:
                        author = users.get(tweet.author_id, None)
                        
                        tweet_obj = Tweet(
                            id=tweet.id,
                            text=tweet.text,
                            author_id=tweet.author_id,
                            author_username=author.username if author else "unknown",
                            created_at=tweet.created_at,
                            metrics=tweet.public_metrics,
                            entities=tweet.entities
                        )
                        tweet_list.append(tweet_obj)
            
            logger.info(f"Retrieved {len(tweet_list)} market sentiment tweets")
            return tweet_list
            
        except Exception as e:
            logger.error(f"Error fetching market sentiment tweets: {e}")
            return []
    
    async def stream_fintwit(self, callback):
        """
        Stream real-time FinTwit tweets
        
        Args:
            callback: Async function to process each tweet
        """
        try:
            # Create filter rules
            rules = []
            
            # Add account rules
            for account in self.fintwit_accounts[:25]:  # API limit
                rules.append(tweepy.StreamRule(f"from:{account}"))
            
            # Add cashtag rules
            cashtag_rule = " OR ".join(self.trading_cashtags[:10])
            rules.append(tweepy.StreamRule(cashtag_rule))
            
            # Create stream
            stream = tweepy.StreamingClient(self.bearer_token)
            
            # Add rules
            stream.add_rules(rules)
            
            # Start streaming
            logger.info("Starting FinTwit stream...")
            stream.filter(
                tweet_fields=['created_at', 'author_id', 'public_metrics'],
                user_fields=['username'],
                expansions=['author_id']
            )
            
        except Exception as e:
            logger.error(f"Error in FinTwit stream: {e}")
            
    def get_user_timeline(
        self, 
        username: str, 
        max_results: int = 20
    ) -> List[Tweet]:
        """
        Get recent tweets from a specific user
        
        Args:
            username: Twitter username
            max_results: Maximum tweets to retrieve
            
        Returns:
            List of Tweet objects
        """
        try:
            # Get user ID
            user = self.client.get_user(username=username)
            if not user.data:
                return []
            
            user_id = user.data.id
            
            # Get tweets
            tweets = self.client.get_users_tweets(
                id=user_id,
                max_results=max_results,
                tweet_fields=['created_at', 'public_metrics', 'entities'],
                exclude=['retweets', 'replies']
            )
            
            # Process results
            tweet_list = []
            
            if tweets.data:
                for tweet in tweets.data:
                    tweet_obj = Tweet(
                        id=tweet.id,
                        text=tweet.text,
                        author_id=user_id,
                        author_username=username,
                        created_at=tweet.created_at,
                        metrics=tweet.public_metrics,
                        entities=tweet.entities
                    )
                    tweet_list.append(tweet_obj)
            
            return tweet_list
            
        except Exception as e:
            logger.error(f"Error fetching user timeline for {username}: {e}")
            return []