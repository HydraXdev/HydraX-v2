"""
WSB Sentiment Scanner using Advanced NLP

Analyzes sentiment from WallStreetBets and other financial subreddits
using transformer models and WSB-specific language understanding.
"""

import re
from typing import List, Dict, Tuple, Optional, Set
from datetime import datetime, timedelta
import numpy as np
from dataclasses import dataclass
import logging
from transformers import pipeline, AutoTokenizer, AutoModelForSequenceClassification
import torch
from collections import defaultdict, Counter
import asyncio
from textblob import TextBlob
import yfinance as yf

from .reddit_client import RedditClient, RedditPost

logger = logging.getLogger(__name__)


@dataclass
class WSBSentiment:
    """WSB sentiment analysis result"""
    post_id: str
    text: str
    author: str
    score: int
    created_at: datetime
    sentiment: str  # bullish, bearish, neutral
    confidence: float
    tickers: List[str]
    wsb_indicators: Dict[str, any]
    position_type: Optional[str] = None  # calls, puts, shares
    price_target: Optional[float] = None
    

class WSBSentimentScanner:
    """
    Scans and analyzes WSB sentiment with deep understanding of WSB culture
    """
    
    def __init__(self, reddit_client: Optional[RedditClient] = None):
        """
        Initialize WSB sentiment scanner
        
        Args:
            reddit_client: Reddit API client instance
        """
        self.reddit_client = reddit_client or RedditClient()
        
        # Initialize models
        self._init_models()
        
        # WSB-specific patterns
        self.position_patterns = {
            'calls': re.compile(r'(\d+)\s*(?:x\s*)?([A-Z]{1,5})\s*(\d+)c', re.IGNORECASE),
            'puts': re.compile(r'(\d+)\s*(?:x\s*)?([A-Z]{1,5})\s*(\d+)p', re.IGNORECASE),
            'shares': re.compile(r'(\d+)\s*(?:shares?|stocks?)\s*(?:of\s*)?([A-Z]{1,5})', re.IGNORECASE)
        }
        
        # Price target patterns
        self.price_patterns = [
            re.compile(r'\$(\d+\.?\d*)\s*(?:PT|price target|target)', re.IGNORECASE),
            re.compile(r'(?:PT|target)\s*\$(\d+\.?\d*)', re.IGNORECASE),
            re.compile(r'(?:going to|will hit|reaching)\s*\$(\d+\.?\d*)', re.IGNORECASE)
        ]
        
        # WSB sentiment indicators
        self.bullish_indicators = {
            'rocket_emojis': ['🚀', '🌙', '🌕', '💎', '🙌'],
            'phrases': [
                'to the moon', 'moon shot', 'diamond hands', 'buy the dip',
                'btfd', 'yolo', 'all in', 'cant go tits up', 'free money',
                'money printer', 'brrr', 'stonks only go up', 'bears r fuk',
                'short squeeze', 'gamma squeeze', 'infinity squeeze'
            ],
            'words': [
                'moon', 'squeeze', 'bullish', 'calls', 'tendies', 'gains',
                'print', 'breakout', 'mooning', 'pumping', 'ripping'
            ]
        }
        
        self.bearish_indicators = {
            'emojis': ['🐻', '📉', '💩', '🔥', '☠️'],
            'phrases': [
                'going to zero', 'bubble', 'puts printing', 'drill team',
                'rug pull', 'paper hands', 'bag holder', 'guh', 'loss porn',
                'theta gang', 'bulls r fuk', 'top is in', 'dead cat bounce'
            ],
            'words': [
                'puts', 'crash', 'dump', 'drill', 'tank', 'bearish',
                'overvalued', 'short', 'collapse', 'plunge', 'selloff'
            ]
        }
        
        # Credibility indicators
        self.credibility_factors = {
            'dd_indicators': ['dd', 'due diligence', 'research', 'analysis', 'data'],
            'position_proof': ['proof', 'position', 'screenshot', 'gains', 'loss'],
            'technical_terms': ['rsi', 'macd', 'ema', 'support', 'resistance', 'volume']
        }
        
    def _init_models(self):
        """Initialize NLP models"""
        try:
            # Use a model fine-tuned on financial/social media text
            model_name = "cardiffnlp/twitter-roberta-base-sentiment-latest"
            self.sentiment_model = pipeline(
                "sentiment-analysis",
                model=model_name,
                device=0 if torch.cuda.is_available() else -1
            )
            
            # Backup financial sentiment model
            self.financial_sentiment = pipeline(
                "sentiment-analysis",
                model="ProsusAI/finbert",
                device=0 if torch.cuda.is_available() else -1
            )
            
            logger.info("WSB sentiment models initialized")
            
        except Exception as e:
            logger.error(f"Error initializing models: {e}")
            self.sentiment_model = None
            self.financial_sentiment = None
    
    async def analyze_wsb_sentiment(
        self,
        time_filter: str = 'day',
        min_score: int = 10
    ) -> Dict[str, any]:
        """
        Analyze overall WSB sentiment
        
        Args:
            time_filter: Time period to analyze
            min_score: Minimum post score
            
        Returns:
            WSB sentiment analysis results
        """
        try:
            # Get WSB posts
            posts = await self.reddit_client.get_wsb_posts(
                time_filter=time_filter,
                limit=200,
                min_score=min_score
            )
            
            # Get trending tickers
            trending = await self.reddit_client.get_trending_tickers(
                subreddits=['wallstreetbets'],
                hours_back=24
            )
            
            # Analyze posts
            sentiments = []
            ticker_sentiments = defaultdict(list)
            
            for post in posts:
                sentiment = self._analyze_post(post)
                sentiments.append(sentiment)
                
                # Group by ticker
                for ticker in sentiment.tickers:
                    ticker_sentiments[ticker].append(sentiment)
            
            # Calculate metrics
            results = {
                'timestamp': datetime.utcnow().isoformat(),
                'post_count': len(posts),
                'overall_sentiment': self._calculate_overall_sentiment(sentiments),
                'sentiment_distribution': self._get_distribution(sentiments),
                'trending_tickers': self._format_trending_tickers(trending, ticker_sentiments),
                'wsb_mood': self._calculate_wsb_mood(sentiments),
                'top_posts': self._get_top_posts(sentiments),
                'position_breakdown': self._analyze_positions(sentiments),
                'unusual_activity': self._detect_unusual_activity(ticker_sentiments)
            }
            
            return results
            
        except Exception as e:
            logger.error(f"Error analyzing WSB sentiment: {e}")
            return {}
    
    async def analyze_ticker_sentiment(
        self,
        ticker: str,
        hours_back: int = 48
    ) -> Dict[str, any]:
        """
        Analyze sentiment for specific ticker on WSB
        
        Args:
            ticker: Stock ticker symbol
            hours_back: Hours to look back
            
        Returns:
            Ticker-specific sentiment analysis
        """
        try:
            # Search for ticker mentions
            posts = []
            
            # Get posts mentioning ticker
            subreddits = ['wallstreetbets', 'stocks', 'options']
            for subreddit in subreddits:
                sub_posts = await self._search_ticker_posts(ticker, subreddit, hours_back)
                posts.extend(sub_posts)
            
            if not posts:
                return {
                    'ticker': ticker,
                    'sentiment': 'neutral',
                    'message': 'No recent mentions found'
                }
            
            # Analyze sentiment
            sentiments = []
            for post in posts:
                sentiment = self._analyze_post(post)
                if ticker in sentiment.tickers:
                    sentiments.append(sentiment)
            
            # Get price data for context
            price_data = self._get_price_context(ticker)
            
            # Calculate metrics
            results = {
                'ticker': ticker,
                'mention_count': len(sentiments),
                'sentiment': self._calculate_ticker_sentiment(sentiments),
                'wsb_score': self._calculate_wsb_score(sentiments),
                'position_bias': self._analyze_position_bias(sentiments),
                'average_confidence': np.mean([s.confidence for s in sentiments]) if sentiments else 0,
                'price_context': price_data,
                'sentiment_timeline': self._create_sentiment_timeline(sentiments),
                'notable_posts': self._get_notable_posts(sentiments, limit=5),
                'crowd_targets': self._extract_crowd_targets(sentiments)
            }
            
            return results
            
        except Exception as e:
            logger.error(f"Error analyzing ticker sentiment: {e}")
            return {'ticker': ticker, 'error': str(e)}
    
    def _analyze_post(self, post: RedditPost) -> WSBSentiment:
        """
        Analyze individual Reddit post
        
        Args:
            post: RedditPost object
            
        Returns:
            WSBSentiment object
        """
        try:
            # Combine title and body
            text = f"{post.title or ''} {post.body}"
            
            # Extract tickers
            tickers = self._extract_tickers_advanced(text)
            
            # Get sentiment
            sentiment, confidence = self._get_wsb_sentiment(text)
            
            # Extract WSB indicators
            wsb_indicators = self._extract_wsb_indicators(text)
            
            # Extract positions
            position_type, price_target = self._extract_position_info(text)
            
            # Adjust sentiment based on WSB indicators
            if wsb_indicators['rocket_count'] > 2 or wsb_indicators['diamond_hands']:
                if sentiment == 'neutral':
                    sentiment = 'bullish'
                    confidence *= 1.2
            
            return WSBSentiment(
                post_id=post.id,
                text=text[:500],  # Truncate for storage
                author=post.author,
                score=post.score,
                created_at=post.created_at,
                sentiment=sentiment,
                confidence=min(confidence, 0.95),
                tickers=tickers,
                wsb_indicators=wsb_indicators,
                position_type=position_type,
                price_target=price_target
            )
            
        except Exception as e:
            logger.error(f"Error analyzing post: {e}")
            return WSBSentiment(
                post_id=post.id,
                text=str(post.title or '')[:500],
                author=post.author,
                score=post.score,
                created_at=post.created_at,
                sentiment='neutral',
                confidence=0.5,
                tickers=[],
                wsb_indicators={}
            )
    
    def _get_wsb_sentiment(self, text: str) -> Tuple[str, float]:
        """Get sentiment using models and WSB understanding"""
        # Clean text
        clean_text = self._clean_wsb_text(text)
        
        # Model sentiment
        if self.sentiment_model:
            try:
                result = self.sentiment_model(clean_text[:512])[0]
                
                # Map labels
                label_map = {
                    'positive': 'bullish',
                    'negative': 'bearish',
                    'neutral': 'neutral'
                }
                
                model_sentiment = label_map.get(result['label'].lower(), 'neutral')
                model_confidence = result['score']
                
            except Exception as e:
                logger.error(f"Model error: {e}")
                model_sentiment = 'neutral'
                model_confidence = 0.5
        else:
            model_sentiment = 'neutral'
            model_confidence = 0.5
        
        # WSB keyword sentiment
        wsb_sentiment, wsb_confidence = self._get_wsb_keyword_sentiment(text)
        
        # Combine sentiments with weights
        if model_confidence > 0.8 and wsb_confidence > 0.7:
            # High confidence in both
            if model_sentiment == wsb_sentiment:
                return model_sentiment, (model_confidence + wsb_confidence) / 2
            else:
                # Disagree - WSB keywords get more weight
                return wsb_sentiment, wsb_confidence * 0.8
        elif wsb_confidence > 0.7:
            # Trust WSB keywords more
            return wsb_sentiment, wsb_confidence
        else:
            # Default to model
            return model_sentiment, model_confidence
    
    def _get_wsb_keyword_sentiment(self, text: str) -> Tuple[str, float]:
        """Get sentiment from WSB-specific keywords"""
        text_lower = text.lower()
        
        # Count indicators
        bullish_score = 0
        bearish_score = 0
        
        # Check phrases (weighted more)
        for phrase in self.bullish_indicators['phrases']:
            if phrase in text_lower:
                bullish_score += 2
        
        for phrase in self.bearish_indicators['phrases']:
            if phrase in text_lower:
                bearish_score += 2
        
        # Check words
        for word in self.bullish_indicators['words']:
            if word in text_lower:
                bullish_score += 1
        
        for word in self.bearish_indicators['words']:
            if word in text_lower:
                bearish_score += 1
        
        # Check emojis
        for emoji in self.bullish_indicators['rocket_emojis']:
            bullish_score += text.count(emoji) * 0.5
        
        for emoji in self.bearish_indicators['emojis']:
            bearish_score += text.count(emoji) * 0.5
        
        # Determine sentiment
        if bullish_score > bearish_score * 1.5:
            confidence = min(0.9, 0.5 + (bullish_score * 0.05))
            return 'bullish', confidence
        elif bearish_score > bullish_score * 1.5:
            confidence = min(0.9, 0.5 + (bearish_score * 0.05))
            return 'bearish', confidence
        else:
            return 'neutral', 0.5
    
    def _extract_tickers_advanced(self, text: str) -> List[str]:
        """Extract tickers with WSB context understanding"""
        tickers = set()
        
        # Standard ticker extraction
        standard_tickers = self.reddit_client._extract_tickers(
            text, 
            {'USA', 'CEO', 'FDA', 'IPO', 'WSB', 'DD', 'YOLO', 'SEC'}
        )
        tickers.update(standard_tickers)
        
        # Extract from option mentions
        for pattern in self.position_patterns.values():
            matches = pattern.findall(text)
            for match in matches:
                if len(match) >= 2:
                    ticker = match[1] if isinstance(match, tuple) else match
                    if 2 <= len(ticker) <= 5:
                        tickers.add(ticker.upper())
        
        # Popular WSB tickers that might be mentioned without $
        wsb_favorites = {
            'GME', 'AMC', 'BB', 'NOK', 'PLTR', 'TSLA', 'SPY', 'QQQ',
            'AAPL', 'AMD', 'NVDA', 'MSFT', 'META', 'AMZN', 'GOOGL'
        }
        
        text_upper = text.upper()
        for ticker in wsb_favorites:
            if f" {ticker} " in text_upper or f"${ticker}" in text_upper:
                tickers.add(ticker)
        
        return list(tickers)
    
    def _extract_wsb_indicators(self, text: str) -> Dict[str, any]:
        """Extract WSB-specific indicators"""
        indicators = {
            'rocket_count': sum(text.count(emoji) for emoji in self.bullish_indicators['rocket_emojis']),
            'diamond_hands': any(phrase in text.lower() for phrase in ['diamond hands', '💎🙌', '💎👐']),
            'yolo_mention': 'yolo' in text.lower(),
            'dd_quality': self._assess_dd_quality(text),
            'gain_loss_porn': 'gain porn' in text.lower() or 'loss porn' in text.lower(),
            'emoji_density': len([c for c in text if ord(c) > 127]) / max(len(text), 1),
            'caps_ratio': sum(1 for c in text if c.isupper()) / max(len(text), 1),
            'exclamation_count': text.count('!'),
            'question_count': text.count('?')
        }
        
        return indicators
    
    def _extract_position_info(self, text: str) -> Tuple[Optional[str], Optional[float]]:
        """Extract position type and price target"""
        position_type = None
        price_target = None
        
        # Check for position types
        for pos_type, pattern in self.position_patterns.items():
            if pattern.search(text):
                position_type = pos_type
                break
        
        # Extract price targets
        for pattern in self.price_patterns:
            match = pattern.search(text)
            if match:
                try:
                    price_target = float(match.group(1))
                    break
                except:
                    pass
        
        return position_type, price_target
    
    def _assess_dd_quality(self, text: str) -> float:
        """Assess quality of due diligence"""
        score = 0.0
        text_lower = text.lower()
        
        # Length bonus
        if len(text) > 1000:
            score += 0.2
        elif len(text) > 500:
            score += 0.1
        
        # Check for DD indicators
        for indicator in self.credibility_factors['dd_indicators']:
            if indicator in text_lower:
                score += 0.1
        
        # Technical analysis mentions
        for term in self.credibility_factors['technical_terms']:
            if term in text_lower:
                score += 0.05
        
        # Data/numbers present
        if re.search(r'\d+\.?\d*%', text):  # Percentages
            score += 0.1
        if re.search(r'\$\d+\.?\d*[BMK]?', text):  # Dollar amounts
            score += 0.1
        
        return min(score, 1.0)
    
    def _clean_wsb_text(self, text: str) -> str:
        """Clean WSB text for analysis"""
        # Remove excessive emojis for model
        text = re.sub(r'[\U0001F600-\U0001F64F\U0001F300-\U0001F5FF\U0001F680-\U0001F6FF\U0001F1E0-\U0001F1FF]+', ' ', text)
        
        # Replace WSB slang with standard terms
        replacements = {
            'tendies': 'profits',
            'guh': 'loss',
            'stonks': 'stocks',
            'hodl': 'hold',
            'dd': 'analysis',
            'fd': 'options',
            'brrr': 'printing money'
        }
        
        text_lower = text.lower()
        for slang, standard in replacements.items():
            text_lower = text_lower.replace(slang, standard)
        
        # Remove excessive punctuation
        text = re.sub(r'[!?]{2,}', '!', text)
        
        return text
    
    def _calculate_overall_sentiment(self, sentiments: List[WSBSentiment]) -> Dict[str, any]:
        """Calculate overall WSB sentiment"""
        if not sentiments:
            return {'sentiment': 'neutral', 'score': 0, 'confidence': 0}
        
        # Weight by post score and confidence
        weighted_sum = 0
        total_weight = 0
        
        for sent in sentiments:
            weight = np.log1p(sent.score) * sent.confidence
            value = 1 if sent.sentiment == 'bullish' else -1 if sent.sentiment == 'bearish' else 0
            weighted_sum += value * weight
            total_weight += weight
        
        if total_weight > 0:
            score = weighted_sum / total_weight
        else:
            score = 0
        
        # Determine sentiment
        if score > 0.2:
            sentiment = 'bullish'
        elif score < -0.2:
            sentiment = 'bearish'
        else:
            sentiment = 'neutral'
        
        return {
            'sentiment': sentiment,
            'score': score * 100,
            'confidence': np.mean([s.confidence for s in sentiments])
        }
    
    def _get_distribution(self, sentiments: List[WSBSentiment]) -> Dict[str, float]:
        """Get sentiment distribution"""
        if not sentiments:
            return {'bullish': 0, 'bearish': 0, 'neutral': 0}
        
        total = len(sentiments)
        return {
            'bullish': sum(1 for s in sentiments if s.sentiment == 'bullish') / total * 100,
            'bearish': sum(1 for s in sentiments if s.sentiment == 'bearish') / total * 100,
            'neutral': sum(1 for s in sentiments if s.sentiment == 'neutral') / total * 100
        }
    
    def _calculate_wsb_mood(self, sentiments: List[WSBSentiment]) -> str:
        """Determine overall WSB mood"""
        if not sentiments:
            return 'quiet'
        
        # Calculate metrics
        avg_rockets = np.mean([s.wsb_indicators.get('rocket_count', 0) for s in sentiments])
        yolo_ratio = sum(1 for s in sentiments if s.wsb_indicators.get('yolo_mention', False)) / len(sentiments)
        diamond_ratio = sum(1 for s in sentiments if s.wsb_indicators.get('diamond_hands', False)) / len(sentiments)
        
        # Determine mood
        if avg_rockets > 3 and yolo_ratio > 0.3:
            return 'euphoric'
        elif diamond_ratio > 0.2:
            return 'determined'
        elif any(s.sentiment == 'bearish' for s in sentiments[:10]):  # Top posts bearish
            return 'fearful'
        elif yolo_ratio > 0.2:
            return 'gambling'
        else:
            return 'normal'
    
    def _format_trending_tickers(
        self, 
        trending: Dict[str, Dict],
        ticker_sentiments: Dict[str, List[WSBSentiment]]
    ) -> List[Dict]:
        """Format trending tickers with sentiment"""
        formatted = []
        
        for ticker, data in list(trending.items())[:20]:  # Top 20
            sentiments = ticker_sentiments.get(ticker, [])
            
            if sentiments:
                sentiment_dist = self._get_distribution(sentiments)
                avg_confidence = np.mean([s.confidence for s in sentiments])
                
                # Determine dominant sentiment
                if sentiment_dist['bullish'] > 60:
                    dominant = 'bullish'
                elif sentiment_dist['bearish'] > 60:
                    dominant = 'bearish'
                else:
                    dominant = 'mixed'
            else:
                sentiment_dist = {'bullish': 0, 'bearish': 0, 'neutral': 100}
                dominant = 'neutral'
                avg_confidence = 0
            
            formatted.append({
                'ticker': ticker,
                'mentions': data['mentions'],
                'total_score': data['score'],
                'sentiment': dominant,
                'sentiment_breakdown': sentiment_dist,
                'confidence': avg_confidence,
                'top_subreddits': list(set(p['subreddit'] for p in data['posts'][:5]))
            })
        
        return formatted
    
    def _get_top_posts(self, sentiments: List[WSBSentiment], limit: int = 10) -> List[Dict]:
        """Get top posts by engagement"""
        sorted_sentiments = sorted(sentiments, key=lambda x: x.score, reverse=True)
        
        return [
            {
                'text': s.text[:200] + '...',
                'author': s.author,
                'score': s.score,
                'sentiment': s.sentiment,
                'tickers': s.tickers,
                'rockets': s.wsb_indicators.get('rocket_count', 0),
                'position': s.position_type,
                'target': s.price_target
            }
            for s in sorted_sentiments[:limit]
        ]
    
    def _analyze_positions(self, sentiments: List[WSBSentiment]) -> Dict[str, int]:
        """Analyze position types mentioned"""
        positions = {'calls': 0, 'puts': 0, 'shares': 0, 'unknown': 0}
        
        for sent in sentiments:
            if sent.position_type:
                positions[sent.position_type] += 1
            else:
                positions['unknown'] += 1
        
        return positions
    
    def _detect_unusual_activity(
        self, 
        ticker_sentiments: Dict[str, List[WSBSentiment]]
    ) -> List[Dict]:
        """Detect unusual ticker activity"""
        unusual = []
        
        for ticker, sentiments in ticker_sentiments.items():
            if len(sentiments) < 5:
                continue
            
            # Calculate metrics
            mention_spike = len(sentiments)
            avg_confidence = np.mean([s.confidence for s in sentiments])
            bullish_ratio = sum(1 for s in sentiments if s.sentiment == 'bullish') / len(sentiments)
            
            # High mention count with high bullish ratio
            if mention_spike > 20 and bullish_ratio > 0.8:
                unusual.append({
                    'ticker': ticker,
                    'type': 'bullish_surge',
                    'mentions': mention_spike,
                    'bullish_ratio': bullish_ratio,
                    'confidence': avg_confidence
                })
            
            # Sudden bearish sentiment
            elif mention_spike > 10 and bullish_ratio < 0.2:
                unusual.append({
                    'ticker': ticker,
                    'type': 'bearish_wave',
                    'mentions': mention_spike,
                    'bullish_ratio': bullish_ratio,
                    'confidence': avg_confidence
                })
        
        return sorted(unusual, key=lambda x: x['mentions'], reverse=True)[:10]
    
    async def _search_ticker_posts(
        self,
        ticker: str,
        subreddit: str,
        hours_back: int
    ) -> List[RedditPost]:
        """Search for posts mentioning specific ticker"""
        # Implementation would search Reddit for ticker mentions
        # Placeholder for now
        return []
    
    def _get_price_context(self, ticker: str) -> Dict[str, any]:
        """Get current price context for ticker"""
        try:
            stock = yf.Ticker(ticker)
            info = stock.info
            
            return {
                'current_price': info.get('regularMarketPrice', 0),
                'change_percent': info.get('regularMarketChangePercent', 0),
                'volume': info.get('regularMarketVolume', 0),
                'market_cap': info.get('marketCap', 0)
            }
        except:
            return {}
    
    def _calculate_ticker_sentiment(self, sentiments: List[WSBSentiment]) -> Dict[str, any]:
        """Calculate sentiment for specific ticker"""
        return self._calculate_overall_sentiment(sentiments)
    
    def _calculate_wsb_score(self, sentiments: List[WSBSentiment]) -> float:
        """Calculate WSB hype score (0-100)"""
        if not sentiments:
            return 0
        
        # Factors
        mention_score = min(len(sentiments) / 50 * 30, 30)  # Max 30 points
        
        engagement_score = min(
            sum(np.log1p(s.score) for s in sentiments) / len(sentiments) * 5,
            20  # Max 20 points
        )
        
        rocket_score = min(
            sum(s.wsb_indicators.get('rocket_count', 0) for s in sentiments) / len(sentiments) * 10,
            20  # Max 20 points
        )
        
        confidence_score = np.mean([s.confidence for s in sentiments]) * 30  # Max 30 points
        
        return mention_score + engagement_score + rocket_score + confidence_score
    
    def _analyze_position_bias(self, sentiments: List[WSBSentiment]) -> Dict[str, float]:
        """Analyze position type bias"""
        positions = defaultdict(int)
        
        for sent in sentiments:
            if sent.position_type:
                positions[sent.position_type] += 1
        
        total = sum(positions.values())
        if total == 0:
            return {'calls': 0, 'puts': 0, 'shares': 0}
        
        return {
            pos: count / total * 100
            for pos, count in positions.items()
        }
    
    def _create_sentiment_timeline(self, sentiments: List[WSBSentiment]) -> List[Dict]:
        """Create hourly sentiment timeline"""
        if not sentiments:
            return []
        
        # Group by hour
        hourly = defaultdict(list)
        for sent in sentiments:
            hour = sent.created_at.replace(minute=0, second=0, microsecond=0)
            hourly[hour].append(sent)
        
        # Calculate hourly sentiment
        timeline = []
        for hour, hour_sents in sorted(hourly.items()):
            dist = self._get_distribution(hour_sents)
            timeline.append({
                'hour': hour.isoformat(),
                'posts': len(hour_sents),
                'sentiment': 'bullish' if dist['bullish'] > 50 else 'bearish' if dist['bearish'] > 50 else 'neutral',
                'distribution': dist
            })
        
        return timeline
    
    def _get_notable_posts(self, sentiments: List[WSBSentiment], limit: int) -> List[Dict]:
        """Get most notable posts"""
        # Sort by score and DD quality
        sorted_sents = sorted(
            sentiments,
            key=lambda x: x.score * x.wsb_indicators.get('dd_quality', 0.5),
            reverse=True
        )
        
        return [
            {
                'text': s.text[:300] + '...',
                'author': s.author,
                'score': s.score,
                'sentiment': s.sentiment,
                'dd_quality': s.wsb_indicators.get('dd_quality', 0),
                'position': s.position_type,
                'target': s.price_target,
                'created': s.created_at.isoformat()
            }
            for s in sorted_sents[:limit]
        ]
    
    def _extract_crowd_targets(self, sentiments: List[WSBSentiment]) -> Dict[str, any]:
        """Extract crowd consensus on price targets"""
        targets = [s.price_target for s in sentiments if s.price_target]
        
        if not targets:
            return {'has_targets': False}
        
        return {
            'has_targets': True,
            'average_target': np.mean(targets),
            'median_target': np.median(targets),
            'min_target': min(targets),
            'max_target': max(targets),
            'target_count': len(targets)
        }