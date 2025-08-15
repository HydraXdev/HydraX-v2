# AI Market Prediction Ensemble System

A comprehensive market prediction AI that combines multiple free APIs to provide ensemble-based market sentiment analysis and price predictions with personality-specific commentary.

## Features

### 1. Multi-Source Data Aggregation
- **Alpha Vantage**: Real-time market data and technical indicators
- **NewsAPI**: News sentiment analysis from multiple sources
- **Reddit API**: Social sentiment from trading communities
- **Twitter API**: Real-time social media sentiment (optional)

### 2. Ensemble Prediction Model
- Technical analysis scoring (RSI, moving averages, price trends)
- Fundamental analysis based on news and market performance
- Social sentiment analysis from Reddit and Twitter
- Weighted ensemble scoring for balanced predictions

### 3. Personality-Based Commentary
Generate market commentary from 10 different trading personalities:
- **Aggressive Bull**: Ultra-optimistic, always looking for moon shots
- **Cautious Bear**: Pessimistic, always warning of crashes
- **Technical Analyst**: Chart-focused, indicator-driven analysis
- **Fundamental Trader**: Earnings and value-focused commentary
- **Contrarian**: Goes against the crowd sentiment
- **Momentum Trader**: Follows trends and momentum
- **Value Investor**: Long-term value perspective
- **Day Trader**: Short-term, intraday focus
- **Swing Trader**: Multi-day to multi-week perspective
- **Crypto Enthusiast**: Crypto-specific slang and enthusiasm

### 4. Advanced Features
- Intelligent caching to reduce API calls
- Asynchronous operations for performance
- Time-weighted news relevance scoring
- Sentiment analysis with keyword matching
- Confidence scoring based on signal agreement
- Risk level assessment

## Installation

```bash
# Install required packages
pip install aiohttp numpy python-dateutil

# For enhanced NLP sentiment analysis (optional)
pip install textblob nltk
```

## Configuration

Create API keys for the free services:

1. **Alpha Vantage** (Free tier: 5 API calls/minute)
   - Sign up at: https://www.alphavantage.co/support/#api-key
   - Free tier includes: Stock quotes, technical indicators

2. **NewsAPI** (Free tier: 100 requests/day)
   - Sign up at: https://newsapi.org/register
   - Free tier includes: News from 80,000+ sources

3. **Reddit API** (Free, rate limited)
   - Create app at: https://www.reddit.com/prefs/apps
   - Select "script" application type

4. **Twitter API** (Optional, requires approval)
   - Apply at: https://developer.twitter.com/

## Usage

### Basic Usage

```python
import asyncio
from ai_market_prediction import MarketPredictionEnsemble

async def predict_market():
    config = {
        'alpha_vantage_key': 'YOUR_ALPHA_VANTAGE_KEY',
        'newsapi_key': 'YOUR_NEWSAPI_KEY',
        'reddit_client_id': 'YOUR_REDDIT_CLIENT_ID',
        'reddit_client_secret': 'YOUR_REDDIT_CLIENT_SECRET',
        'twitter_bearer_token': 'OPTIONAL_TWITTER_TOKEN'
    }
    
    async with MarketPredictionEnsemble(config) as predictor:
        # Predict stock
        prediction = await predictor.predict('AAPL', keywords=['iPhone', 'earnings'])
        report = predictor.format_prediction_report(prediction)
        print(report)

asyncio.run(predict_market())
```

### Advanced Usage

```python
# Get raw prediction data
prediction = await predictor.predict('BTC')

# Access individual scores
print(f"Technical Score: {prediction.technical_score}")
print(f"Social Sentiment: {prediction.social_score}")
print(f"News Sentiment: {prediction.news_score}")

# Get specific personality commentary
aggressive_bull_comment = prediction.personality_commentary['aggressive_bull']
print(f"Aggressive Bull says: {aggressive_bull_comment}")

# Check prediction confidence
if prediction.confidence_score > 0.7:
    print(f"High confidence prediction: {prediction.recommendation}")
```

### Batch Predictions

```python
async def batch_predict(symbols):
    async with MarketPredictionEnsemble(config) as predictor:
        tasks = [predictor.predict(symbol) for symbol in symbols]
        predictions = await asyncio.gather(*tasks, return_exceptions=True)
        
        for pred in predictions:
            if isinstance(pred, Exception):
                print(f"Error: {pred}")
            else:
                print(f"{pred.symbol}: {pred.sentiment.value} - {pred.recommendation}")

# Predict multiple symbols
asyncio.run(batch_predict(['AAPL', 'GOOGL', 'TSLA', 'BTC', 'ETH']))
```

## Output Format

### Prediction Result Structure

```python
@dataclass
class PredictionResult:
    symbol: str                           # Trading symbol
    current_price: float                  # Current market price
    predicted_price_1h: float            # 1-hour price prediction
    predicted_price_24h: float           # 24-hour price prediction
    predicted_price_7d: float            # 7-day price prediction
    confidence_score: float              # Prediction confidence (0-1)
    sentiment: MarketSentiment           # Overall market sentiment
    technical_score: float               # Technical analysis score (-1 to 1)
    fundamental_score: float             # Fundamental analysis score (-1 to 1)
    social_score: float                  # Social sentiment score (-1 to 1)
    news_score: float                    # News sentiment score (-1 to 1)
    risk_level: str                      # "Low", "Medium", or "High"
    recommendation: str                  # "Strong Buy", "Buy", "Hold", "Sell", "Strong Sell"
    personality_commentary: Dict[str, str]  # Commentary from each personality
    timestamp: datetime                  # Prediction timestamp
```

### Market Sentiment Enum

```python
class MarketSentiment(Enum):
    VERY_BULLISH = "very_bullish"   # Strong positive sentiment
    BULLISH = "bullish"             # Positive sentiment
    NEUTRAL = "neutral"             # Mixed or unclear sentiment
    BEARISH = "bearish"             # Negative sentiment
    VERY_BEARISH = "very_bearish"   # Strong negative sentiment
```

## Sample Output

```markdown
# Market Prediction Report for AAPL

**Generated at:** 2025-07-12 15:30:00

## Current Market Status
- **Current Price:** $182.50
- **Market Sentiment:** Bullish
- **Recommendation:** Buy
- **Risk Level:** Medium
- **Confidence:** 72.5%

## Price Predictions
- **1 Hour:** $183.25 (+0.41%)
- **24 Hours:** $185.50 (+1.64%)
- **7 Days:** $190.75 (+4.52%)

## Analysis Scores
- **Technical Analysis:** 65.0%
- **Fundamental Analysis:** 70.0%
- **News Sentiment:** 75.0%
- **Social Sentiment:** 80.0%

## Personality Commentaries

### Aggressive Bull
🚀 TO THE MOON! AAPL is absolutely crushing it! Load up the truck!

### Cautious Bear
Proceed with caution. AAPL rally losing steam.

### Technical Analyst
AAPL testing resistance. Break above 185.0 targets 190.0.

### Fundamental Trader
AAPL showing strong fundamentals. Revenue growth accelerating.

### Contrarian
Getting crowded. AAPL sentiment too positive for comfort.

### Momentum Trader
AAPL momentum building. Adding on strength!

### Value Investor
AAPL approaching fair value. Still room for appreciation.

### Day Trader
Nice intraday setup on AAPL. Looking for quick 2-3%.

### Swing Trader
AAPL swing trade triggered. 2-4 week target: 190.0.

### Crypto Enthusiast
AAPL looking good! Accumulation phase ending soon!
```

## API Rate Limits

Be aware of free tier limitations:

| API | Free Tier Limit | Notes |
|-----|----------------|-------|
| Alpha Vantage | 5 calls/minute, 500/day | Use caching |
| NewsAPI | 100 requests/day | Batch requests when possible |
| Reddit | 60 requests/minute | Respect subreddit rules |
| Twitter | Varies by endpoint | Optional, requires approval |

## Best Practices

1. **Use Caching**: The system includes 5-minute caching to reduce API calls
2. **Batch Requests**: Process multiple symbols together when possible
3. **Error Handling**: Always handle API failures gracefully
4. **Rate Limiting**: Implement delays between requests if needed
5. **API Keys**: Keep API keys secure, use environment variables

## Extending the System

### Add New Data Sources

```python
async def fetch_custom_data(self, symbol: str) -> Dict:
    """Add your custom data source"""
    # Implement your data fetching logic
    pass

# Add to prediction calculation
custom_score = self._calculate_custom_score(custom_data)
```

### Add New Personalities

```python
# Add to TradingPersonality enum
NEW_TRADER = "new_trader"

# Add templates to _init_personality_generators
self.personality_templates[TradingPersonality.NEW_TRADER] = {
    'very_bullish': ["Your bullish templates"],
    'bullish': ["Your bullish templates"],
    # ... etc
}
```

### Customize Scoring Weights

```python
# Modify in _calculate_ensemble_prediction
weights = {
    'technical': 0.25,      # Reduce technical weight
    'fundamental': 0.25,    # Increase fundamental weight
    'news': 0.30,          # Increase news weight
    'social': 0.20         # Reduce social weight
}
```

## Limitations

1. **Sentiment Analysis**: Uses keyword-based sentiment analysis. Consider upgrading to ML-based analysis for production
2. **Technical Indicators**: Limited to basic indicators available from free APIs
3. **Fundamental Data**: Limited fundamental data from free sources
4. **Real-time Data**: Free tiers often have delays (15-20 minutes for stocks)
5. **Rate Limits**: Free API tiers have strict rate limits

## Production Considerations

1. **API Key Management**: Use environment variables or secret management service
2. **Error Handling**: Implement robust error handling and retry logic
3. **Monitoring**: Add logging and monitoring for API usage
4. **Database**: Store predictions for historical analysis
5. **ML Enhancement**: Consider adding machine learning models for better predictions
6. **Premium APIs**: Upgrade to paid tiers for real-time data and higher limits

## Disclaimer

This system is for educational and research purposes only. Always do your own research and consult with financial advisors before making investment decisions. Past performance does not guarantee future results.