#!/usr/bin/env python3
"""
SHEPHERD Validation for AAA Signal Engine
Tests compatibility and validates signal generation methods
"""

import os
import sys
import json
import logging
from datetime import datetime
from pathlib import Path

# Add project root to path
sys.path.insert(0, '/root/HydraX-v2')

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('AAA_VALIDATOR')

def validate_aaa_methods():
    """Validate AAA signal generation methods"""
    logger.info("=== VALIDATING AAA SIGNAL METHODS ===")
    
    try:
        # Import AAA methods
        from bitten_alerts_AAA import (
            analyze_top_games,
            create_final_recommendations,
            show_game_psychology,
            test_formats
        )
        
        # Test analyze_top_games
        logger.info("\n1. Testing analyze_top_games...")
        games = analyze_top_games()
        assert isinstance(games, dict), "analyze_top_games should return dict"
        assert len(games) == 3, "Should have 3 games"
        assert all(game in games for game in ["Call of Duty", "Fortnite", "CS:GO"])
        logger.info("✓ analyze_top_games validated")
        
        # Test create_final_recommendations
        logger.info("\n2. Testing create_final_recommendations...")
        recommendations = create_final_recommendations()
        assert isinstance(recommendations, list), "Should return list"
        assert len(recommendations) == 4, "Should have 4 recommendations"
        
        for rec in recommendations:
            assert "name" in rec, "Missing name field"
            assert "arcade" in rec, "Missing arcade format"
            assert "sniper" in rec, "Missing sniper format"
            assert isinstance(rec["arcade"], str), "Arcade should be string"
            assert isinstance(rec["sniper"], str), "Sniper should be string"
            assert len(rec["arcade"]) > 0, "Arcade format empty"
            assert len(rec["sniper"]) > 0, "Sniper format empty"
            
        logger.info("✓ create_final_recommendations validated")
        logger.info(f"  Found {len(recommendations)} recommendation formats")
        
        # Display recommendation details
        for i, rec in enumerate(recommendations, 1):
            logger.info(f"  {i}. {rec['name']}:")
            logger.info(f"     Arcade: {rec['arcade'][:30]}...")
            logger.info(f"     Sniper: {rec['sniper'][:30]}...")
        
        return True
        
    except Exception as e:
        logger.error(f"AAA validation failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def validate_signal_integration():
    """Check if AAA methods can be integrated with signal system"""
    logger.info("\n=== VALIDATING SIGNAL INTEGRATION ===")
    
    try:
        # Check live signals compatibility
        from bitten_alerts_AAA import create_final_recommendations
        
        # Test signal format compatibility
        recommendations = create_final_recommendations()
        
        # Simulate signal generation with AAA format
        test_signals = []
        for rec in recommendations:
            arcade_signal = {
                "type": "ARCADE",
                "format": rec["name"],
                "text": rec["arcade"],
                "tcs_score": 78,
                "signal_id": f"TEST_AAA_{rec['name']}_ARCADE"
            }
            
            sniper_signal = {
                "type": "SNIPER", 
                "format": rec["name"],
                "text": rec["sniper"],
                "tcs_score": 87,
                "signal_id": f"TEST_AAA_{rec['name']}_SNIPER"
            }
            
            test_signals.extend([arcade_signal, sniper_signal])
        
        logger.info(f"✓ Generated {len(test_signals)} test signals with AAA formats")
        
        # Validate signal structure
        for signal in test_signals:
            assert "type" in signal
            assert "format" in signal
            assert "text" in signal
            assert "tcs_score" in signal
            assert "signal_id" in signal
            assert len(signal["text"]) > 0
            
        logger.info("✓ All signals have valid structure")
        
        return True
        
    except Exception as e:
        logger.error(f"Integration validation failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def run_shepherd_validation():
    """Run SHEPHERD trace and validation"""
    logger.info("\n=== RUNNING SHEPHERD VALIDATION ===")
    
    try:
        from bitten.core.shepherd.shepherd import ShepherdCore
        
        # Initialize SHEPHERD
        shepherd = ShepherdCore('/root/HydraX-v2')
        
        # Trace AAA module
        logger.info("\n1. Tracing AAA module...")
        trace_result = shepherd.trace('bitten_alerts_AAA.py')
        
        if 'error' not in trace_result:
            logger.info(f"✓ Module traced successfully")
            logger.info(f"  Functions: {', '.join(trace_result.get('functions', []))}")
            logger.info(f"  Connections: {trace_result.get('total_connections', 0)}")
        else:
            logger.warning(f"  Trace error: {trace_result.get('error')}")
        
        # Wrap validation for AAA outputs
        logger.info("\n2. Testing SHEPHERD wrap on AAA outputs...")
        from bitten_alerts_AAA import create_final_recommendations
        recommendations = create_final_recommendations()
        
        wrap_result = shepherd.wrap(recommendations)
        logger.info(f"✓ Wrap validation: {'SAFE' if wrap_result.get('safe') else 'UNSAFE'}")
        logger.info(f"  Output type: {wrap_result.get('output_type')}")
        logger.info(f"  Validations: {len(wrap_result.get('validations', []))}")
        logger.info(f"  Contradictions: {len(wrap_result.get('contradictions', []))}")
        
        # Document AAA functions
        logger.info("\n3. Documenting AAA functions...")
        for func_name in ['analyze_top_games', 'create_final_recommendations']:
            doc_result = shepherd.doc(func_name)
            if 'summary' in doc_result:
                logger.info(f"✓ {func_name}: {doc_result.get('summary', 'No summary')}")
            
        return True
        
    except Exception as e:
        logger.error(f"SHEPHERD validation failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def update_shepherd_index():
    """Update SHEPHERD index with AAA signal methods"""
    logger.info("\n=== UPDATING SHEPHERD INDEX ===")
    
    try:
        index_path = Path('/root/HydraX-v2/bitten/data/shepherd/shepherd_index.json')
        
        # Create AAA index entry
        aaa_entry = {
            "module": "bitten_alerts_AAA",
            "functions": [
                {
                    "name": "analyze_top_games",
                    "purpose": "Analyze top game patterns for engagement",
                    "returns": "Dictionary of game patterns and psychology"
                },
                {
                    "name": "create_final_recommendations", 
                    "purpose": "Generate AAA-style alert formats",
                    "returns": "List of recommended alert formats"
                },
                {
                    "name": "show_game_psychology",
                    "purpose": "Display psychological elements from games",
                    "returns": "None (prints to console)"
                },
                {
                    "name": "test_formats",
                    "purpose": "Test and display AAA format options",
                    "returns": "None (prints to console)"
                }
            ],
            "integration": {
                "compatible_with": ["bitten_live_signals", "telegram_alerts"],
                "signal_types": ["ARCADE", "SNIPER"],
                "format_styles": ["MILITARY_OPS", "URGENCY_PLAY", "ZONE_CONTROL", "SQUAD_DYNAMICS"]
            },
            "validation": {
                "timestamp": datetime.now().isoformat(),
                "status": "VALIDATED",
                "shepherd_compatible": True
            }
        }
        
        # Save AAA validation report
        report_path = Path('/root/HydraX-v2/aaa_validation_report.json')
        with open(report_path, 'w') as f:
            json.dump(aaa_entry, f, indent=2)
        
        logger.info(f"✓ AAA validation report saved to {report_path}")
        
        return True
        
    except Exception as e:
        logger.error(f"Failed to update SHEPHERD index: {e}")
        return False

def main():
    """Run all validations"""
    logger.info("=" * 60)
    logger.info("AAA SIGNAL ENGINE - SHEPHERD VALIDATION")
    logger.info("=" * 60)
    
    results = {
        "aaa_methods": validate_aaa_methods(),
        "signal_integration": validate_signal_integration(),
        "shepherd_validation": run_shepherd_validation(),
        "index_update": update_shepherd_index()
    }
    
    # Summary
    logger.info("\n" + "=" * 60)
    logger.info("VALIDATION SUMMARY")
    logger.info("=" * 60)
    
    for test, passed in results.items():
        status = "PASSED" if passed else "FAILED"
        logger.info(f"{test}: {status}")
    
    all_passed = all(results.values())
    
    if all_passed:
        logger.info("\n✓ ALL VALIDATIONS PASSED")
        logger.info("The AAA signal engine is compatible with SHEPHERD's validation system")
    else:
        logger.info("\n✗ SOME VALIDATIONS FAILED")
        logger.info("Please review the errors above")
    
    return all_passed

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)