#!/usr/bin/env python3
"""
🔧 MULTI-BROKER SYMBOL MAPPER FOR BITTEN
Translates universal signals to broker-specific symbols for MT5 execution

CAPABILITIES:
- Maps BITTEN internal pairs to broker-specific symbols
- Handles different naming conventions and suffixes
- Validates symbol availability and properties
- Per-user symbol translation maps
- Fuzzy matching fallbacks for symbol discovery
"""

import json
import os
import time
import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict
from difflib import SequenceMatcher
import re

logger = logging.getLogger(__name__)

@dataclass
class SymbolMapping:
    """Symbol mapping result"""
    base_pair: str
    translated_pair: str
    broker_name: str
    digits: int
    pip_value: float
    min_lot: float
    max_lot: float
    lot_step: float
    margin_rate: float
    swap_long: float
    swap_short: float
    contract_size: float
    trade_mode: int
    last_updated: datetime

@dataclass
class TranslationResult:
    """Symbol translation result"""
    success: bool
    user_id: str
    base_pair: str
    translated_pair: Optional[str]
    symbol_info: Optional[Dict]
    error_message: Optional[str]
    fallback_used: bool = False
    timestamp: datetime = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now(timezone.utc)

class BrokerSymbolMapper:
    """
    🔧 BROKER SYMBOL MAPPER
    
    Handles symbol translation for different broker types and naming conventions
    """
    
    def __init__(self, maps_directory: str = "/root/HydraX-v2/data/symbol_maps"):
        self.maps_directory = maps_directory
        self.user_maps: Dict[str, Dict[str, str]] = {}
        self.user_symbol_info: Dict[str, Dict[str, Dict]] = {}
        self.translation_log_path = "/root/HydraX-v2/data/symbol_translations.log"
        
        # BITTEN standard pairs that need translation
        self.standard_pairs = [
            # Major Forex Pairs
            "EURUSD", "GBPUSD", "USDJPY", "USDCHF", "AUDUSD", "USDCAD", "NZDUSD",
            # Cross Pairs  
            "EURJPY", "GBPJPY", "EURGBP", "EURAUD", "EURCAD", "EURNZD", "EURCHT",
            "GBPAUD", "GBPCAD", "GBPNZD", "GBPCHF", "AUDJPY", "AUDCAD", "AUDNZD",
            "AUDCHF", "CADJPY", "CADCHF", "NZDJPY", "NZDCAD", "NZDCHF", "CHFJPY",
            # Commodities
            "XAUUSD", "XAGUSD", "USOIL", "UKOIL", "NATGAS",
            # Indices
            "US30", "US500", "NAS100", "GER30", "UK100", "JPN225", "AUS200",
            # Crypto (if supported)
            "BTCUSD", "ETHUSD", "LTCUSD", "XRPUSD", "ADAUSD"
        ]
        
        # Common broker suffix patterns
        self.suffix_patterns = [
            "", ".r", ".raw", ".pro", ".ecn", ".stp", ".m", ".c", ".i",
            "_", "-", "m", "pro", "ecn", "raw", "mini", "micro"
        ]
        
        # Alternative symbol names for common pairs
        self.symbol_alternatives = {
            "XAUUSD": ["XAU/USD", "GOLD", "XAUUSD", "Gold", "XAU_USD"],
            "XAGUSD": ["XAG/USD", "SILVER", "XAGUSD", "Silver", "XAG_USD"],
            "USOIL": ["CRUDE", "OIL", "WTI", "USOIL", "CL", "CRUDE_OIL"],
            "UKOIL": ["BRENT", "UKOIL", "BRENT_OIL", "BRN"],
            "NATGAS": ["NGAS", "NG", "NATGAS", "NATURAL_GAS"],
            "US30": ["DOW", "US30", "DJ30", "DJIA", "DJI"],
            "US500": ["SPX", "SP500", "US500", "SPX500"],
            "NAS100": ["NASDAQ", "NAS100", "NDX", "NDAQ"],
            "GER30": ["DAX", "GER30", "DE30", "DAX30"],
            "UK100": ["FTSE", "UK100", "UKX"],
            "JPN225": ["NIKKEI", "JPN225", "NI225", "N225"],
            "BTCUSD": ["BITCOIN", "BTC", "BTCUSD", "BTC/USD"],
            "ETHUSD": ["ETHEREUM", "ETH", "ETHUSD", "ETH/USD"]
        }
        
        # Ensure directories exist
        os.makedirs(self.maps_directory, exist_ok=True)
        os.makedirs(os.path.dirname(self.translation_log_path), exist_ok=True)
        
        logger.info("🔧 Broker Symbol Mapper initialized")
    
    def initialize_user_symbols(self, user_id: str, mt5_symbols: List[Dict], 
                              broker_name: str = "Unknown") -> bool:
        """
        Initialize symbol mapping for a user based on their MT5 terminal symbols
        
        Args:
            user_id: Unique user identifier
            mt5_symbols: List of symbol dictionaries from mt5.symbols_get()
            broker_name: Broker name for identification
            
        Returns:
            bool: Success status
        """
        try:
            logger.info(f"🔧 Initializing symbol mapping for user {user_id} ({broker_name})")
            
            # Extract symbol names from MT5 symbol info
            available_symbols = []
            symbol_info_map = {}
            
            for symbol_data in mt5_symbols:
                if isinstance(symbol_data, dict):
                    symbol_name = symbol_data.get('name', '')
                    if symbol_name:
                        available_symbols.append(symbol_name)
                        symbol_info_map[symbol_name] = symbol_data
                elif hasattr(symbol_data, 'name'):
                    # Handle MT5 symbol objects
                    symbol_name = symbol_data.name
                    available_symbols.append(symbol_name)
                    symbol_info_map[symbol_name] = {
                        'name': symbol_data.name,
                        'digits': getattr(symbol_data, 'digits', 5),
                        'point': getattr(symbol_data, 'point', 0.00001),
                        'volume_min': getattr(symbol_data, 'volume_min', 0.01),
                        'volume_max': getattr(symbol_data, 'volume_max', 100.0),
                        'volume_step': getattr(symbol_data, 'volume_step', 0.01),
                        'margin_rate': getattr(symbol_data, 'margin_rate', 1.0),
                        'swap_long': getattr(symbol_data, 'swap_long', 0.0),
                        'swap_short': getattr(symbol_data, 'swap_short', 0.0),
                        'contract_size': getattr(symbol_data, 'contract_size', 100000.0),
                        'trade_mode': getattr(symbol_data, 'trade_mode', 4)
                    }
            
            logger.info(f"📊 Found {len(available_symbols)} symbols for user {user_id}")
            
            # Build translation map
            translation_map = {}
            
            for standard_pair in self.standard_pairs:
                translated_symbol = self._find_matching_symbol(standard_pair, available_symbols)
                
                if translated_symbol:
                    translation_map[standard_pair] = translated_symbol
                    logger.debug(f"✅ {standard_pair} → {translated_symbol}")
                else:
                    logger.warning(f"⚠️ No match found for {standard_pair}")
            
            # Save user mapping
            self.user_maps[user_id] = translation_map
            self.user_symbol_info[user_id] = symbol_info_map
            
            # Persist to file
            self._save_user_mapping(user_id, translation_map, symbol_info_map, broker_name)
            
            logger.info(f"✅ Symbol mapping completed for user {user_id}: {len(translation_map)} pairs mapped")
            return True
            
        except Exception as e:
            logger.error(f"❌ Symbol mapping initialization failed for user {user_id}: {e}")
            return False
    
    def translate_symbol(self, user_id: str, base_pair: str) -> TranslationResult:
        """
        Translate a BITTEN standard pair to user's broker-specific symbol
        
        Args:
            user_id: User identifier
            base_pair: BITTEN standard pair (e.g., "XAUUSD")
            
        Returns:
            TranslationResult: Translation result with success status
        """
        try:
            # Load user mapping if not in memory
            if user_id not in self.user_maps:
                self._load_user_mapping(user_id)
            
            # Check if user mapping exists
            if user_id not in self.user_maps:
                return TranslationResult(
                    success=False,
                    user_id=user_id,
                    base_pair=base_pair,
                    translated_pair=None,
                    symbol_info=None,
                    error_message=f"No symbol mapping found for user {user_id}",
                    fallback_used=False
                )
            
            user_map = self.user_maps[user_id]
            
            # Direct translation
            if base_pair in user_map:
                translated_pair = user_map[base_pair]
                symbol_info = self.user_symbol_info.get(user_id, {}).get(translated_pair, {})
                
                result = TranslationResult(
                    success=True,
                    user_id=user_id,
                    base_pair=base_pair,
                    translated_pair=translated_pair,
                    symbol_info=symbol_info,
                    error_message=None,
                    fallback_used=False
                )
                
                # Log successful translation
                self._log_translation(result)
                return result
            
            # Attempt fallback matching
            logger.warning(f"⚠️ Direct mapping not found for {base_pair}, attempting fallback")
            fallback_result = self._attempt_fallback_translation(user_id, base_pair)
            
            if fallback_result.success:
                # Update user mapping with fallback result
                self.user_maps[user_id][base_pair] = fallback_result.translated_pair
                self._save_user_mapping(user_id, self.user_maps[user_id], 
                                      self.user_symbol_info.get(user_id, {}), "Updated")
            
            # Log translation attempt
            self._log_translation(fallback_result)
            return fallback_result
            
        except Exception as e:
            logger.error(f"❌ Symbol translation failed for user {user_id}, pair {base_pair}: {e}")
            
            error_result = TranslationResult(
                success=False,
                user_id=user_id,
                base_pair=base_pair,
                translated_pair=None,
                symbol_info=None,
                error_message=f"Translation error: {str(e)}",
                fallback_used=False
            )
            
            self._log_translation(error_result)
            return error_result
    
    def _find_matching_symbol(self, standard_pair: str, available_symbols: List[str]) -> Optional[str]:
        """
        Find the best matching symbol for a standard pair
        
        Args:
            standard_pair: BITTEN standard pair
            available_symbols: List of broker's available symbols
            
        Returns:
            str: Best matching symbol or None
        """
        # Direct match
        if standard_pair in available_symbols:
            return standard_pair
        
        # Try with common suffixes
        for suffix in self.suffix_patterns:
            if suffix:
                candidate = f"{standard_pair}{suffix}"
                if candidate in available_symbols:
                    return candidate
        
        # Try alternative names
        if standard_pair in self.symbol_alternatives:
            for alternative in self.symbol_alternatives[standard_pair]:
                if alternative in available_symbols:
                    return alternative
                
                # Try alternatives with suffixes
                for suffix in self.suffix_patterns:
                    if suffix:
                        candidate = f"{alternative}{suffix}"
                        if candidate in available_symbols:
                            return candidate
        
        # Fuzzy matching as last resort
        best_match = None
        best_score = 0.6  # Minimum similarity threshold
        
        for symbol in available_symbols:
            # Remove common suffixes for comparison
            clean_symbol = re.sub(r'\.(r|raw|pro|ecn|stp|m|c|i)$', '', symbol)
            clean_symbol = re.sub(r'[_\-]$', '', clean_symbol)
            
            # Calculate similarity
            similarity = SequenceMatcher(None, standard_pair.lower(), clean_symbol.lower()).ratio()
            
            if similarity > best_score:
                best_score = similarity
                best_match = symbol
        
        if best_match:
            logger.info(f"🔍 Fuzzy match: {standard_pair} → {best_match} (similarity: {best_score:.2f})")
        
        return best_match
    
    def _attempt_fallback_translation(self, user_id: str, base_pair: str) -> TranslationResult:
        """
        Attempt fallback translation for unmapped symbols
        
        Args:
            user_id: User identifier
            base_pair: Base pair to translate
            
        Returns:
            TranslationResult: Fallback translation result
        """
        try:
            # Get user's available symbols
            symbol_info_map = self.user_symbol_info.get(user_id, {})
            available_symbols = list(symbol_info_map.keys())
            
            if not available_symbols:
                return TranslationResult(
                    success=False,
                    user_id=user_id,
                    base_pair=base_pair,
                    translated_pair=None,
                    symbol_info=None,
                    error_message="No symbol information available for fallback",
                    fallback_used=True
                )
            
            # Attempt to find match
            matched_symbol = self._find_matching_symbol(base_pair, available_symbols)
            
            if matched_symbol:
                symbol_info = symbol_info_map.get(matched_symbol, {})
                
                return TranslationResult(
                    success=True,
                    user_id=user_id,
                    base_pair=base_pair,
                    translated_pair=matched_symbol,
                    symbol_info=symbol_info,
                    error_message=None,
                    fallback_used=True
                )
            else:
                return TranslationResult(
                    success=False,
                    user_id=user_id,
                    base_pair=base_pair,
                    translated_pair=None,
                    symbol_info=None,
                    error_message=f"Symbol not found for user {user_id}: {base_pair}",
                    fallback_used=True
                )
                
        except Exception as e:
            return TranslationResult(
                success=False,
                user_id=user_id,
                base_pair=base_pair,
                translated_pair=None,
                symbol_info=None,
                error_message=f"Fallback translation error: {str(e)}",
                fallback_used=True
            )
    
    def _save_user_mapping(self, user_id: str, translation_map: Dict[str, str], 
                          symbol_info_map: Dict[str, Dict], broker_name: str):
        """Save user mapping to file"""
        try:
            mapping_data = {
                "user_id": user_id,
                "broker_name": broker_name,
                "last_updated": datetime.now(timezone.utc).isoformat(),
                "translation_map": translation_map,
                "symbol_count": len(symbol_info_map),
                "pairs_mapped": len(translation_map),
                "symbol_info": symbol_info_map
            }
            
            file_path = os.path.join(self.maps_directory, f"user_{user_id}_symbols.json")
            
            with open(file_path, 'w') as f:
                json.dump(mapping_data, f, indent=2)
                
            logger.debug(f"💾 Saved symbol mapping for user {user_id}")
            
        except Exception as e:
            logger.error(f"❌ Failed to save mapping for user {user_id}: {e}")
    
    def _load_user_mapping(self, user_id: str) -> bool:
        """Load user mapping from file"""
        try:
            file_path = os.path.join(self.maps_directory, f"user_{user_id}_symbols.json")
            
            if not os.path.exists(file_path):
                logger.warning(f"⚠️ No saved mapping found for user {user_id}")
                return False
            
            with open(file_path, 'r') as f:
                mapping_data = json.load(f)
            
            self.user_maps[user_id] = mapping_data.get("translation_map", {})
            self.user_symbol_info[user_id] = mapping_data.get("symbol_info", {})
            
            logger.debug(f"📥 Loaded symbol mapping for user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to load mapping for user {user_id}: {e}")
            return False
    
    def _log_translation(self, result: TranslationResult):
        """Log translation result"""
        try:
            log_entry = {
                "timestamp": result.timestamp.isoformat(),
                "user": result.user_id,
                "base_pair": result.base_pair,
                "translated_pair": result.translated_pair,
                "status": "success" if result.success else "error",
                "fallback_used": result.fallback_used,
                "error_message": result.error_message
            }
            
            # Append to log file
            with open(self.translation_log_path, 'a') as f:
                f.write(json.dumps(log_entry) + '\n')
                
        except Exception as e:
            logger.error(f"❌ Failed to log translation: {e}")
    
    def get_user_mapping_status(self, user_id: str) -> Dict:
        """Get mapping status for a user"""
        try:
            if user_id not in self.user_maps:
                self._load_user_mapping(user_id)
            
            user_map = self.user_maps.get(user_id, {})
            symbol_info = self.user_symbol_info.get(user_id, {})
            
            return {
                "user_id": user_id,
                "mapping_exists": bool(user_map),
                "pairs_mapped": len(user_map),
                "total_symbols": len(symbol_info),
                "mapped_pairs": list(user_map.keys()),
                "translation_map": user_map
            }
            
        except Exception as e:
            return {
                "user_id": user_id,
                "mapping_exists": False,
                "error": str(e)
            }
    
    def refresh_user_mapping(self, user_id: str, mt5_symbols: List[Dict], 
                           broker_name: str = "Updated") -> bool:
        """Refresh symbol mapping for a user"""
        logger.info(f"🔄 Refreshing symbol mapping for user {user_id}")
        return self.initialize_user_symbols(user_id, mt5_symbols, broker_name)
    
    def get_translation_stats(self, hours_back: int = 24) -> Dict:
        """Get translation statistics"""
        try:
            stats = {
                "total_translations": 0,
                "successful_translations": 0,
                "failed_translations": 0,
                "fallback_used": 0,
                "unique_users": set(),
                "popular_pairs": {},
                "error_reasons": {}
            }
            
            cutoff_time = datetime.now(timezone.utc) - timedelta(hours=hours_back)
            
            if not os.path.exists(self.translation_log_path):
                return stats
            
            with open(self.translation_log_path, 'r') as f:
                for line in f:
                    try:
                        entry = json.loads(line.strip())
                        entry_time = datetime.fromisoformat(entry["timestamp"])
                        
                        if entry_time >= cutoff_time:
                            stats["total_translations"] += 1
                            stats["unique_users"].add(entry["user"])
                            
                            if entry["status"] == "success":
                                stats["successful_translations"] += 1
                            else:
                                stats["failed_translations"] += 1
                                error_msg = entry.get("error_message", "Unknown")
                                stats["error_reasons"][error_msg] = stats["error_reasons"].get(error_msg, 0) + 1
                            
                            if entry.get("fallback_used"):
                                stats["fallback_used"] += 1
                            
                            # Track popular pairs
                            pair = entry["base_pair"]
                            stats["popular_pairs"][pair] = stats["popular_pairs"].get(pair, 0) + 1
                            
                    except (json.JSONDecodeError, KeyError, ValueError):
                        continue
            
            # Convert set to count
            stats["unique_users"] = len(stats["unique_users"])
            
            return stats
            
        except Exception as e:
            logger.error(f"❌ Failed to get translation stats: {e}")
            return {"error": str(e)}

# Global instance for integration
symbol_mapper = BrokerSymbolMapper()

def initialize_user_symbols(user_id: str, mt5_symbols: List[Dict], 
                          broker_name: str = "Unknown") -> bool:
    """Convenience function to initialize user symbols"""
    return symbol_mapper.initialize_user_symbols(user_id, mt5_symbols, broker_name)

def translate_symbol(user_id: str, base_pair: str) -> TranslationResult:
    """Convenience function to translate symbols"""
    return symbol_mapper.translate_symbol(user_id, base_pair)

def get_user_mapping_status(user_id: str) -> Dict:
    """Convenience function to get user mapping status"""
    return symbol_mapper.get_user_mapping_status(user_id)

# Test function
def test_symbol_mapper():
    """Test the symbol mapper with sample data"""
    print("🔧 Testing Broker Symbol Mapper...")
    
    # Sample MT5 symbols for different broker types
    test_symbols = [
        # Standard broker
        {"name": "EURUSD", "digits": 5, "point": 0.00001, "volume_min": 0.01},
        {"name": "GBPUSD", "digits": 5, "point": 0.00001, "volume_min": 0.01},
        {"name": "XAUUSD", "digits": 2, "point": 0.01, "volume_min": 0.01},
        
        # Broker with .r suffix
        {"name": "EURUSD.r", "digits": 5, "point": 0.00001, "volume_min": 0.01},
        {"name": "GBPUSD.r", "digits": 5, "point": 0.00001, "volume_min": 0.01},
        {"name": "XAU/USD.r", "digits": 2, "point": 0.01, "volume_min": 0.01},
        
        # Alternative names
        {"name": "GOLD", "digits": 2, "point": 0.01, "volume_min": 0.01},
        {"name": "US30", "digits": 1, "point": 0.1, "volume_min": 0.1},
    ]
    
    # Test initialization
    success = initialize_user_symbols("test_user_001", test_symbols, "Test Broker")
    print(f"✅ Initialization: {'Success' if success else 'Failed'}")
    
    # Test translations
    test_pairs = ["EURUSD", "XAUUSD", "US30", "NONEXISTENT"]
    
    for pair in test_pairs:
        result = translate_symbol("test_user_001", pair)
        print(f"📊 {pair} → {result.translated_pair if result.success else 'FAILED'}")
        if not result.success:
            print(f"   Error: {result.error_message}")
    
    # Test status
    status = get_user_mapping_status("test_user_001")
    print(f"📈 Mapping Status: {status['pairs_mapped']} pairs mapped")
    
    print("🎯 Symbol Mapper testing complete!")

if __name__ == "__main__":
    test_symbol_mapper()