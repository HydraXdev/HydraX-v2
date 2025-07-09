"""
FinTwit Sentiment Analyzer using Modern NLP

Analyzes Twitter/X posts from financial Twitter influencers using
transformer models for accurate sentiment detection.
"""

import re
from typing import List, Dict, Tuple, Optional
from datetime import datetime
import numpy as np
from dataclasses import dataclass
import logging
from transformers import pipeline, AutoTokenizer, AutoModelForSequenceClassification
import torch
from collections import defaultdict
import asyncio

from .twitter_client import TwitterClient, Tweet

logger = logging.getLogger(__name__)


@dataclass
class FinTwitSentiment:
    """FinTwit sentiment analysis result"""
    tweet_id: str
    text: str
    author: str
    created_at: datetime
    sentiment: str  # bullish, bearish, neutral
    confidence: float
    symbols: List[str]
    entities: Dict[str, List[str]]
    engagement_score: float
    
    
class FinTwitAnalyzer:
    """
    Analyzes FinTwit sentiment using state-of-the-art NLP models
    """
    
    def __init__(self, twitter_client: Optional[TwitterClient] = None):
        """
        Initialize FinTwit analyzer
        
        Args:
            twitter_client: Twitter API client instance
        """
        self.twitter_client = twitter_client or TwitterClient()
        
        # Initialize sentiment models
        self._init_models()
        
        # Regex patterns
        self.symbol_pattern = re.compile(r'\$[A-Z]{1,5}\b')
        self.price_pattern = re.compile(r'\$?\d+\.?\d*')
        
        # Sentiment keywords
        self.bullish_keywords = {
            'bullish', 'long', 'buy', 'calls', 'moon', 'rocket', 'breakout',
            'accumulate', 'oversold', 'bounce', 'support', 'uptrend', 'rally',
            'squeeze', 'gamma', 'printing', 'tendies', 'gains', 'ath', 'rip'
        }
        
        self.bearish_keywords = {
            'bearish', 'short', 'sell', 'puts', 'crash', 'dump', 'breakdown',
            'overbought', 'resistance', 'downtrend', 'correction', 'collapse',
            'bubble', 'overvalued', 'weak', 'risk', 'warning', 'danger'
        }
        
    def _init_models(self):
        """Initialize NLP models"""
        try:
            # Financial sentiment model (fine-tuned on financial texts)
            model_name = "ProsusAI/finbert"
            self.tokenizer = AutoTokenizer.from_pretrained(model_name)
            self.model = AutoModelForSequenceClassification.from_pretrained(model_name)
            
            # Create pipeline
            self.sentiment_pipeline = pipeline(
                "sentiment-analysis",
                model=self.model,
                tokenizer=self.tokenizer,
                device=0 if torch.cuda.is_available() else -1
            )
            
            # Backup: General sentiment model
            self.general_sentiment = pipeline(
                "sentiment-analysis",
                model="cardiffnlp/twitter-roberta-base-sentiment-latest",
                device=0 if torch.cuda.is_available() else -1
            )
            
            logger.info("NLP models initialized successfully")
            
        except Exception as e:
            logger.error(f"Error initializing models: {e}")
            # Fallback to basic sentiment
            self.sentiment_pipeline = None
            self.general_sentiment = None
    
    async def analyze_fintwit_sentiment(
        self,
        symbols: Optional[List[str]] = None,
        hours_back: int = 1
    ) -> Dict[str, Dict]:
        """
        Analyze FinTwit sentiment for given symbols
        
        Args:
            symbols: List of stock symbols to analyze
            hours_back: Hours to look back
            
        Returns:
            Dictionary with sentiment analysis results
        """
        try:
            # Get tweets
            tweets = await self.twitter_client.get_fintwit_tweets(
                symbols=symbols,
                hours_back=hours_back
            )
            
            # Analyze sentiment
            results = {
                'timestamp': datetime.utcnow().isoformat(),
                'symbols': {},
                'overall_sentiment': None,
                'tweet_count': len(tweets),
                'sentiment_distribution': {'bullish': 0, 'bearish': 0, 'neutral': 0},
                'top_tweets': []
            }
            
            # Process each tweet
            sentiments = []
            symbol_sentiments = defaultdict(list)
            
            for tweet in tweets:
                sentiment_result = self._analyze_tweet(tweet)
                sentiments.append(sentiment_result)
                
                # Track sentiment by symbol
                for symbol in sentiment_result.symbols:
                    symbol_sentiments[symbol].append(sentiment_result)
                
                # Track distribution
                results['sentiment_distribution'][sentiment_result.sentiment] += 1
            
            # Calculate overall sentiment
            if sentiments:
                bullish_score = sum(1 for s in sentiments if s.sentiment == 'bullish')
                bearish_score = sum(1 for s in sentiments if s.sentiment == 'bearish')
                
                total = len(sentiments)
                bullish_pct = bullish_score / total
                bearish_pct = bearish_score / total
                
                if bullish_pct > 0.6:
                    results['overall_sentiment'] = 'bullish'
                elif bearish_pct > 0.6:
                    results['overall_sentiment'] = 'bearish'
                else:
                    results['overall_sentiment'] = 'neutral'
                
                results['sentiment_score'] = (bullish_pct - bearish_pct) * 100
                
                # Top tweets by engagement
                top_tweets = sorted(
                    sentiments, 
                    key=lambda x: x.engagement_score, 
                    reverse=True
                )[:10]
                
                results['top_tweets'] = [
                    {
                        'text': t.text,
                        'author': t.author,
                        'sentiment': t.sentiment,
                        'confidence': t.confidence,
                        'engagement': t.engagement_score
                    }
                    for t in top_tweets
                ]
            
            # Analyze sentiment by symbol
            for symbol, symbol_tweets in symbol_sentiments.items():
                bullish = sum(1 for t in symbol_tweets if t.sentiment == 'bullish')
                bearish = sum(1 for t in symbol_tweets if t.sentiment == 'bearish')
                total = len(symbol_tweets)
                
                results['symbols'][symbol] = {
                    'tweet_count': total,
                    'bullish': bullish,
                    'bearish': bearish,
                    'sentiment_score': ((bullish - bearish) / total * 100) if total > 0 else 0,
                    'top_influencers': list(set(t.author for t in symbol_tweets))[:5]
                }
            
            return results
            
        except Exception as e:
            logger.error(f"Error analyzing FinTwit sentiment: {e}")
            return {}
    
    def _analyze_tweet(self, tweet: Tweet) -> FinTwitSentiment:
        """
        Analyze individual tweet sentiment
        
        Args:
            tweet: Tweet object
            
        Returns:
            FinTwitSentiment object
        """
        try:
            # Extract symbols
            symbols = self._extract_symbols(tweet.text)
            
            # Clean text for analysis
            clean_text = self._clean_text(tweet.text)
            
            # Get sentiment from model
            if self.sentiment_pipeline:
                sentiment_result = self._get_model_sentiment(clean_text)
            else:
                sentiment_result = self._get_keyword_sentiment(clean_text)
            
            # Calculate engagement score
            engagement_score = self._calculate_engagement_score(tweet.metrics)
            
            # Extract entities
            entities = self._extract_entities(tweet)
            
            return FinTwitSentiment(
                tweet_id=tweet.id,
                text=tweet.text,
                author=tweet.author_username,
                created_at=tweet.created_at,
                sentiment=sentiment_result[0],
                confidence=sentiment_result[1],
                symbols=symbols,
                entities=entities,
                engagement_score=engagement_score
            )
            
        except Exception as e:
            logger.error(f"Error analyzing tweet: {e}")
            return FinTwitSentiment(
                tweet_id=tweet.id,
                text=tweet.text,
                author=tweet.author_username,
                created_at=tweet.created_at,
                sentiment='neutral',
                confidence=0.5,
                symbols=[],
                entities={},
                engagement_score=0.0
            )
    
    def _get_model_sentiment(self, text: str) -> Tuple[str, float]:
        """
        Get sentiment using transformer model
        
        Args:
            text: Cleaned tweet text
            
        Returns:
            Tuple of (sentiment, confidence)
        """
        try:
            # Get prediction
            result = self.sentiment_pipeline(text[:512])[0]  # Truncate for model
            
            # Map FinBERT labels to our labels
            label_map = {
                'positive': 'bullish',
                'negative': 'bearish',
                'neutral': 'neutral'
            }
            
            sentiment = label_map.get(result['label'].lower(), 'neutral')
            confidence = result['score']
            
            # Double-check with keyword analysis for high confidence
            keyword_sentiment = self._get_keyword_sentiment(text)[0]
            if confidence > 0.8 and keyword_sentiment != 'neutral' and keyword_sentiment != sentiment:
                # Reduce confidence if there's disagreement
                confidence *= 0.7
            
            return sentiment, confidence
            
        except Exception as e:
            logger.error(f"Error in model sentiment: {e}")
            return self._get_keyword_sentiment(text)
    
    def _get_keyword_sentiment(self, text: str) -> Tuple[str, float]:
        """
        Get sentiment using keyword analysis
        
        Args:
            text: Cleaned tweet text
            
        Returns:
            Tuple of (sentiment, confidence)
        """
        text_lower = text.lower()
        
        bullish_count = sum(1 for word in self.bullish_keywords if word in text_lower)
        bearish_count = sum(1 for word in self.bearish_keywords if word in text_lower)
        
        if bullish_count > bearish_count:
            confidence = min(0.9, 0.5 + (bullish_count * 0.1))
            return 'bullish', confidence
        elif bearish_count > bullish_count:
            confidence = min(0.9, 0.5 + (bearish_count * 0.1))
            return 'bearish', confidence
        else:
            return 'neutral', 0.5
    
    def _extract_symbols(self, text: str) -> List[str]:
        """Extract stock symbols from text"""
        symbols = self.symbol_pattern.findall(text)
        # Remove $ and deduplicate
        return list(set(s.replace('$', '') for s in symbols))
    
    def _clean_text(self, text: str) -> str:
        """Clean tweet text for analysis"""
        # Remove URLs
        text = re.sub(r'http\S+|www.\S+', '', text)
        # Remove mentions
        text = re.sub(r'@\w+', '', text)
        # Remove excessive whitespace
        text = ' '.join(text.split())
        return text
    
    def _calculate_engagement_score(self, metrics: Dict[str, int]) -> float:
        """Calculate engagement score from tweet metrics"""
        likes = metrics.get('like_count', 0)
        retweets = metrics.get('retweet_count', 0)
        replies = metrics.get('reply_count', 0)
        
        # Weighted engagement score
        score = (likes * 1.0) + (retweets * 2.0) + (replies * 0.5)
        
        # Normalize to 0-100 scale (assuming 1000 is high engagement)
        return min(100, score / 10)
    
    def _extract_entities(self, tweet: Tweet) -> Dict[str, List[str]]:
        """Extract entities from tweet"""
        entities = {
            'symbols': [],
            'prices': [],
            'urls': []
        }
        
        if tweet.entities:
            # Extract cashtags
            if 'cashtags' in tweet.entities:
                entities['symbols'] = [tag['tag'] for tag in tweet.entities['cashtags']]
            
            # Extract URLs
            if 'urls' in tweet.entities:
                entities['urls'] = [url['expanded_url'] for url in tweet.entities['urls']]
        
        # Extract prices
        entities['prices'] = self.price_pattern.findall(tweet.text)
        
        return entities
    
    async def get_influencer_consensus(
        self,
        symbol: str,
        top_n: int = 10
    ) -> Dict[str, any]:
        """
        Get sentiment consensus from top FinTwit influencers
        
        Args:
            symbol: Stock symbol to analyze
            top_n: Number of top influencers to check
            
        Returns:
            Consensus sentiment data
        """
        try:
            consensus = {
                'symbol': symbol,
                'influencer_sentiments': [],
                'consensus': None,
                'confidence': 0.0
            }
            
            # Get tweets from top influencers
            for influencer in self.twitter_client.fintwit_accounts[:top_n]:
                tweets = self.twitter_client.get_user_timeline(influencer)
                
                # Find tweets mentioning the symbol
                symbol_tweets = [
                    t for t in tweets 
                    if f'${symbol}' in t.text.upper()
                ]
                
                if symbol_tweets:
                    # Analyze most recent tweet
                    sentiment_result = self._analyze_tweet(symbol_tweets[0])
                    
                    consensus['influencer_sentiments'].append({
                        'influencer': influencer,
                        'sentiment': sentiment_result.sentiment,
                        'confidence': sentiment_result.confidence,
                        'text': sentiment_result.text[:200] + '...'
                    })
            
            # Calculate consensus
            if consensus['influencer_sentiments']:
                sentiments = [s['sentiment'] for s in consensus['influencer_sentiments']]
                bullish = sentiments.count('bullish')
                bearish = sentiments.count('bearish')
                
                if bullish > bearish * 1.5:
                    consensus['consensus'] = 'bullish'
                    consensus['confidence'] = bullish / len(sentiments)
                elif bearish > bullish * 1.5:
                    consensus['consensus'] = 'bearish'
                    consensus['confidence'] = bearish / len(sentiments)
                else:
                    consensus['consensus'] = 'neutral'
                    consensus['confidence'] = 0.5
            
            return consensus
            
        except Exception as e:
            logger.error(f"Error getting influencer consensus: {e}")
            return {}