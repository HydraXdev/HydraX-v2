"""
GROK AI Integration for Enhanced Sentiment Analysis
Analyzes X/Twitter sentiment with advanced AI capabilities
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
import numpy as np
import random
from enum import Enum

# Import required components
from .signal_fusion import IntelSource

logger = logging.getLogger(__name__)


class SentimentCategory(Enum):
    """Grok AI sentiment categories"""
    X_MOMENTUM = "x_momentum"           # Viral/trending momentum on X
    WHALE_ACTIVITY = "whale_activity"   # Large trader sentiment
    RETAIL_FOMO = "retail_fomo"        # Retail trader FOMO indicators
    SMART_MONEY_FLOW = "smart_money_flow"  # Institutional sentiment


@dataclass
class GrokSentimentData:
    """Structured sentiment data from Grok AI"""
    category: SentimentCategory
    score: float  # -100 to +100 (bearish to bullish)
    confidence: float  # 0-100
    volume: int  # Number of posts/mentions analyzed
    influencer_weight: float  # Weight based on influencer activity
    metadata: Dict = None


class GrokAIClient:
    """Mock Grok AI client - structured for real API integration"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key
        self.base_url = "https://api.grok.x.ai/v1"  # Placeholder for actual API
        self.rate_limit = 100  # requests per minute
        self.last_request_time = datetime.now()
        
    async def analyze_sentiment(self, symbol: str, timeframe: str = "1h") -> Dict[str, Any]:
        """
        Mock API call to Grok AI for sentiment analysis
        In production, this would make actual API calls
        """
        # Simulate API delay
        await asyncio.sleep(0.1)
        
        # Generate mock sentiment data with realistic patterns
        base_sentiment = random.uniform(-50, 50)
        
        # Add market hours influence
        hour = datetime.now().hour
        if 9 <= hour <= 16:  # US market hours
            base_sentiment += random.uniform(5, 15)
        
        # Generate category-specific sentiments
        sentiments = {
            SentimentCategory.X_MOMENTUM: self._generate_x_momentum(base_sentiment),
            SentimentCategory.WHALE_ACTIVITY: self._generate_whale_activity(base_sentiment),
            SentimentCategory.RETAIL_FOMO: self._generate_retail_fomo(base_sentiment),
            SentimentCategory.SMART_MONEY_FLOW: self._generate_smart_money_flow(base_sentiment)
        }
        
        return {
            'symbol': symbol,
            'timeframe': timeframe,
            'timestamp': datetime.now().isoformat(),
            'sentiments': sentiments,
            'overall_score': np.mean([s['score'] for s in sentiments.values()]),
            'api_version': 'mock_v1'
        }
    
    def _generate_x_momentum(self, base: float) -> Dict:
        """Generate X momentum sentiment data"""
        volatility = random.uniform(10, 30)
        score = base + random.uniform(-volatility, volatility)
        
        return {
            'score': max(-100, min(100, score)),
            'confidence': random.uniform(70, 95),
            'volume': random.randint(1000, 50000),
            'influencer_weight': random.uniform(0.5, 1.0),
            'trending_rank': random.randint(1, 100) if score > 30 else None,
            'viral_coefficient': random.uniform(0.1, 2.0)
        }
    
    def _generate_whale_activity(self, base: float) -> Dict:
        """Generate whale activity sentiment data"""
        # Whales tend to be contrarian
        score = base * -0.3 + random.uniform(-20, 20)
        
        return {
            'score': max(-100, min(100, score)),
            'confidence': random.uniform(75, 90),
            'volume': random.randint(10, 500),
            'influencer_weight': random.uniform(0.8, 1.0),
            'whale_count': random.randint(5, 50),
            'avg_position_size': random.uniform(100000, 1000000)
        }
    
    def _generate_retail_fomo(self, base: float) -> Dict:
        """Generate retail FOMO sentiment data"""
        # Retail tends to be more extreme
        score = base * 1.5 + random.uniform(-25, 25)
        
        return {
            'score': max(-100, min(100, score)),
            'confidence': random.uniform(65, 85),
            'volume': random.randint(5000, 100000),
            'influencer_weight': random.uniform(0.3, 0.7),
            'fomo_index': random.uniform(0, 100),
            'new_trader_ratio': random.uniform(0.1, 0.5)
        }
    
    def _generate_smart_money_flow(self, base: float) -> Dict:
        """Generate smart money flow sentiment data"""
        # Smart money is more measured
        score = base * 0.7 + random.uniform(-15, 15)
        
        return {
            'score': max(-100, min(100, score)),
            'confidence': random.uniform(80, 95),
            'volume': random.randint(50, 1000),
            'influencer_weight': random.uniform(0.9, 1.0),
            'institutional_ratio': random.uniform(0.6, 0.9),
            'options_flow_alignment': random.uniform(-1, 1)
        }


class GrokAIIntelligence:
    """Grok AI intelligence source for BITTEN integration"""
    
    def __init__(self):
        self.client = GrokAIClient()
        self.cache = {}
        self.cache_duration = timedelta(minutes=5)
        
        # Sentiment thresholds
        self.bullish_threshold = 30
        self.bearish_threshold = -30
        
        # Category weights for final signal
        self.category_weights = {
            SentimentCategory.X_MOMENTUM: 0.25,
            SentimentCategory.WHALE_ACTIVITY: 0.35,
            SentimentCategory.RETAIL_FOMO: 0.15,
            SentimentCategory.SMART_MONEY_FLOW: 0.25
        }
    
    async def analyze(self, pair: str, market_data: Dict) -> Optional[IntelSource]:
        """Analyze sentiment using Grok AI"""
        try:
            # Check cache
            cache_key = f"{pair}_{datetime.now().hour}"
            if cache_key in self.cache:
                cached_data, cache_time = self.cache[cache_key]
                if datetime.now() - cache_time < self.cache_duration:
                    return self._process_sentiment_data(cached_data, pair)
            
            # Get sentiment from Grok AI
            sentiment_data = await self.client.analyze_sentiment(pair)
            
            # Cache the result
            self.cache[cache_key] = (sentiment_data, datetime.now())
            
            # Process and return signal
            return self._process_sentiment_data(sentiment_data, pair)
            
        except Exception as e:
            logger.error(f"Grok AI intelligence error: {e}")
            return None
    
    def _process_sentiment_data(self, data: Dict, pair: str) -> Optional[IntelSource]:
        """Process Grok AI sentiment data into IntelSource"""
        try:
            sentiments = data['sentiments']
            
            # Calculate weighted sentiment score
            weighted_score = 0
            total_confidence = 0
            category_details = {}
            
            for category, weight in self.category_weights.items():
                sentiment = sentiments.get(category, {})
                score = sentiment.get('score', 0)
                confidence = sentiment.get('confidence', 50)
                
                weighted_score += score * weight * (confidence / 100)
                total_confidence += confidence * weight
                
                # Store category details
                category_details[category.value] = {
                    'score': score,
                    'confidence': confidence,
                    'volume': sentiment.get('volume', 0),
                    'influencer_weight': sentiment.get('influencer_weight', 0.5)
                }
            
            # Determine signal direction
            if weighted_score > self.bullish_threshold:
                direction = 'BUY'
                signal_confidence = min(95, 50 + (weighted_score - self.bullish_threshold))
            elif weighted_score < self.bearish_threshold:
                direction = 'SELL'
                signal_confidence = min(95, 50 + abs(weighted_score - self.bearish_threshold))
            else:
                return None  # No clear signal
            
            # Adjust confidence based on volume and influencer activity
            avg_volume = np.mean([s.get('volume', 0) for s in sentiments.values()])
            if avg_volume > 10000:
                signal_confidence *= 1.1
            
            avg_influencer = np.mean([s.get('influencer_weight', 0.5) for s in sentiments.values()])
            if avg_influencer > 0.8:
                signal_confidence *= 1.05
            
            signal_confidence = min(95, signal_confidence)
            
            # Create special metadata for Grok AI
            grok_metadata = {
                'overall_sentiment': weighted_score,
                'category_breakdown': category_details,
                'x_momentum': category_details.get('x_momentum', {}).get('score', 0),
                'whale_activity': category_details.get('whale_activity', {}).get('score', 0),
                'retail_fomo': category_details.get('retail_fomo', {}).get('score', 0),
                'smart_money_flow': category_details.get('smart_money_flow', {}).get('score', 0),
                'data_freshness': 'real-time',
                'powered_by': 'Grok AI',
                'api_version': data.get('api_version', 'mock_v1')
            }
            
            return IntelSource(
                source_id='grok_ai_sentiment',
                source_type='ai_sentiment',
                signal=direction,
                confidence=signal_confidence,
                weight=0.35,  # High weight for Grok AI
                metadata=grok_metadata
            )
            
        except Exception as e:
            logger.error(f"Error processing Grok sentiment data: {e}")
            return None
    
    def get_sentiment_summary(self, intel_source: IntelSource) -> Dict[str, Any]:
        """Get formatted sentiment summary for display"""
        if not intel_source or intel_source.source_id != 'grok_ai_sentiment':
            return {}
        
        metadata = intel_source.metadata
        
        # Format sentiment categories with emojis
        category_display = {
            'x_momentum': f"📈 X Momentum: {metadata.get('x_momentum', 0):.0f}",
            'whale_activity': f"🐋 Whale Activity: {metadata.get('whale_activity', 0):.0f}",
            'retail_fomo': f"🚀 Retail FOMO: {metadata.get('retail_fomo', 0):.0f}",
            'smart_money': f"💎 Smart Money Flow: {metadata.get('smart_money_flow', 0):.0f}"
        }
        
        return {
            'powered_by': '🤖 Powered by Grok AI',
            'overall_sentiment': metadata.get('overall_sentiment', 0),
            'signal': intel_source.signal,
            'confidence': intel_source.confidence,
            'categories': category_display,
            'timestamp': intel_source.timestamp
        }
    
    def format_signal_enhancement(self, signal_display: str, intel_source: Optional[IntelSource]) -> str:
        """Add Grok AI branding to signal displays"""
        if not intel_source or intel_source.source_id != 'grok_ai_sentiment':
            return signal_display
        
        summary = self.get_sentiment_summary(intel_source)
        
        # Create Grok AI sentiment section
        grok_section = f"""
🤖 **GROK AI SENTIMENT ANALYSIS** 🤖
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{summary['categories']['x_momentum']}
{summary['categories']['whale_activity']}
{summary['categories']['retail_fomo']}
{summary['categories']['smart_money']}

**Overall Signal:** {summary['signal']} @ {summary['confidence']:.0f}% confidence
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{summary['powered_by']}
"""
        
        # Insert Grok section into signal display
        # Find a good insertion point (after TCS score)
        lines = signal_display.split('\n')
        insert_index = -1
        
        for i, line in enumerate(lines):
            if 'INTEL CONFIDENCE' in line or 'TCS' in line:
                insert_index = i + 2  # Insert after the TCS visual
                break
        
        if insert_index > 0:
            lines.insert(insert_index, grok_section)
            return '\n'.join(lines)
        else:
            # If no good insertion point, append at end
            return signal_display + '\n' + grok_section


# Create global instance
grok_ai_intelligence = GrokAIIntelligence()


# Test the integration
if __name__ == "__main__":
    async def test_grok_integration():
        """Test Grok AI integration"""
        
        # Test sentiment analysis
        intel = await grok_ai_intelligence.analyze("EURUSD", {})
        
        if intel:
            print("=== GROK AI INTEL SOURCE ===")
            print(f"Signal: {intel.signal}")
            print(f"Confidence: {intel.confidence:.1f}%")
            print(f"Weight: {intel.weight}")
            
            print("\n=== SENTIMENT SUMMARY ===")
            summary = grok_ai_intelligence.get_sentiment_summary(intel)
            for key, value in summary['categories'].items():
                print(value)
            
            print(f"\nOverall Sentiment: {summary['overall_sentiment']:.1f}")
            print(summary['powered_by'])
        
        # Test signal enhancement
        test_signal = """
⚡ **TACTICAL SITREP** - ARCADE SCALP ⚡
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🎮 **OP: ROCKET RIDE**
📍 **AO:** EURUSD | **VECTOR:** BUY
🎯 **ENTRY:** 1.08750
💥 **OBJECTIVE:** +25 PIPS
⚔️ **RISK:** 5 PIPS

📊 **INTEL CONFIDENCE:** 82% ⭐
⭐ ███████░░ PRECISION

⏱️ **OP WINDOW:** 🟩🟩🟩🟩🟩 HOT
👥 **SQUAD ENGAGED:** 47 OPERATORS

[🔫 **ENGAGE TARGET**] [📋 **VIEW INTEL**]
"""
        
        if intel:
            enhanced_signal = grok_ai_intelligence.format_signal_enhancement(test_signal, intel)
            print("\n=== ENHANCED SIGNAL WITH GROK AI ===")
            print(enhanced_signal)
    
    # Run the test
    asyncio.run(test_grok_integration())