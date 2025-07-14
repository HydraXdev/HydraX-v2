#!/usr/bin/env python3
"""
Web API wrapper for AI Market Prediction Ensemble System
Provides RESTful endpoints for market predictions
"""

from flask import Flask, jsonify, request
from flask_cors import CORS
import asyncio
import os
import logging
from datetime import datetime
from functools import wraps
from ai_market_prediction import MarketPredictionEnsemble, MarketSentiment, TradingPersonality

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
CORS(app)  # Enable CORS for frontend access

# Global predictor instance
predictor = None
loop = None


def async_route(f):
    """Decorator to run async functions in Flask routes"""
    @wraps(f)
    def wrapper(*args, **kwargs):
        return asyncio.run_coroutine_threadsafe(
            f(*args, **kwargs), loop
        ).result()
    return wrapper


@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'service': 'AI Market Prediction API'
    })


@app.route('/predict/<symbol>', methods=['GET'])
@async_route
async def predict_symbol(symbol):
    """
    Get prediction for a specific symbol
    
    Query parameters:
    - keywords: Comma-separated keywords for news search
    - personality: Specific personality for commentary (optional)
    """
    try:
        # Parse query parameters
        keywords = request.args.get('keywords', '').split(',') if request.args.get('keywords') else None
        personality_filter = request.args.get('personality')
        
        # Get prediction
        prediction = await predictor.predict(symbol.upper(), keywords)
        
        # Build response
        response = {
            'success': True,
            'data': {
                'symbol': prediction.symbol,
                'timestamp': prediction.timestamp.isoformat(),
                'current_price': prediction.current_price,
                'predictions': {
                    '1h': {
                        'price': prediction.predicted_price_1h,
                        'change_percent': round((prediction.predicted_price_1h / prediction.current_price - 1) * 100, 2)
                    },
                    '24h': {
                        'price': prediction.predicted_price_24h,
                        'change_percent': round((prediction.predicted_price_24h / prediction.current_price - 1) * 100, 2)
                    },
                    '7d': {
                        'price': prediction.predicted_price_7d,
                        'change_percent': round((prediction.predicted_price_7d / prediction.current_price - 1) * 100, 2)
                    }
                },
                'analysis': {
                    'sentiment': prediction.sentiment.value,
                    'recommendation': prediction.recommendation,
                    'confidence_score': round(prediction.confidence_score, 3),
                    'risk_level': prediction.risk_level
                },
                'scores': {
                    'technical': round(prediction.technical_score, 3),
                    'fundamental': round(prediction.fundamental_score, 3),
                    'news': round(prediction.news_score, 3),
                    'social': round(prediction.social_score, 3)
                },
                'personality_commentary': prediction.personality_commentary if not personality_filter
                    else {personality_filter: prediction.personality_commentary.get(personality_filter, 'N/A')}
            }
        }
        
        return jsonify(response)
        
    except Exception as e:
        logger.error(f"Error predicting {symbol}: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/predict/batch', methods=['POST'])
@async_route
async def predict_batch():
    """
    Get predictions for multiple symbols
    
    Request body:
    {
        "symbols": ["AAPL", "GOOGL", "BTC"],
        "keywords": {
            "AAPL": ["iPhone", "earnings"],
            "BTC": ["Bitcoin", "halving"]
        }
    }
    """
    try:
        data = request.get_json()
        symbols = data.get('symbols', [])
        keywords_map = data.get('keywords', {})
        
        if not symbols:
            return jsonify({
                'success': False,
                'error': 'No symbols provided'
            }), 400
        
        # Create prediction tasks
        tasks = []
        for symbol in symbols:
            keywords = keywords_map.get(symbol)
            tasks.append(predictor.predict(symbol.upper(), keywords))
        
        # Execute predictions in parallel
        predictions = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Build response
        results = []
        errors = []
        
        for symbol, pred in zip(symbols, predictions):
            if isinstance(pred, Exception):
                errors.append({
                    'symbol': symbol,
                    'error': str(pred)
                })
            else:
                results.append({
                    'symbol': pred.symbol,
                    'current_price': pred.current_price,
                    'sentiment': pred.sentiment.value,
                    'recommendation': pred.recommendation,
                    'confidence_score': round(pred.confidence_score, 3),
                    'predicted_change_24h': round((pred.predicted_price_24h / pred.current_price - 1) * 100, 2)
                })
        
        return jsonify({
            'success': True,
            'data': {
                'results': results,
                'errors': errors,
                'timestamp': datetime.now().isoformat()
            }
        })
        
    except Exception as e:
        logger.error(f"Error in batch prediction: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/personalities', methods=['GET'])
def get_personalities():
    """Get available trading personalities"""
    personalities = [
        {
            'id': p.value,
            'name': p.value.replace('_', ' ').title(),
            'description': get_personality_description(p)
        }
        for p in TradingPersonality
    ]
    
    return jsonify({
        'success': True,
        'data': personalities
    })


@app.route('/sentiments', methods=['GET'])
def get_sentiments():
    """Get possible sentiment values"""
    sentiments = [
        {
            'value': s.value,
            'name': s.value.replace('_', ' ').title(),
            'description': get_sentiment_description(s)
        }
        for s in MarketSentiment
    ]
    
    return jsonify({
        'success': True,
        'data': sentiments
    })


@app.route('/report/<symbol>', methods=['GET'])
@async_route
async def get_report(symbol):
    """Get formatted markdown report for a symbol"""
    try:
        keywords = request.args.get('keywords', '').split(',') if request.args.get('keywords') else None
        
        # Get prediction
        prediction = await predictor.predict(symbol.upper(), keywords)
        
        # Generate report
        report = predictor.format_prediction_report(prediction)
        
        return jsonify({
            'success': True,
            'data': {
                'symbol': prediction.symbol,
                'report': report,
                'timestamp': prediction.timestamp.isoformat()
            }
        })
        
    except Exception as e:
        logger.error(f"Error generating report for {symbol}: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


def get_personality_description(personality: TradingPersonality) -> str:
    """Get description for a trading personality"""
    descriptions = {
        TradingPersonality.AGGRESSIVE_BULL: "Ultra-optimistic trader always looking for moon shots",
        TradingPersonality.CAUTIOUS_BEAR: "Pessimistic trader always warning of potential crashes",
        TradingPersonality.TECHNICAL_ANALYST: "Chart-focused trader using indicators and patterns",
        TradingPersonality.FUNDAMENTAL_TRADER: "Value-focused trader analyzing earnings and fundamentals",
        TradingPersonality.CONTRARIAN: "Trader who goes against crowd sentiment",
        TradingPersonality.MOMENTUM_TRADER: "Trend-following trader riding momentum",
        TradingPersonality.VALUE_INVESTOR: "Long-term investor seeking undervalued assets",
        TradingPersonality.DAY_TRADER: "Short-term trader focusing on intraday moves",
        TradingPersonality.SWING_TRADER: "Medium-term trader holding positions for days/weeks",
        TradingPersonality.CRYPTO_ENTHUSIAST: "Crypto-focused trader with diamond hands mentality"
    }
    return descriptions.get(personality, "Trading personality")


def get_sentiment_description(sentiment: MarketSentiment) -> str:
    """Get description for a market sentiment"""
    descriptions = {
        MarketSentiment.VERY_BULLISH: "Extremely positive market outlook",
        MarketSentiment.BULLISH: "Positive market outlook",
        MarketSentiment.NEUTRAL: "Mixed or unclear market direction",
        MarketSentiment.BEARISH: "Negative market outlook",
        MarketSentiment.VERY_BEARISH: "Extremely negative market outlook"
    }
    return descriptions.get(sentiment, "Market sentiment")


async def init_predictor():
    """Initialize the predictor with configuration"""
    global predictor
    
    config = {
        'alpha_vantage_key': os.getenv('ALPHA_VANTAGE_KEY', 'demo'),
        'newsapi_key': os.getenv('NEWSAPI_KEY', 'demo'),
        'reddit_client_id': os.getenv('REDDIT_CLIENT_ID', 'demo'),
        'reddit_client_secret': os.getenv('REDDIT_CLIENT_SECRET', 'demo'),
        'twitter_bearer_token': os.getenv('TWITTER_BEARER_TOKEN', '')
    }
    
    predictor = MarketPredictionEnsemble(config)
    await predictor.__aenter__()
    logger.info("Predictor initialized")


def create_app():
    """Create and configure the Flask app"""
    global loop
    
    # Create event loop for async operations
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    # Initialize predictor
    loop.run_until_complete(init_predictor())
    
    return app


# Example HTML frontend
@app.route('/')
def index():
    """Serve simple HTML frontend"""
    return '''
<!DOCTYPE html>
<html>
<head>
    <title>AI Market Prediction API</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; }
        .endpoint { background: #f0f0f0; padding: 10px; margin: 10px 0; }
        code { background: #e0e0e0; padding: 2px 5px; }
        .method { color: #007bff; font-weight: bold; }
    </style>
</head>
<body>
    <h1>AI Market Prediction API</h1>
    <p>RESTful API for market predictions using ensemble AI system.</p>
    
    <h2>Available Endpoints:</h2>
    
    <div class="endpoint">
        <span class="method">GET</span> <code>/health</code>
        <p>Health check endpoint</p>
    </div>
    
    <div class="endpoint">
        <span class="method">GET</span> <code>/predict/{symbol}</code>
        <p>Get prediction for a specific symbol</p>
        <p>Query params: keywords (comma-separated), personality (filter)</p>
        <p>Example: <code>/predict/AAPL?keywords=iPhone,earnings&personality=technical_analyst</code></p>
    </div>
    
    <div class="endpoint">
        <span class="method">POST</span> <code>/predict/batch</code>
        <p>Get predictions for multiple symbols</p>
        <p>Body: <code>{"symbols": ["AAPL", "GOOGL"], "keywords": {"AAPL": ["iPhone"]}}</code></p>
    </div>
    
    <div class="endpoint">
        <span class="method">GET</span> <code>/report/{symbol}</code>
        <p>Get formatted markdown report for a symbol</p>
    </div>
    
    <div class="endpoint">
        <span class="method">GET</span> <code>/personalities</code>
        <p>Get list of available trading personalities</p>
    </div>
    
    <div class="endpoint">
        <span class="method">GET</span> <code>/sentiments</code>
        <p>Get list of possible sentiment values</p>
    </div>
    
    <h2>Example Usage:</h2>
    <pre>
# Get prediction for Apple
curl http://localhost:5000/predict/AAPL

# Get batch predictions
curl -X POST http://localhost:5000/predict/batch \
  -H "Content-Type: application/json" \
  -d '{"symbols": ["AAPL", "GOOGL", "BTC"]}'

# Get prediction with specific personality
curl http://localhost:5000/predict/TSLA?personality=aggressive_bull
    </pre>
    
    <h2>Configuration:</h2>
    <p>Set environment variables for API keys:</p>
    <ul>
        <li>ALPHA_VANTAGE_KEY</li>
        <li>NEWSAPI_KEY</li>
        <li>REDDIT_CLIENT_ID</li>
        <li>REDDIT_CLIENT_SECRET</li>
        <li>TWITTER_BEARER_TOKEN (optional)</li>
    </ul>
</body>
</html>
    '''


if __name__ == '__main__':
    app = create_app()
    app.run(host='0.0.0.0', port=5000, debug=True)