"""
Options Flow Analyzer

Analyzes options trading data to detect market sentiment and unusual activity.
Tracks large trades, unusual volume, and options flow patterns.
"""

import os
from typing import List, Dict, Tuple, Optional
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from dataclasses import dataclass
import logging
import aiohttp
import asyncio
from collections import defaultdict
import yfinance as yf

logger = logging.getLogger(__name__)


@dataclass
class OptionsFlow:
    """Options flow data structure"""
    timestamp: datetime
    symbol: str
    strike: float
    expiry: datetime
    option_type: str  # 'call' or 'put'
    volume: int
    open_interest: int
    bid: float
    ask: float
    last_price: float
    implied_volatility: float
    delta: Optional[float] = None
    gamma: Optional[float] = None
    theta: Optional[float] = None
    vega: Optional[float] = None
    

@dataclass
class UnusualOption:
    """Unusual options activity data"""
    symbol: str
    strike: float
    expiry: datetime
    option_type: str
    volume: int
    open_interest: int
    volume_oi_ratio: float
    price: float
    total_value: float
    implied_volatility: float
    unusual_type: str  # 'volume_spike', 'large_trade', 'sweep', 'block'
    sentiment: str  # 'bullish', 'bearish', 'neutral'
    

class OptionsFlowAnalyzer:
    """
    Analyzes options flow data for sentiment and unusual activity
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize options flow analyzer
        
        Args:
            api_key: API key for options data provider
        """
        self.api_key = api_key or os.getenv("OPTIONS_API_KEY")
        
        # Thresholds for unusual activity
        self.thresholds = {
            'volume_spike_multiplier': 5.0,  # Volume > 5x average
            'large_trade_value': 100000,  # $100k+ trades
            'high_volume_oi_ratio': 5.0,  # Volume > 5x OI
            'sweep_time_window': 300,  # 5 minutes for sweep detection
            'block_min_contracts': 500,  # Minimum for block trades
            'unusual_iv_percentile': 90  # Top 10% IV
        }
        
        # Track historical data for comparisons
        self.historical_volume = defaultdict(lambda: defaultdict(list))
        self.historical_iv = defaultdict(list)
        
    async def analyze_options_flow(
        self,
        symbols: Optional[List[str]] = None,
        lookback_hours: int = 24
    ) -> Dict[str, any]:
        """
        Analyze overall options flow sentiment
        
        Args:
            symbols: List of symbols to analyze (None for market-wide)
            lookback_hours: Hours to look back
            
        Returns:
            Options flow analysis results
        """
        try:
            # Get options flow data
            if symbols:
                flow_data = await self._get_options_flow(symbols, lookback_hours)
            else:
                # Get most active options
                flow_data = await self._get_market_flow(lookback_hours)
            
            # Analyze flow
            results = {
                'timestamp': datetime.utcnow().isoformat(),
                'total_volume': sum(f.volume for f in flow_data),
                'call_put_ratio': self._calculate_call_put_ratio(flow_data),
                'sentiment': self._calculate_flow_sentiment(flow_data),
                'unusual_activity': await self._detect_unusual_activity(flow_data),
                'smart_money_flow': self._analyze_smart_money(flow_data),
                'volatility_skew': self._analyze_volatility_skew(flow_data),
                'sector_flow': self._analyze_sector_flow(flow_data),
                'expiry_analysis': self._analyze_expiry_distribution(flow_data)
            }
            
            return results
            
        except Exception as e:
            logger.error(f"Error analyzing options flow: {e}")
            return {}
    
    async def analyze_symbol_options(
        self,
        symbol: str,
        lookback_hours: int = 24
    ) -> Dict[str, any]:
        """
        Analyze options flow for specific symbol
        
        Args:
            symbol: Stock symbol
            lookback_hours: Hours to look back
            
        Returns:
            Symbol-specific options analysis
        """
        try:
            # Get options chain
            options_chain = await self._get_options_chain(symbol)
            
            # Get recent flow
            flow_data = await self._get_options_flow([symbol], lookback_hours)
            
            # Get stock info for context
            stock_info = self._get_stock_context(symbol)
            
            # Analyze
            results = {
                'symbol': symbol,
                'timestamp': datetime.utcnow().isoformat(),
                'stock_price': stock_info.get('price', 0),
                'options_volume': sum(f.volume for f in flow_data),
                'call_put_ratio': self._calculate_call_put_ratio(flow_data),
                'sentiment': self._determine_options_sentiment(flow_data, stock_info),
                'unusual_strikes': self._find_unusual_strikes(flow_data, options_chain),
                'max_pain': self._calculate_max_pain(options_chain),
                'gamma_exposure': self._calculate_gamma_exposure(options_chain, stock_info),
                'put_call_skew': self._calculate_put_call_skew(options_chain),
                'smart_money_strikes': self._identify_smart_money_strikes(flow_data),
                'volatility_term_structure': self._analyze_term_structure(options_chain)
            }
            
            return results
            
        except Exception as e:
            logger.error(f"Error analyzing {symbol} options: {e}")
            return {'symbol': symbol, 'error': str(e)}
    
    async def _get_options_flow(
        self,
        symbols: List[str],
        hours_back: int
    ) -> List[OptionsFlow]:
        """Get options flow data for symbols"""
        # This would connect to a real options data provider
        # For now, using yfinance as example
        flow_data = []
        
        for symbol in symbols:
            try:
                ticker = yf.Ticker(symbol)
                
                # Get options dates
                exp_dates = ticker.options
                
                for exp_date in exp_dates[:3]:  # Next 3 expiries
                    # Get options chain
                    opt_chain = ticker.option_chain(exp_date)
                    
                    # Process calls
                    for _, call in opt_chain.calls.iterrows():
                        if call['volume'] > 0:
                            flow = OptionsFlow(
                                timestamp=datetime.utcnow(),
                                symbol=symbol,
                                strike=call['strike'],
                                expiry=datetime.strptime(exp_date, '%Y-%m-%d'),
                                option_type='call',
                                volume=int(call['volume']),
                                open_interest=int(call['openInterest']),
                                bid=call['bid'],
                                ask=call['ask'],
                                last_price=call['lastPrice'],
                                implied_volatility=call['impliedVolatility']
                            )
                            flow_data.append(flow)
                    
                    # Process puts
                    for _, put in opt_chain.puts.iterrows():
                        if put['volume'] > 0:
                            flow = OptionsFlow(
                                timestamp=datetime.utcnow(),
                                symbol=symbol,
                                strike=put['strike'],
                                expiry=datetime.strptime(exp_date, '%Y-%m-%d'),
                                option_type='put',
                                volume=int(put['volume']),
                                open_interest=int(put['openInterest']),
                                bid=put['bid'],
                                ask=put['ask'],
                                last_price=put['lastPrice'],
                                implied_volatility=put['impliedVolatility']
                            )
                            flow_data.append(flow)
                            
            except Exception as e:
                logger.error(f"Error getting options for {symbol}: {e}")
        
        return flow_data
    
    async def _get_market_flow(self, hours_back: int) -> List[OptionsFlow]:
        """Get market-wide options flow"""
        # Get most active options from major indices and stocks
        symbols = ['SPY', 'QQQ', 'IWM', 'AAPL', 'TSLA', 'NVDA', 'AMD', 'MSFT']
        return await self._get_options_flow(symbols, hours_back)
    
    async def _get_options_chain(self, symbol: str) -> pd.DataFrame:
        """Get full options chain for symbol"""
        try:
            ticker = yf.Ticker(symbol)
            exp_dates = ticker.options
            
            all_options = []
            
            for exp_date in exp_dates:
                opt_chain = ticker.option_chain(exp_date)
                
                # Add expiry date to dataframes
                opt_chain.calls['expiry'] = exp_date
                opt_chain.calls['type'] = 'call'
                opt_chain.puts['expiry'] = exp_date
                opt_chain.puts['type'] = 'put'
                
                all_options.append(opt_chain.calls)
                all_options.append(opt_chain.puts)
            
            return pd.concat(all_options, ignore_index=True)
            
        except Exception as e:
            logger.error(f"Error getting options chain: {e}")
            return pd.DataFrame()
    
    def _calculate_call_put_ratio(self, flow_data: List[OptionsFlow]) -> Dict[str, float]:
        """Calculate call/put ratios"""
        call_volume = sum(f.volume for f in flow_data if f.option_type == 'call')
        put_volume = sum(f.volume for f in flow_data if f.option_type == 'put')
        
        call_value = sum(
            f.volume * f.last_price * 100 
            for f in flow_data 
            if f.option_type == 'call'
        )
        put_value = sum(
            f.volume * f.last_price * 100 
            for f in flow_data 
            if f.option_type == 'put'
        )
        
        return {
            'volume_ratio': call_volume / put_volume if put_volume > 0 else 0,
            'value_ratio': call_value / put_value if put_value > 0 else 0,
            'call_volume': call_volume,
            'put_volume': put_volume,
            'call_value': call_value,
            'put_value': put_value
        }
    
    def _calculate_flow_sentiment(self, flow_data: List[OptionsFlow]) -> Dict[str, any]:
        """Calculate sentiment from options flow"""
        if not flow_data:
            return {'sentiment': 'neutral', 'score': 0}
        
        # Weight by volume and moneyness
        bullish_score = 0
        bearish_score = 0
        
        for flow in flow_data:
            weight = flow.volume * flow.last_price
            
            if flow.option_type == 'call':
                # Calls are generally bullish
                bullish_score += weight
                
                # OTM calls with high volume extra bullish
                if flow.volume > flow.open_interest * 2:
                    bullish_score += weight * 0.5
                    
            else:  # puts
                # Puts can be bearish or hedging
                if flow.volume > flow.open_interest * 3:
                    # High volume/OI ratio suggests directional bet
                    bearish_score += weight
                else:
                    # Could be hedging
                    bearish_score += weight * 0.5
        
        total_score = bullish_score + bearish_score
        if total_score == 0:
            return {'sentiment': 'neutral', 'score': 0}
        
        sentiment_score = (bullish_score - bearish_score) / total_score
        
        if sentiment_score > 0.2:
            sentiment = 'bullish'
        elif sentiment_score < -0.2:
            sentiment = 'bearish'
        else:
            sentiment = 'neutral'
        
        return {
            'sentiment': sentiment,
            'score': sentiment_score * 100,
            'bullish_flow': bullish_score,
            'bearish_flow': bearish_score
        }
    
    async def _detect_unusual_activity(
        self, 
        flow_data: List[OptionsFlow]
    ) -> List[UnusualOption]:
        """Detect unusual options activity"""
        unusual_options = []
        
        # Group by symbol and strike
        grouped = defaultdict(list)
        for flow in flow_data:
            key = (flow.symbol, flow.strike, flow.expiry, flow.option_type)
            grouped[key].append(flow)
        
        for (symbol, strike, expiry, opt_type), flows in grouped.items():
            # Aggregate metrics
            total_volume = sum(f.volume for f in flows)
            avg_oi = np.mean([f.open_interest for f in flows])
            avg_price = np.mean([f.last_price for f in flows])
            avg_iv = np.mean([f.implied_volatility for f in flows])
            
            # Check for unusual activity
            unusual_types = []
            
            # High volume relative to OI
            if avg_oi > 0 and total_volume > avg_oi * self.thresholds['high_volume_oi_ratio']:
                unusual_types.append('volume_spike')
            
            # Large dollar value
            total_value = total_volume * avg_price * 100
            if total_value > self.thresholds['large_trade_value']:
                unusual_types.append('large_trade')
            
            # Block trade detection
            if total_volume > self.thresholds['block_min_contracts']:
                unusual_types.append('block')
            
            # Create unusual option entry
            if unusual_types:
                sentiment = 'bullish' if opt_type == 'call' else 'bearish'
                
                unusual = UnusualOption(
                    symbol=symbol,
                    strike=strike,
                    expiry=expiry,
                    option_type=opt_type,
                    volume=total_volume,
                    open_interest=int(avg_oi),
                    volume_oi_ratio=total_volume / avg_oi if avg_oi > 0 else 0,
                    price=avg_price,
                    total_value=total_value,
                    implied_volatility=avg_iv,
                    unusual_type=', '.join(unusual_types),
                    sentiment=sentiment
                )
                unusual_options.append(unusual)
        
        # Sort by total value
        unusual_options.sort(key=lambda x: x.total_value, reverse=True)
        
        return unusual_options[:50]  # Top 50
    
    def _analyze_smart_money(self, flow_data: List[OptionsFlow]) -> Dict[str, any]:
        """Analyze smart money flow patterns"""
        smart_money_indicators = {
            'large_trades': [],
            'sweep_orders': [],
            'near_ask_trades': [],
            'high_delta_trades': []
        }
        
        for flow in flow_data:
            # Large trades
            trade_value = flow.volume * flow.last_price * 100
            if trade_value > 50000:  # $50k+
                smart_money_indicators['large_trades'].append({
                    'symbol': flow.symbol,
                    'strike': flow.strike,
                    'type': flow.option_type,
                    'value': trade_value
                })
            
            # Near ask trades (aggressive buying)
            if flow.ask > 0 and flow.last_price >= flow.ask * 0.95:
                smart_money_indicators['near_ask_trades'].append({
                    'symbol': flow.symbol,
                    'strike': flow.strike,
                    'type': flow.option_type
                })
        
        # Calculate smart money sentiment
        bullish_trades = sum(
            1 for t in smart_money_indicators['large_trades'] 
            if t['type'] == 'call'
        )
        bearish_trades = sum(
            1 for t in smart_money_indicators['large_trades'] 
            if t['type'] == 'put'
        )
        
        if bullish_trades + bearish_trades > 0:
            smart_sentiment = 'bullish' if bullish_trades > bearish_trades else 'bearish'
        else:
            smart_sentiment = 'neutral'
        
        return {
            'sentiment': smart_sentiment,
            'large_trade_count': len(smart_money_indicators['large_trades']),
            'total_smart_value': sum(t['value'] for t in smart_money_indicators['large_trades']),
            'aggressive_buying': len(smart_money_indicators['near_ask_trades'])
        }
    
    def _analyze_volatility_skew(self, flow_data: List[OptionsFlow]) -> Dict[str, float]:
        """Analyze implied volatility skew"""
        # Group by symbol
        symbol_ivs = defaultdict(lambda: {'calls': [], 'puts': []})
        
        for flow in flow_data:
            if flow.implied_volatility > 0:
                symbol_ivs[flow.symbol][
                    'calls' if flow.option_type == 'call' else 'puts'
                ].append(flow.implied_volatility)
        
        # Calculate skews
        skews = {}
        for symbol, ivs in symbol_ivs.items():
            if ivs['calls'] and ivs['puts']:
                call_iv = np.mean(ivs['calls'])
                put_iv = np.mean(ivs['puts'])
                skews[symbol] = {
                    'skew': put_iv - call_iv,
                    'call_iv': call_iv,
                    'put_iv': put_iv,
                    'sentiment': 'bearish' if put_iv > call_iv * 1.1 else 'neutral'
                }
        
        return skews
    
    def _analyze_sector_flow(self, flow_data: List[OptionsFlow]) -> Dict[str, any]:
        """Analyze flow by sector"""
        # This would map symbols to sectors
        # Simplified example
        sector_map = {
            'AAPL': 'Technology', 'MSFT': 'Technology', 'GOOGL': 'Technology',
            'JPM': 'Financials', 'BAC': 'Financials', 'GS': 'Financials',
            'XOM': 'Energy', 'CVX': 'Energy',
            'AMZN': 'Consumer', 'TSLA': 'Consumer',
            'SPY': 'Index', 'QQQ': 'Index', 'IWM': 'Index'
        }
        
        sector_flow = defaultdict(lambda: {
            'call_volume': 0, 'put_volume': 0, 'total_value': 0
        })
        
        for flow in flow_data:
            sector = sector_map.get(flow.symbol, 'Other')
            
            if flow.option_type == 'call':
                sector_flow[sector]['call_volume'] += flow.volume
            else:
                sector_flow[sector]['put_volume'] += flow.volume
            
            sector_flow[sector]['total_value'] += flow.volume * flow.last_price * 100
        
        # Calculate sector sentiments
        sector_sentiments = {}
        for sector, data in sector_flow.items():
            if data['put_volume'] > 0:
                ratio = data['call_volume'] / data['put_volume']
                if ratio > 1.5:
                    sentiment = 'bullish'
                elif ratio < 0.67:
                    sentiment = 'bearish'
                else:
                    sentiment = 'neutral'
            else:
                sentiment = 'bullish' if data['call_volume'] > 0 else 'neutral'
            
            sector_sentiments[sector] = {
                'sentiment': sentiment,
                'call_put_ratio': ratio if data['put_volume'] > 0 else 0,
                'total_flow': data['total_value']
            }
        
        return sector_sentiments
    
    def _analyze_expiry_distribution(self, flow_data: List[OptionsFlow]) -> Dict[str, any]:
        """Analyze distribution across expiries"""
        expiry_dist = defaultdict(lambda: {'volume': 0, 'calls': 0, 'puts': 0})
        
        for flow in flow_data:
            # Categorize by time to expiry
            days_to_expiry = (flow.expiry - datetime.now()).days
            
            if days_to_expiry <= 1:
                category = '0-1 days'
            elif days_to_expiry <= 7:
                category = '2-7 days'
            elif days_to_expiry <= 30:
                category = '8-30 days'
            elif days_to_expiry <= 90:
                category = '31-90 days'
            else:
                category = '90+ days'
            
            expiry_dist[category]['volume'] += flow.volume
            if flow.option_type == 'call':
                expiry_dist[category]['calls'] += flow.volume
            else:
                expiry_dist[category]['puts'] += flow.volume
        
        return dict(expiry_dist)
    
    def _get_stock_context(self, symbol: str) -> Dict[str, float]:
        """Get current stock price and context"""
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info
            
            return {
                'price': info.get('regularMarketPrice', 0),
                'change': info.get('regularMarketChangePercent', 0),
                'volume': info.get('regularMarketVolume', 0),
                'avg_volume': info.get('averageVolume', 0),
                'market_cap': info.get('marketCap', 0)
            }
        except:
            return {}
    
    def _determine_options_sentiment(
        self,
        flow_data: List[OptionsFlow],
        stock_info: Dict
    ) -> Dict[str, any]:
        """Determine sentiment considering stock context"""
        base_sentiment = self._calculate_flow_sentiment(flow_data)
        
        # Adjust for stock performance
        if stock_info.get('change', 0) > 2:
            # Stock up significantly, calls might be chasing
            if base_sentiment['sentiment'] == 'bullish':
                base_sentiment['confidence'] = 'moderate'
                base_sentiment['note'] = 'Calls may be chasing rally'
        elif stock_info.get('change', 0) < -2:
            # Stock down, puts might be late
            if base_sentiment['sentiment'] == 'bearish':
                base_sentiment['confidence'] = 'moderate'
                base_sentiment['note'] = 'Puts may be late to decline'
        
        return base_sentiment
    
    def _find_unusual_strikes(
        self,
        flow_data: List[OptionsFlow],
        options_chain: pd.DataFrame
    ) -> List[Dict]:
        """Find strikes with unusual activity"""
        strike_activity = defaultdict(lambda: {'volume': 0, 'oi': 0})
        
        for flow in flow_data:
            key = (flow.strike, flow.option_type)
            strike_activity[key]['volume'] += flow.volume
            strike_activity[key]['oi'] = flow.open_interest
        
        unusual_strikes = []
        for (strike, opt_type), activity in strike_activity.items():
            if activity['oi'] > 0 and activity['volume'] > activity['oi'] * 3:
                unusual_strikes.append({
                    'strike': strike,
                    'type': opt_type,
                    'volume': activity['volume'],
                    'oi': activity['oi'],
                    'ratio': activity['volume'] / activity['oi']
                })
        
        return sorted(unusual_strikes, key=lambda x: x['ratio'], reverse=True)[:10]
    
    def _calculate_max_pain(self, options_chain: pd.DataFrame) -> Dict[str, float]:
        """Calculate max pain strike price"""
        if options_chain.empty:
            return {'max_pain': 0, 'total_oi': 0}
        
        # Get unique strikes
        strikes = sorted(options_chain['strike'].unique())
        
        max_pain_values = []
        
        for strike in strikes:
            call_pain = 0
            put_pain = 0
            
            # Calculate pain for calls
            calls = options_chain[
                (options_chain['type'] == 'call') & 
                (options_chain['strike'] < strike)
            ]
            for _, call in calls.iterrows():
                call_pain += (strike - call['strike']) * call['openInterest']
            
            # Calculate pain for puts
            puts = options_chain[
                (options_chain['type'] == 'put') & 
                (options_chain['strike'] > strike)
            ]
            for _, put in puts.iterrows():
                put_pain += (put['strike'] - strike) * put['openInterest']
            
            total_pain = call_pain + put_pain
            max_pain_values.append((strike, total_pain))
        
        # Find minimum pain
        if max_pain_values:
            max_pain_strike = min(max_pain_values, key=lambda x: x[1])[0]
            total_oi = options_chain['openInterest'].sum()
        else:
            max_pain_strike = 0
            total_oi = 0
        
        return {
            'max_pain': max_pain_strike,
            'total_oi': total_oi
        }
    
    def _calculate_gamma_exposure(
        self,
        options_chain: pd.DataFrame,
        stock_info: Dict
    ) -> Dict[str, float]:
        """Calculate gamma exposure (simplified)"""
        if options_chain.empty or not stock_info.get('price'):
            return {'total_gamma': 0, 'net_gamma': 0}
        
        current_price = stock_info['price']
        
        # Simplified gamma calculation
        total_gamma = 0
        net_gamma = 0
        
        for _, option in options_chain.iterrows():
            # Approximate gamma for ATM options
            if abs(option['strike'] - current_price) / current_price < 0.1:
                gamma_estimate = option['openInterest'] * 100 * 0.05  # Simplified
                
                total_gamma += abs(gamma_estimate)
                if option['type'] == 'call':
                    net_gamma += gamma_estimate
                else:
                    net_gamma -= gamma_estimate
        
        return {
            'total_gamma': total_gamma,
            'net_gamma': net_gamma,
            'gamma_flip': current_price  # Simplified
        }
    
    def _calculate_put_call_skew(self, options_chain: pd.DataFrame) -> Dict[str, float]:
        """Calculate put/call IV skew"""
        if options_chain.empty:
            return {'skew': 0, 'sentiment': 'neutral'}
        
        # Get ATM options
        atm_calls = options_chain[
            options_chain['type'] == 'call'
        ]['impliedVolatility'].mean()
        
        atm_puts = options_chain[
            options_chain['type'] == 'put'
        ]['impliedVolatility'].mean()
        
        if atm_calls > 0:
            skew = (atm_puts - atm_calls) / atm_calls
        else:
            skew = 0
        
        # Interpret skew
        if skew > 0.1:
            sentiment = 'bearish'
        elif skew < -0.1:
            sentiment = 'bullish'
        else:
            sentiment = 'neutral'
        
        return {
            'skew': skew,
            'call_iv': atm_calls,
            'put_iv': atm_puts,
            'sentiment': sentiment
        }
    
    def _identify_smart_money_strikes(
        self, 
        flow_data: List[OptionsFlow]
    ) -> List[Dict]:
        """Identify strikes with potential smart money activity"""
        smart_strikes = []
        
        # Group by strike
        strike_data = defaultdict(lambda: {
            'volume': 0, 'value': 0, 'trades': []
        })
        
        for flow in flow_data:
            value = flow.volume * flow.last_price * 100
            
            # Look for large trades
            if value > 25000:  # $25k+
                strike_data[flow.strike]['volume'] += flow.volume
                strike_data[flow.strike]['value'] += value
                strike_data[flow.strike]['trades'].append({
                    'type': flow.option_type,
                    'volume': flow.volume,
                    'value': value
                })
        
        # Identify smart money strikes
        for strike, data in strike_data.items():
            if data['value'] > 100000:  # $100k+ total
                # Determine bias
                call_value = sum(
                    t['value'] for t in data['trades'] 
                    if t['type'] == 'call'
                )
                put_value = sum(
                    t['value'] for t in data['trades'] 
                    if t['type'] == 'put'
                )
                
                bias = 'bullish' if call_value > put_value else 'bearish'
                
                smart_strikes.append({
                    'strike': strike,
                    'total_value': data['value'],
                    'trade_count': len(data['trades']),
                    'bias': bias
                })
        
        return sorted(smart_strikes, key=lambda x: x['total_value'], reverse=True)[:10]
    
    def _analyze_term_structure(self, options_chain: pd.DataFrame) -> Dict[str, any]:
        """Analyze volatility term structure"""
        if options_chain.empty:
            return {}
        
        # Group by expiry
        term_structure = {}
        
        for expiry in options_chain['expiry'].unique():
            expiry_options = options_chain[options_chain['expiry'] == expiry]
            
            avg_iv = expiry_options['impliedVolatility'].mean()
            
            # Calculate days to expiry
            try:
                exp_date = datetime.strptime(expiry, '%Y-%m-%d')
                days_to_exp = (exp_date - datetime.now()).days
            except:
                days_to_exp = 30  # Default
            
            term_structure[expiry] = {
                'days_to_expiry': days_to_exp,
                'avg_iv': avg_iv
            }
        
        # Determine term structure shape
        sorted_terms = sorted(term_structure.items(), key=lambda x: x[1]['days_to_expiry'])
        
        if len(sorted_terms) >= 2:
            near_iv = sorted_terms[0][1]['avg_iv']
            far_iv = sorted_terms[-1][1]['avg_iv']
            
            if near_iv > far_iv * 1.1:
                structure = 'backwardation'
                sentiment = 'high_near_term_uncertainty'
            elif far_iv > near_iv * 1.1:
                structure = 'contango'
                sentiment = 'long_term_uncertainty'
            else:
                structure = 'flat'
                sentiment = 'stable'
        else:
            structure = 'insufficient_data'
            sentiment = 'unknown'
        
        return {
            'structure': structure,
            'sentiment': sentiment,
            'term_data': dict(sorted_terms[:5])  # First 5 expiries
        }