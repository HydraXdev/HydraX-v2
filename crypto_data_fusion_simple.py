# crypto_data_fusion_simple.py - Essential exchange data helpers only
from typing import Dict
from crypto_consensus import compute_consensus
import time

def top_of_book(exchange_manager, symbol: str) -> Dict[str, dict]:
    """
    Return {venue: {'bid':..., 'ask':..., 'mid':..., 'spread_bps':..., 'depth5bps_usd':...}}
    Implement using exchange_manager websocket snapshots; fallback to REST if needed.
    """
    quotes = {}
    if not hasattr(exchange_manager, 'connected') or not exchange_manager:
        return quotes
        
    try:
        for venue in exchange_manager.connected():
            q = exchange_manager.best_quote(venue, symbol)  # implement in manager
            if not q: continue
            bid, ask = q["bid"], q["ask"]
            mid = (bid + ask)/2.0
            spread_bps = (ask - bid)/mid * 10000.0
            depth = q.get("depth5bps_usd", 0.0)
            quotes[venue] = {"bid":bid,"ask":ask,"mid":mid,"spread_bps":spread_bps,"depth5bps_usd":depth}
    except Exception as e:
        # Graceful fallback if exchange manager not available
        pass
        
    return quotes

def order_book_imbalance(imbalance_detector, venue: str, symbol: str) -> float:
    """Return ratio bid_depth/ask_depth near top; implement in imbalance_detector"""
    if not imbalance_detector or not hasattr(imbalance_detector, 'top_imbalance'):
        return 1.0  # neutral if not available
        
    try:
        return imbalance_detector.top_imbalance(venue, symbol) or 1.0
    except:
        return 1.0

def consensus_snapshot(exchange_manager, symbol: str):
    """Get consensus and quotes for a symbol"""
    if not exchange_manager:
        # Return stub data if exchange manager not available
        from crypto_consensus import Consensus
        return Consensus(mid=0, spread_bps=999, depth_usd=0, conf=0, nx=0), {}
    
    try:
        quotes = top_of_book(exchange_manager, symbol)
        cons = compute_consensus(quotes)
        return cons, quotes
    except Exception as e:
        # Return stub data on error
        from crypto_consensus import Consensus
        return Consensus(mid=0, spread_bps=999, depth_usd=0, conf=0, nx=0), {}