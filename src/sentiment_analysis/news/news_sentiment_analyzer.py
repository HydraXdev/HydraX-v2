"""
News Sentiment Analyzer using BERT and Transformers

Performs advanced sentiment analysis on financial news using
state-of-the-art transformer models fine-tuned for financial texts.
"""

import re
from typing import List, Dict, Tuple, Optional
from datetime import datetime, timedelta
import numpy as np
from dataclasses import dataclass
import logging
from transformers import (
    pipeline, 
    AutoTokenizer, 
    AutoModelForSequenceClassification,
    AutoModelForTokenClassification
)
import torch
from collections import defaultdict
import asyncio
from textblob import TextBlob

from .news_client import NewsClient, NewsArticle

logger = logging.getLogger(__name__)


@dataclass
class NewsSentiment:
    """News sentiment analysis result"""
    article_id: str
    title: str
    source: str
    published_at: datetime
    sentiment: str  # positive, negative, neutral
    confidence: float
    impact_score: float  # 0-100 impact on market
    entities: Dict[str, List[str]]
    keywords: List[str]
    summary: Optional[str] = None
    

class NewsSentimentAnalyzer:
    """
    Advanced news sentiment analyzer using BERT and financial NLP models
    """
    
    def __init__(self, news_client: Optional[NewsClient] = None):
        """
        Initialize news sentiment analyzer
        
        Args:
            news_client: News API client instance
        """
        self.news_client = news_client or NewsClient()
        
        # Initialize models
        self._init_models()
        
        # Market impact keywords
        self.high_impact_keywords = {
            'fed', 'federal reserve', 'interest rate', 'inflation', 'cpi',
            'unemployment', 'gdp', 'earnings', 'guidance', 'merger',
            'acquisition', 'bankruptcy', 'scandal', 'investigation',
            'sec', 'regulation', 'tariff', 'trade war', 'recession',
            'stimulus', 'bailout', 'ipo', 'offering', 'dividend'
        }
        
        # Sentiment modifiers
        self.positive_modifiers = {
            'beat', 'exceed', 'surge', 'jump', 'rally', 'boost', 'gain',
            'profit', 'growth', 'expand', 'improve', 'upgrade', 'positive'
        }
        
        self.negative_modifiers = {
            'miss', 'fall', 'drop', 'plunge', 'crash', 'loss', 'decline',
            'weak', 'concern', 'worry', 'fear', 'risk', 'downgrade', 'negative'
        }
        
    def _init_models(self):
        """Initialize NLP models"""
        try:
            # Financial BERT for sentiment
            self.finbert_model = "ProsusAI/finbert"
            self.sentiment_analyzer = pipeline(
                "sentiment-analysis",
                model=self.finbert_model,
                device=0 if torch.cuda.is_available() else -1
            )
            
            # NER for entity extraction
            self.ner_model = "dslim/bert-base-NER"
            self.ner_analyzer = pipeline(
                "ner",
                model=self.ner_model,
                aggregation_strategy="simple",
                device=0 if torch.cuda.is_available() else -1
            )
            
            # Summarization model
            self.summarizer = pipeline(
                "summarization",
                model="facebook/bart-large-cnn",
                device=0 if torch.cuda.is_available() else -1
            )
            
            logger.info("News sentiment models initialized successfully")
            
        except Exception as e:
            logger.error(f"Error initializing models: {e}")
            self.sentiment_analyzer = None
            self.ner_analyzer = None
            self.summarizer = None
    
    async def analyze_market_news(
        self,
        hours_back: int = 24,
        min_impact_score: float = 50.0
    ) -> Dict[str, any]:
        """
        Analyze overall market news sentiment
        
        Args:
            hours_back: Hours to look back
            min_impact_score: Minimum impact score to include
            
        Returns:
            Market sentiment analysis results
        """
        try:
            # Get recent news
            articles = await self.news_client.get_market_news(hours_back=hours_back)
            
            # Analyze each article
            sentiments = []
            high_impact_news = []
            
            for article in articles:
                sentiment = await self._analyze_article(article)
                sentiments.append(sentiment)
                
                # Track high impact news
                if sentiment.impact_score >= min_impact_score:
                    high_impact_news.append(sentiment)
            
            # Calculate aggregate metrics
            results = {
                'timestamp': datetime.utcnow().isoformat(),
                'article_count': len(sentiments),
                'sentiment_distribution': self._calculate_distribution(sentiments),
                'average_confidence': np.mean([s.confidence for s in sentiments]) if sentiments else 0,
                'market_sentiment': self._calculate_market_sentiment(sentiments),
                'high_impact_news': self._format_high_impact_news(high_impact_news),
                'top_entities': self._extract_top_entities(sentiments),
                'sentiment_trend': self._calculate_sentiment_trend(sentiments)
            }
            
            return results
            
        except Exception as e:
            logger.error(f"Error analyzing market news: {e}")
            return {}
    
    async def analyze_symbol_news(
        self,
        symbol: str,
        hours_back: int = 24
    ) -> Dict[str, any]:
        """
        Analyze news sentiment for a specific symbol
        
        Args:
            symbol: Stock symbol
            hours_back: Hours to look back
            
        Returns:
            Symbol-specific sentiment analysis
        """
        try:
            # Get symbol news
            articles = await self.news_client.get_symbol_news(
                symbol=symbol,
                hours_back=hours_back
            )
            
            if not articles:
                return {
                    'symbol': symbol,
                    'sentiment': 'neutral',
                    'confidence': 0.0,
                    'article_count': 0,
                    'message': 'No recent news found'
                }
            
            # Analyze articles
            sentiments = []
            for article in articles:
                sentiment = await self._analyze_article(article)
                sentiments.append(sentiment)
            
            # Calculate symbol sentiment
            positive = sum(1 for s in sentiments if s.sentiment == 'positive')
            negative = sum(1 for s in sentiments if s.sentiment == 'negative')
            total = len(sentiments)
            
            # Weighted by impact and confidence
            weighted_score = sum(
                (1 if s.sentiment == 'positive' else -1 if s.sentiment == 'negative' else 0) 
                * s.confidence * (s.impact_score / 100)
                for s in sentiments
            ) / total if total > 0 else 0
            
            # Determine overall sentiment
            if weighted_score > 0.2:
                overall_sentiment = 'positive'
            elif weighted_score < -0.2:
                overall_sentiment = 'negative'
            else:
                overall_sentiment = 'neutral'
            
            results = {
                'symbol': symbol,
                'sentiment': overall_sentiment,
                'sentiment_score': weighted_score * 100,
                'confidence': np.mean([s.confidence for s in sentiments]),
                'article_count': total,
                'positive_count': positive,
                'negative_count': negative,
                'average_impact': np.mean([s.impact_score for s in sentiments]),
                'recent_headlines': [
                    {
                        'title': s.title,
                        'source': s.source,
                        'sentiment': s.sentiment,
                        'impact': s.impact_score,
                        'published': s.published_at.isoformat()
                    }
                    for s in sorted(sentiments, key=lambda x: x.impact_score, reverse=True)[:5]
                ],
                'key_themes': self._extract_themes(sentiments)
            }
            
            return results
            
        except Exception as e:
            logger.error(f"Error analyzing symbol news: {e}")
            return {'symbol': symbol, 'error': str(e)}
    
    async def _analyze_article(self, article: NewsArticle) -> NewsSentiment:
        """
        Analyze individual news article
        
        Args:
            article: NewsArticle object
            
        Returns:
            NewsSentiment object
        """
        try:
            # Combine title and description for analysis
            text = f"{article.title}. {article.description or ''}"
            
            # Get sentiment
            if self.sentiment_analyzer:
                sentiment, confidence = await self._get_bert_sentiment(text)
            else:
                sentiment, confidence = self._get_basic_sentiment(text)
            
            # Calculate impact score
            impact_score = self._calculate_impact_score(article)
            
            # Extract entities
            entities = await self._extract_entities(text)
            
            # Extract keywords
            keywords = self._extract_keywords(text)
            
            # Generate summary if content available
            summary = None
            if article.content and self.summarizer:
                try:
                    summary = self.summarizer(
                        article.content[:1024], 
                        max_length=100, 
                        min_length=30
                    )[0]['summary_text']
                except:
                    pass
            
            return NewsSentiment(
                article_id=str(hash(article.url)),
                title=article.title,
                source=article.source,
                published_at=article.published_at,
                sentiment=sentiment,
                confidence=confidence,
                impact_score=impact_score,
                entities=entities,
                keywords=keywords,
                summary=summary
            )
            
        except Exception as e:
            logger.error(f"Error analyzing article: {e}")
            return NewsSentiment(
                article_id=str(hash(article.url)),
                title=article.title,
                source=article.source,
                published_at=article.published_at,
                sentiment='neutral',
                confidence=0.5,
                impact_score=50.0,
                entities={},
                keywords=[]
            )
    
    async def _get_bert_sentiment(self, text: str) -> Tuple[str, float]:
        """Get sentiment using BERT model"""
        try:
            # Truncate text for model
            truncated_text = text[:512]
            
            # Get prediction
            result = self.sentiment_analyzer(truncated_text)[0]
            
            # Map labels
            label_map = {
                'positive': 'positive',
                'negative': 'negative',
                'neutral': 'neutral'
            }
            
            sentiment = label_map.get(result['label'].lower(), 'neutral')
            confidence = result['score']
            
            return sentiment, confidence
            
        except Exception as e:
            logger.error(f"Error in BERT sentiment: {e}")
            return self._get_basic_sentiment(text)
    
    def _get_basic_sentiment(self, text: str) -> Tuple[str, float]:
        """Get basic sentiment using keywords and TextBlob"""
        try:
            # Keyword analysis
            text_lower = text.lower()
            
            positive_count = sum(1 for word in self.positive_modifiers if word in text_lower)
            negative_count = sum(1 for word in self.negative_modifiers if word in text_lower)
            
            # TextBlob sentiment
            blob = TextBlob(text)
            polarity = blob.sentiment.polarity
            
            # Combine approaches
            keyword_score = positive_count - negative_count
            combined_score = (polarity + (keyword_score * 0.1)) / 2
            
            if combined_score > 0.1:
                sentiment = 'positive'
                confidence = min(0.9, 0.5 + abs(combined_score))
            elif combined_score < -0.1:
                sentiment = 'negative'
                confidence = min(0.9, 0.5 + abs(combined_score))
            else:
                sentiment = 'neutral'
                confidence = 0.6
            
            return sentiment, confidence
            
        except Exception as e:
            logger.error(f"Error in basic sentiment: {e}")
            return 'neutral', 0.5
    
    def _calculate_impact_score(self, article: NewsArticle) -> float:
        """Calculate market impact score for article"""
        score = 50.0  # Base score
        
        text_lower = f"{article.title} {article.description or ''}".lower()
        
        # Check for high impact keywords
        for keyword in self.high_impact_keywords:
            if keyword in text_lower:
                score += 10
        
        # Source credibility bonus
        credible_sources = ['Reuters', 'Bloomberg', 'WSJ', 'Financial Times', 'CNBC']
        if article.source in credible_sources:
            score += 15
        
        # Recency bonus
        age_hours = (datetime.utcnow() - article.published_at).total_seconds() / 3600
        if age_hours < 1:
            score += 20
        elif age_hours < 6:
            score += 10
        
        # Cap at 100
        return min(100, score)
    
    async def _extract_entities(self, text: str) -> Dict[str, List[str]]:
        """Extract named entities from text"""
        entities = {
            'organizations': [],
            'persons': [],
            'locations': [],
            'misc': []
        }
        
        if not self.ner_analyzer:
            return entities
        
        try:
            # Get NER results
            ner_results = self.ner_analyzer(text[:512])
            
            # Group by entity type
            for entity in ner_results:
                entity_type = entity['entity_group']
                entity_text = entity['word']
                
                if entity_type == 'ORG':
                    entities['organizations'].append(entity_text)
                elif entity_type == 'PER':
                    entities['persons'].append(entity_text)
                elif entity_type == 'LOC':
                    entities['locations'].append(entity_text)
                else:
                    entities['misc'].append(entity_text)
            
            # Deduplicate
            for key in entities:
                entities[key] = list(set(entities[key]))
            
        except Exception as e:
            logger.error(f"Error extracting entities: {e}")
        
        return entities
    
    def _extract_keywords(self, text: str) -> List[str]:
        """Extract important keywords from text"""
        keywords = []
        
        # Extract financial terms
        financial_terms = [
            'earnings', 'revenue', 'profit', 'loss', 'growth', 'decline',
            'forecast', 'guidance', 'dividend', 'buyback', 'merger',
            'acquisition', 'ipo', 'bankruptcy', 'restructuring'
        ]
        
        text_lower = text.lower()
        for term in financial_terms:
            if term in text_lower:
                keywords.append(term)
        
        # Extract percentages and numbers
        percentage_pattern = re.compile(r'\d+\.?\d*%')
        percentages = percentage_pattern.findall(text)
        keywords.extend(percentages[:3])  # Top 3 percentages
        
        return keywords
    
    def _calculate_distribution(self, sentiments: List[NewsSentiment]) -> Dict[str, float]:
        """Calculate sentiment distribution"""
        if not sentiments:
            return {'positive': 0, 'negative': 0, 'neutral': 0}
        
        total = len(sentiments)
        distribution = {
            'positive': sum(1 for s in sentiments if s.sentiment == 'positive') / total * 100,
            'negative': sum(1 for s in sentiments if s.sentiment == 'negative') / total * 100,
            'neutral': sum(1 for s in sentiments if s.sentiment == 'neutral') / total * 100
        }
        
        return distribution
    
    def _calculate_market_sentiment(self, sentiments: List[NewsSentiment]) -> Dict[str, any]:
        """Calculate overall market sentiment"""
        if not sentiments:
            return {'sentiment': 'neutral', 'score': 0, 'confidence': 0}
        
        # Weight by impact and confidence
        weighted_sum = sum(
            (1 if s.sentiment == 'positive' else -1 if s.sentiment == 'negative' else 0)
            * s.confidence * (s.impact_score / 100)
            for s in sentiments
        )
        
        weighted_avg = weighted_sum / len(sentiments)
        
        if weighted_avg > 0.2:
            sentiment = 'bullish'
        elif weighted_avg < -0.2:
            sentiment = 'bearish'
        else:
            sentiment = 'neutral'
        
        return {
            'sentiment': sentiment,
            'score': weighted_avg * 100,
            'confidence': np.mean([s.confidence for s in sentiments])
        }
    
    def _format_high_impact_news(self, news: List[NewsSentiment]) -> List[Dict]:
        """Format high impact news for output"""
        return [
            {
                'title': n.title,
                'source': n.source,
                'sentiment': n.sentiment,
                'impact': n.impact_score,
                'summary': n.summary,
                'published': n.published_at.isoformat()
            }
            for n in sorted(news, key=lambda x: x.impact_score, reverse=True)[:10]
        ]
    
    def _extract_top_entities(self, sentiments: List[NewsSentiment]) -> Dict[str, List[str]]:
        """Extract most mentioned entities"""
        entity_counts = defaultdict(lambda: defaultdict(int))
        
        for sentiment in sentiments:
            for entity_type, entities in sentiment.entities.items():
                for entity in entities:
                    entity_counts[entity_type][entity] += 1
        
        # Get top 5 for each type
        top_entities = {}
        for entity_type, counts in entity_counts.items():
            sorted_entities = sorted(counts.items(), key=lambda x: x[1], reverse=True)
            top_entities[entity_type] = [e[0] for e in sorted_entities[:5]]
        
        return top_entities
    
    def _calculate_sentiment_trend(self, sentiments: List[NewsSentiment]) -> Dict[str, any]:
        """Calculate sentiment trend over time"""
        if not sentiments:
            return {'trend': 'stable', 'change': 0}
        
        # Sort by time
        sorted_sentiments = sorted(sentiments, key=lambda x: x.published_at)
        
        # Split into halves
        mid = len(sorted_sentiments) // 2
        first_half = sorted_sentiments[:mid]
        second_half = sorted_sentiments[mid:]
        
        # Calculate sentiment scores for each half
        def calc_score(sents):
            if not sents:
                return 0
            return sum(
                1 if s.sentiment == 'positive' else -1 if s.sentiment == 'negative' else 0
                for s in sents
            ) / len(sents)
        
        first_score = calc_score(first_half)
        second_score = calc_score(second_half)
        
        change = second_score - first_score
        
        if change > 0.1:
            trend = 'improving'
        elif change < -0.1:
            trend = 'deteriorating'
        else:
            trend = 'stable'
        
        return {
            'trend': trend,
            'change': change * 100
        }
    
    def _extract_themes(self, sentiments: List[NewsSentiment]) -> List[str]:
        """Extract key themes from news"""
        theme_counts = defaultdict(int)
        
        for sentiment in sentiments:
            for keyword in sentiment.keywords:
                theme_counts[keyword] += 1
        
        # Get top themes
        sorted_themes = sorted(theme_counts.items(), key=lambda x: x[1], reverse=True)
        return [theme[0] for theme in sorted_themes[:5]]