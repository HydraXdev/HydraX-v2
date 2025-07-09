# correlation_visualizer.py
# Visualization tools for cross-asset correlation analysis

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple
import json
from datetime import datetime

class CorrelationVisualizer:
    """Generate visual representations of correlation data for web display"""
    
    @staticmethod
    def generate_correlation_heatmap_data(correlation_matrix: pd.DataFrame) -> Dict:
        """Generate data for correlation heatmap visualization"""
        
        if correlation_matrix is None or correlation_matrix.empty:
            return {
                'status': 'no_data',
                'message': 'No correlation data available'
            }
        
        # Convert correlation matrix to nested list format
        assets = correlation_matrix.columns.tolist()
        values = correlation_matrix.values.tolist()
        
        # Create heatmap data
        heatmap_data = []
        for i, asset1 in enumerate(assets):
            for j, asset2 in enumerate(assets):
                heatmap_data.append({
                    'x': asset2,
                    'y': asset1,
                    'value': round(values[i][j], 3),
                    'color': CorrelationVisualizer._get_correlation_color(values[i][j])
                })
        
        return {
            'status': 'success',
            'assets': assets,
            'data': heatmap_data,
            'timestamp': datetime.now().isoformat()
        }
    
    @staticmethod
    def _get_correlation_color(value: float) -> str:
        """Get color for correlation value"""
        if value >= 0.8:
            return '#006400'  # Dark green
        elif value >= 0.5:
            return '#228B22'  # Forest green
        elif value >= 0.2:
            return '#90EE90'  # Light green
        elif value >= -0.2:
            return '#FFFFE0'  # Light yellow (neutral)
        elif value >= -0.5:
            return '#FFB6C1'  # Light red
        elif value >= -0.8:
            return '#DC143C'  # Crimson
        else:
            return '#8B0000'  # Dark red
    
    @staticmethod
    def generate_network_graph_data(correlations: List[Dict], threshold: float = 0.5) -> Dict:
        """Generate network graph data for correlation visualization"""
        
        # Build nodes and edges
        nodes = set()
        edges = []
        
        for corr in correlations:
            if abs(corr['correlation']) >= threshold:
                # Extract assets from pair string (e.g., "EURUSD/GOLD")
                assets = corr['pair'].split('/')
                nodes.add(assets[0])
                nodes.add(assets[1])
                
                edges.append({
                    'source': assets[0],
                    'target': assets[1],
                    'value': abs(corr['correlation']),
                    'correlation': corr['correlation'],
                    'type': corr['direction'],
                    'strength': corr['strength']
                })
        
        # Convert nodes to list with additional properties
        node_list = []
        for node in nodes:
            node_list.append({
                'id': node,
                'name': node,
                'group': CorrelationVisualizer._get_asset_group(node)
            })
        
        return {
            'nodes': node_list,
            'edges': edges,
            'threshold': threshold
        }
    
    @staticmethod
    def _get_asset_group(asset: str) -> str:
        """Determine asset group for visualization"""
        forex_pairs = ['EUR', 'USD', 'GBP', 'JPY', 'CHF', 'AUD', 'NZD', 'CAD']
        indices = ['SPX', 'NDX', 'DJI', 'DAX', 'FTSE', 'NKY', 'HSI']
        commodities = ['GOLD', 'SILVER', 'OIL', 'COPPER', 'WHEAT', 'CORN']
        bonds = ['US10Y', 'US2Y', 'BUND', 'JGB', 'GILT']
        
        # Check if it's a forex pair
        for currency in forex_pairs:
            if currency in asset:
                return 'forex'
        
        if asset in indices:
            return 'index'
        elif asset in commodities:
            return 'commodity'
        elif asset in bonds:
            return 'bond'
        else:
            return 'other'
    
    @staticmethod
    def generate_divergence_chart_data(divergences: List[Dict]) -> Dict:
        """Generate chart data for divergence visualization"""
        
        chart_data = []
        
        for div in divergences:
            chart_data.append({
                'assets': ' vs '.join(div['assets']),
                'severity': div['severity'],
                'type': div['divergence_type'],
                'confidence': div['confidence'] * 100,  # Convert to percentage
                'resolution': div['expected_resolution']
            })
        
        # Sort by severity
        chart_data.sort(key=lambda x: x['severity'], reverse=True)
        
        return {
            'data': chart_data[:10],  # Top 10 divergences
            'timestamp': datetime.now().isoformat()
        }
    
    @staticmethod
    def generate_risk_sentiment_gauge_data(risk_sentiment: str, 
                                         risk_metrics: Dict) -> Dict:
        """Generate gauge chart data for risk sentiment"""
        
        # Convert sentiment to numerical value
        sentiment_values = {
            'risk_on': 75,
            'risk_off': 25,
            'neutral': 50,
            'mixed': 50
        }
        
        gauge_value = sentiment_values.get(risk_sentiment, 50)
        
        # Add some variation based on additional metrics
        if 'volatility' in risk_metrics:
            if risk_metrics['volatility'] > 20:
                gauge_value -= 10  # High volatility = more risk-off
                
        return {
            'value': gauge_value,
            'sentiment': risk_sentiment,
            'zones': [
                {'from': 0, 'to': 30, 'color': '#DC143C', 'label': 'Risk Off'},
                {'from': 30, 'to': 70, 'color': '#FFD700', 'label': 'Neutral'},
                {'from': 70, 'to': 100, 'color': '#228B22', 'label': 'Risk On'}
            ],
            'timestamp': datetime.now().isoformat()
        }
    
    @staticmethod
    def generate_correlation_timeline_data(correlation_history: Dict[str, List]) -> Dict:
        """Generate timeline data for correlation evolution"""
        
        timeline_data = []
        
        for pair, history in correlation_history.items():
            if len(history) > 0:
                series_data = []
                for point in history:
                    series_data.append({
                        'timestamp': point['timestamp'].isoformat(),
                        'value': point['correlation']
                    })
                
                timeline_data.append({
                    'name': pair,
                    'data': series_data
                })
        
        return {
            'series': timeline_data,
            'timestamp': datetime.now().isoformat()
        }
    
    @staticmethod
    def generate_trading_signals_table(analysis: Dict) -> List[Dict]:
        """Generate trading signals table data"""
        
        signals = []
        
        # Dollar-based signals
        if 'dollar_analysis' in analysis and analysis['dollar_analysis'].get('signal'):
            signals.append({
                'asset': 'USD Index',
                'signal': analysis['dollar_analysis']['signal'],
                'strength': 'High' if 'strong' in analysis['dollar_analysis']['signal'] else 'Medium',
                'timeframe': 'Medium Term',
                'rationale': f"DXY trend: {analysis['dollar_analysis'].get('trend', 'N/A')}"
            })
        
        # Commodity currency signals
        if 'commodity_currency_signals' in analysis:
            for currency, data in analysis['commodity_currency_signals'].items():
                if data['signal'] != 'neutral':
                    signals.append({
                        'asset': currency,
                        'signal': data['signal'],
                        'strength': 'High' if 'strong' in data['signal'] else 'Medium',
                        'timeframe': 'Short-Medium Term',
                        'rationale': f"Commodity correlation: {data['strength']:.2f}"
                    })
        
        # Risk sentiment-based signals
        if 'trading_bias' in analysis:
            bias = analysis['trading_bias']
            if bias['forex']:
                signals.append({
                    'asset': 'Forex Pairs',
                    'signal': bias['forex'],
                    'strength': 'Medium',
                    'timeframe': 'Varies',
                    'rationale': f"Risk sentiment: {analysis.get('risk_sentiment', 'N/A')}"
                })
        
        return signals
    
    @staticmethod
    def generate_correlation_strength_bars(correlations: List[Dict]) -> Dict:
        """Generate bar chart data for correlation strengths"""
        
        # Group by strength categories
        strength_counts = {
            'very_strong': 0,
            'strong': 0,
            'moderate': 0,
            'weak': 0
        }
        
        for corr in correlations:
            strength = corr.get('strength', 'weak')
            if strength in strength_counts:
                strength_counts[strength] += 1
        
        # Create bar chart data
        bar_data = []
        colors = {
            'very_strong': '#006400',
            'strong': '#228B22',
            'moderate': '#FFD700',
            'weak': '#FFA500'
        }
        
        for strength, count in strength_counts.items():
            bar_data.append({
                'category': strength.replace('_', ' ').title(),
                'count': count,
                'color': colors.get(strength, '#808080')
            })
        
        return {
            'data': bar_data,
            'total': len(correlations),
            'timestamp': datetime.now().isoformat()
        }
    
    @staticmethod
    def generate_market_overview_cards(analysis: Dict) -> List[Dict]:
        """Generate overview cards for dashboard"""
        
        cards = []
        
        # Risk Sentiment Card
        cards.append({
            'title': 'Market Risk Sentiment',
            'value': analysis.get('risk_sentiment', 'Unknown').replace('_', ' ').title(),
            'icon': 'shield',
            'color': '#228B22' if 'risk_on' in analysis.get('risk_sentiment', '') else '#DC143C',
            'trend': 'neutral'
        })
        
        # Dollar Strength Card
        if 'dollar_analysis' in analysis and analysis['dollar_analysis'].get('current_value'):
            dollar_data = analysis['dollar_analysis']
            cards.append({
                'title': 'Dollar Index',
                'value': f"{dollar_data['current_value']:.2f}",
                'icon': 'dollar',
                'color': '#1E90FF',
                'trend': 'up' if dollar_data.get('momentum_pct', 0) > 0 else 'down',
                'change': f"{dollar_data.get('momentum_pct', 0):.2f}%"
            })
        
        # Divergences Card
        divergence_count = len(analysis.get('divergences', []))
        cards.append({
            'title': 'Active Divergences',
            'value': str(divergence_count),
            'icon': 'divergence',
            'color': '#FF6347' if divergence_count > 3 else '#32CD32',
            'trend': 'neutral',
            'subtitle': 'Intermarket divergences detected'
        })
        
        # Correlation Strength Card
        strong_correlations = len([c for c in analysis.get('strongest_correlations', []) 
                                 if abs(c.get('correlation', 0)) > 0.7])
        cards.append({
            'title': 'Strong Correlations',
            'value': str(strong_correlations),
            'icon': 'link',
            'color': '#9370DB',
            'trend': 'neutral',
            'subtitle': 'Above 0.7 threshold'
        })
        
        return cards

# HTML template for visualization
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Cross-Asset Correlation Dashboard</title>
    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
    <style>
        body {
            font-family: Arial, sans-serif;
            background-color: #f0f0f0;
            margin: 0;
            padding: 20px;
        }
        .dashboard {
            max-width: 1400px;
            margin: 0 auto;
        }
        .header {
            background-color: #2c3e50;
            color: white;
            padding: 20px;
            border-radius: 8px;
            margin-bottom: 20px;
        }
        .cards-container {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        .card {
            background-color: white;
            border-radius: 8px;
            padding: 20px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .card-title {
            font-size: 14px;
            color: #7f8c8d;
            margin-bottom: 10px;
        }
        .card-value {
            font-size: 28px;
            font-weight: bold;
            margin-bottom: 5px;
        }
        .chart-container {
            background-color: white;
            border-radius: 8px;
            padding: 20px;
            margin-bottom: 20px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .chart-title {
            font-size: 18px;
            font-weight: bold;
            margin-bottom: 15px;
            color: #2c3e50;
        }
        .table-container {
            background-color: white;
            border-radius: 8px;
            padding: 20px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            overflow-x: auto;
        }
        table {
            width: 100%;
            border-collapse: collapse;
        }
        th, td {
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }
        th {
            background-color: #f8f9fa;
            font-weight: bold;
        }
        .positive { color: #27ae60; }
        .negative { color: #e74c3c; }
        .neutral { color: #95a5a6; }
    </style>
</head>
<body>
    <div class="dashboard">
        <div class="header">
            <h1>Cross-Asset Correlation Dashboard</h1>
            <p>Real-time analysis of market correlations and trading signals</p>
        </div>
        
        <div class="cards-container" id="overview-cards"></div>
        
        <div class="chart-container">
            <div class="chart-title">Correlation Heatmap</div>
            <div id="heatmap"></div>
        </div>
        
        <div class="chart-container">
            <div class="chart-title">Risk Sentiment Gauge</div>
            <div id="risk-gauge"></div>
        </div>
        
        <div class="chart-container">
            <div class="chart-title">Intermarket Divergences</div>
            <div id="divergence-chart"></div>
        </div>
        
        <div class="table-container">
            <div class="chart-title">Trading Signals</div>
            <table id="signals-table">
                <thead>
                    <tr>
                        <th>Asset</th>
                        <th>Signal</th>
                        <th>Strength</th>
                        <th>Timeframe</th>
                        <th>Rationale</th>
                    </tr>
                </thead>
                <tbody id="signals-tbody"></tbody>
            </table>
        </div>
    </div>
    
    <script>
        // Dashboard data will be injected here
        const dashboardData = {DASHBOARD_DATA};
        
        // Render overview cards
        function renderOverviewCards(cards) {
            const container = document.getElementById('overview-cards');
            cards.forEach(card => {
                const cardHtml = `
                    <div class="card">
                        <div class="card-title">${card.title}</div>
                        <div class="card-value" style="color: ${card.color}">${card.value}</div>
                        ${card.subtitle ? `<div>${card.subtitle}</div>` : ''}
                        ${card.change ? `<div>${card.change}</div>` : ''}
                    </div>
                `;
                container.innerHTML += cardHtml;
            });
        }
        
        // Render correlation heatmap
        function renderHeatmap(data) {
            if (data.status !== 'success') return;
            
            const trace = {
                x: data.assets,
                y: data.assets,
                z: data.data.map(d => d.value),
                type: 'heatmap',
                colorscale: [
                    [0, '#8B0000'],
                    [0.25, '#DC143C'],
                    [0.5, '#FFFFE0'],
                    [0.75, '#228B22'],
                    [1, '#006400']
                ],
                zmin: -1,
                zmax: 1
            };
            
            const layout = {
                height: 500,
                xaxis: { tickangle: -45 },
                yaxis: { tickangle: 0 }
            };
            
            Plotly.newPlot('heatmap', [trace], layout);
        }
        
        // Initialize dashboard
        renderOverviewCards(dashboardData.overview_cards);
        renderHeatmap(dashboardData.heatmap_data);
        
        // Render signals table
        const tbody = document.getElementById('signals-tbody');
        dashboardData.signals.forEach(signal => {
            const row = tbody.insertRow();
            row.innerHTML = `
                <td>${signal.asset}</td>
                <td class="${signal.signal.includes('bullish') ? 'positive' : signal.signal.includes('bearish') ? 'negative' : 'neutral'}">
                    ${signal.signal}
                </td>
                <td>${signal.strength}</td>
                <td>${signal.timeframe}</td>
                <td>${signal.rationale}</td>
            `;
        });
    </script>
</body>
</html>
"""

def generate_dashboard_html(analysis: Dict, correlation_matrix: pd.DataFrame) -> str:
    """Generate complete HTML dashboard"""
    
    visualizer = CorrelationVisualizer()
    
    # Generate all visualization data
    dashboard_data = {
        'overview_cards': visualizer.generate_market_overview_cards(analysis),
        'heatmap_data': visualizer.generate_correlation_heatmap_data(correlation_matrix),
        'risk_gauge': visualizer.generate_risk_sentiment_gauge_data(
            analysis.get('risk_sentiment', 'neutral'), {}
        ),
        'divergences': visualizer.generate_divergence_chart_data(
            analysis.get('divergences', [])
        ),
        'signals': visualizer.generate_trading_signals_table(analysis)
    }
    
    # Inject data into HTML template
    html = HTML_TEMPLATE.replace(
        '{DASHBOARD_DATA}', 
        json.dumps(dashboard_data, default=str)
    )
    
    return html