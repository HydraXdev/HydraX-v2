# correlation_router.py
# Flask routes for cross-asset correlation system

from flask import Blueprint, jsonify, request, render_template_string
from datetime import datetime
import logging
from typing import Dict, Any

from .strategies.cross_asset_correlation import (
    CrossAssetCorrelationSystem,
    AssetData,
    AssetClass
)
from .strategies.correlation_visualizer import (
    CorrelationVisualizer,
    generate_dashboard_html
)

logger = logging.getLogger(__name__)

# Create Blueprint
correlation_bp = Blueprint('correlation', __name__, url_prefix='/api/correlation')

# Initialize correlation system
correlation_system = CrossAssetCorrelationSystem()

@correlation_bp.route('/update', methods=['POST'])
def update_market_data():
    """Update market data endpoint"""
    try:
        data = request.json
        
        # Validate required fields
        required_fields = ['symbol', 'asset_class', 'price']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'success': False,
                    'error': f'Missing required field: {field}'
                }), 400
        
        # Create AssetData object
        asset_data = AssetData(
            symbol=data['symbol'],
            asset_class=AssetClass(data['asset_class']),
            price=float(data['price']),
            change_pct=float(data.get('change_pct', 0)),
            volume=float(data.get('volume', 0)),
            timestamp=datetime.now(),
            additional_data=data.get('additional_data', {})
        )
        
        # Update correlation system
        correlation_system.update_market_data(asset_data)
        
        return jsonify({
            'success': True,
            'message': f'Updated data for {data["symbol"]}'
        })
        
    except Exception as e:
        logger.error(f"Error updating market data: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@correlation_bp.route('/analysis', methods=['GET'])
def get_analysis():
    """Get comprehensive correlation analysis"""
    try:
        analysis = correlation_system.get_comprehensive_analysis()
        
        # Convert any datetime objects to strings
        def serialize_analysis(obj):
            if isinstance(obj, datetime):
                return obj.isoformat()
            elif isinstance(obj, dict):
                return {k: serialize_analysis(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [serialize_analysis(item) for item in obj]
            else:
                return obj
        
        serialized_analysis = serialize_analysis(analysis)
        
        return jsonify({
            'success': True,
            'data': serialized_analysis
        })
        
    except Exception as e:
        logger.error(f"Error getting analysis: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@correlation_bp.route('/pair/<symbol>', methods=['GET'])
def get_pair_analysis(symbol: str):
    """Get analysis for specific trading pair"""
    try:
        analysis = correlation_system.get_pair_specific_analysis(symbol.upper())
        
        return jsonify({
            'success': True,
            'data': analysis
        })
        
    except Exception as e:
        logger.error(f"Error getting pair analysis: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@correlation_bp.route('/correlations/matrix', methods=['GET'])
def get_correlation_matrix():
    """Get current correlation matrix"""
    try:
        # Get period from query params
        period = request.args.get('period', 50, type=int)
        
        # Calculate correlation matrix
        matrix = correlation_system.correlation_calculator.calculate_correlation_matrix(period)
        
        if matrix is None:
            return jsonify({
                'success': False,
                'error': 'Insufficient data for correlation calculation'
            }), 400
        
        # Convert to JSON-serializable format
        matrix_data = {
            'assets': matrix.columns.tolist(),
            'values': matrix.values.tolist(),
            'period': period
        }
        
        return jsonify({
            'success': True,
            'data': matrix_data
        })
        
    except Exception as e:
        logger.error(f"Error getting correlation matrix: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@correlation_bp.route('/divergences', methods=['GET'])
def get_divergences():
    """Get current market divergences"""
    try:
        divergences = correlation_system.divergence_detector.detect_divergences()
        
        # Convert to serializable format
        divergence_data = []
        for div in divergences:
            divergence_data.append({
                'assets': div.assets,
                'divergence_type': div.divergence_type,
                'severity': div.severity,
                'expected_resolution': div.expected_resolution,
                'confidence': div.confidence
            })
        
        return jsonify({
            'success': True,
            'data': divergence_data
        })
        
    except Exception as e:
        logger.error(f"Error getting divergences: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@correlation_bp.route('/dollar-index', methods=['GET'])
def get_dollar_index():
    """Get Dollar Index analysis"""
    try:
        analysis = correlation_system.dollar_analyzer.analyze_dollar_strength()
        
        return jsonify({
            'success': True,
            'data': analysis
        })
        
    except Exception as e:
        logger.error(f"Error getting dollar index: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@correlation_bp.route('/risk-sentiment', methods=['GET'])
def get_risk_sentiment():
    """Get current risk sentiment"""
    try:
        sentiment = correlation_system.equity_detector.calculate_risk_sentiment()
        sector_signals = correlation_system.equity_detector.get_sector_rotation_signals()
        
        return jsonify({
            'success': True,
            'data': {
                'sentiment': sentiment.value,
                'sector_signals': sector_signals
            }
        })
        
    except Exception as e:
        logger.error(f"Error getting risk sentiment: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@correlation_bp.route('/commodity-currencies', methods=['GET'])
def get_commodity_currencies():
    """Get commodity currency correlations"""
    try:
        signals = correlation_system.commodity_analyzer.get_commodity_currency_signals()
        
        return jsonify({
            'success': True,
            'data': signals
        })
        
    except Exception as e:
        logger.error(f"Error getting commodity currencies: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@correlation_bp.route('/dashboard', methods=['GET'])
def correlation_dashboard():
    """Render correlation dashboard HTML"""
    try:
        # Get current analysis
        analysis = correlation_system.get_comprehensive_analysis()
        
        # Get correlation matrix
        matrix = correlation_system.correlation_calculator.calculate_correlation_matrix()
        
        # Generate HTML dashboard
        html = generate_dashboard_html(analysis, matrix)
        
        return render_template_string(html)
        
    except Exception as e:
        logger.error(f"Error rendering dashboard: {str(e)}")
        return f"<h1>Error loading dashboard</h1><p>{str(e)}</p>", 500

@correlation_bp.route('/visualizations/heatmap', methods=['GET'])
def get_heatmap_data():
    """Get correlation heatmap visualization data"""
    try:
        matrix = correlation_system.correlation_calculator.calculate_correlation_matrix()
        
        if matrix is None:
            return jsonify({
                'success': False,
                'error': 'No correlation data available'
            }), 400
        
        visualizer = CorrelationVisualizer()
        heatmap_data = visualizer.generate_correlation_heatmap_data(matrix)
        
        return jsonify({
            'success': True,
            'data': heatmap_data
        })
        
    except Exception as e:
        logger.error(f"Error getting heatmap data: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@correlation_bp.route('/visualizations/network', methods=['GET'])
def get_network_data():
    """Get correlation network visualization data"""
    try:
        # Get threshold from query params
        threshold = request.args.get('threshold', 0.5, type=float)
        
        # Get strongest correlations
        correlations = correlation_system.correlation_calculator.get_strongest_correlations(threshold)
        
        # Convert to dict format
        corr_dicts = []
        for corr in correlations:
            corr_dicts.append({
                'pair': f"{corr.asset1}/{corr.asset2}",
                'correlation': corr.correlation,
                'strength': corr.strength,
                'direction': corr.direction
            })
        
        visualizer = CorrelationVisualizer()
        network_data = visualizer.generate_network_graph_data(corr_dicts, threshold)
        
        return jsonify({
            'success': True,
            'data': network_data
        })
        
    except Exception as e:
        logger.error(f"Error getting network data: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@correlation_bp.route('/predictions/<asset1>/<asset2>', methods=['GET'])
def get_correlation_prediction(asset1: str, asset2: str):
    """Get correlation prediction for asset pair"""
    try:
        # Get horizon from query params
        horizon = request.args.get('horizon', 5, type=int)
        
        prediction = correlation_system.predictive_model.predict_correlation_change(
            asset1.upper(), 
            asset2.upper(), 
            horizon
        )
        
        return jsonify({
            'success': True,
            'data': prediction
        })
        
    except Exception as e:
        logger.error(f"Error getting prediction: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@correlation_bp.route('/regime-changes', methods=['GET'])
def get_regime_changes():
    """Get correlation regime changes"""
    try:
        regime_analysis = correlation_system.predictive_model.detect_correlation_regime_change()
        
        return jsonify({
            'success': True,
            'data': regime_analysis
        })
        
    except Exception as e:
        logger.error(f"Error getting regime changes: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# Health check endpoint
@correlation_bp.route('/health', methods=['GET'])
def health_check():
    """Health check for correlation system"""
    return jsonify({
        'success': True,
        'status': 'operational',
        'timestamp': datetime.now().isoformat()
    })

# Error handlers
@correlation_bp.errorhandler(404)
def not_found(error):
    return jsonify({
        'success': False,
        'error': 'Endpoint not found'
    }), 404

@correlation_bp.errorhandler(500)
def internal_error(error):
    return jsonify({
        'success': False,
        'error': 'Internal server error'
    }), 500