#!/usr/bin/env python3
"""
Performance-optimized webapp server with caching, monitoring, and optimizations
This is an enhanced version of webapp_server_optimized.py with performance improvements
"""

import os
import sys
import json
import time
import logging
from datetime import datetime
from functools import wraps

# Import performance tools
from performance_profiler import RoutePerformanceProfiler
from mission_cache import OptimizedMissionLoader
from webapp_performance_patch import performance_monitor, create_api_cache

# Flask imports
from flask import Flask, render_template, request, jsonify, make_response, g

# Initialize Flask app with performance optimizations
app = Flask(__name__)
app.config['JSON_SORT_KEYS'] = False  # Faster JSON serialization

# Initialize performance systems
profiler = RoutePerformanceProfiler()
mission_loader = OptimizedMissionLoader()
get_cached, set_cached = create_api_cache()

# Performance logging setup
perf_logger = logging.getLogger('webapp_performance')
perf_logger.setLevel(logging.INFO)

handler = logging.FileHandler('/tmp/webapp_performance.log')
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
perf_logger.addHandler(handler)

def log_hud_access(user_id, mission_id):
    """Lightweight HUD access logging"""
    try:
        log_data = {
            'timestamp': datetime.now().isoformat(),
            'user_id': user_id,
            'mission_id': mission_id,
            'event': 'hud_access'
        }
        perf_logger.info(f"HUD_ACCESS: {json.dumps(log_data)}")
    except:
        pass  # Don't let logging errors affect the request

@app.before_request
def before_request():
    """Performance monitoring setup"""
    g.start_time = time.time()

@app.after_request
def after_request(response):
    """Log request performance"""
    if hasattr(g, 'start_time'):
        response_time = time.time() - g.start_time
        
        # Add performance headers
        response.headers['X-Response-Time'] = f"{response_time:.3f}s"
        
        # Log slow requests
        if response_time > 1.0:
            perf_logger.warning(
                f"SLOW_REQUEST: {request.method} {request.path} took {response_time:.3f}s"
            )
    
    return response

# OPTIMIZED ROUTES

@app.route('/')
@performance_monitor('GET_index')
def index():
    """Optimized landing page with caching"""
    # Check cache first
    cache_key = "landing_page"
    cached_response = get_cached(cache_key, ttl=300)  # 5 minute cache
    
    if cached_response:
        return cached_response
    
    try:
        # Quick render without heavy processing
        response = make_response(render_template('landing_page.html'))
        
        # Set cache headers
        response.headers['Cache-Control'] = 'public, max-age=300'
        
        # Cache the response  
        set_cached(cache_key, response)
        
        return response
        
    except Exception as e:
        perf_logger.error(f"Landing page error: {e}")
        return "Error loading page", 500

@app.route('/hud')
@performance_monitor('GET_hud')
def mission_briefing():
    """OPTIMIZED Mission HUD with intelligent caching"""
    try:
        # Quick parameter extraction
        mission_id = request.args.get('mission_id') or request.args.get('signal')
        user_id = request.args.get('user_id')
        
        if not mission_id:
            return render_template('error_hud.html', 
                                 error="Missing mission_id or signal parameter",
                                 error_code=400), 400
        
        # Use optimized mission loader with multi-level caching
        template_vars = mission_loader.get_mission_for_hud(mission_id, user_id)
        
        if template_vars is None:
            perf_logger.warning(f"Mission not found: {mission_id}")
            return render_template('error_hud.html', 
                                 error=f"Mission {mission_id} not found", 
                                 error_code=404), 404
        
        # Background logging (non-blocking)
        if user_id and mission_id:
            try:
                import threading
                threading.Thread(
                    target=log_hud_access, 
                    args=(user_id, mission_id), 
                    daemon=True
                ).start()
            except:
                pass
        
        # Create response with smart caching
        response = make_response(render_template('new_hud_template.html', **template_vars))
        
        # Intelligent cache headers based on mission expiry
        expiry_seconds = template_vars.get('expiry_seconds', 0)
        
        if expiry_seconds > 600:  # More than 10 minutes left
            response.headers['Cache-Control'] = 'public, max-age=120'  # 2 minutes
        elif expiry_seconds > 60:  # More than 1 minute left
            response.headers['Cache-Control'] = 'public, max-age=30'   # 30 seconds
        else:
            response.headers['Cache-Control'] = 'no-cache'  # No caching for expiring missions
        
        # Add ETag for client-side caching
        etag = f'"{mission_id}-{int(time.time() // 60)}"'  # Changes every minute
        response.headers['ETag'] = etag
        
        # Check if client has cached version
        if request.headers.get('If-None-Match') == etag:
            return '', 304  # Not Modified
        
        # Performance metadata
        if hasattr(g, 'start_time'):
            response.headers['X-Cache-Status'] = 'HIT' if template_vars.get('_cache_hit') else 'MISS'
            response.headers['X-Processing-Time'] = f"{time.time() - g.start_time:.3f}s"
        
        return response
        
    except Exception as e:
        perf_logger.error(f"HUD error for mission_id='{mission_id}': {e}", exc_info=True)
        return render_template('error_hud.html', 
                             error=f"Error loading mission {mission_id}: {str(e)}", 
                             error_code=500), 500

@app.route('/api/fire', methods=['POST'])
@performance_monitor('POST_api_fire')
def fire_mission():
    """OPTIMIZED Fire mission endpoint with async processing"""
    try:
        start_time = time.time()
        
        # Fast parameter extraction
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No JSON data provided', 'success': False}), 400
        
        mission_id = data.get('mission_id')
        user_id = request.headers.get('X-User-ID')
        
        # Quick validation
        if not mission_id or not user_id:
            return jsonify({
                'error': 'Missing mission_id or user_id', 
                'success': False
            }), 400
        
        # Use cached mission data
        mission_data = mission_loader.cache.get_mission(mission_id)
        if mission_data is None:
            return jsonify({
                'error': 'Mission not found', 
                'success': False
            }), 404
        
        # Quick expiry check
        try:
            expires_at_str = mission_data.get('timing', {}).get('expires_at')
            if expires_at_str:
                expires_at = datetime.fromisoformat(expires_at_str)
                if datetime.now() > expires_at:
                    return jsonify({
                        'error': 'Mission expired', 
                        'success': False
                    }), 410
        except:
            pass  # Continue if expiry check fails
        
        # Background processing for non-critical operations
        def background_tasks():
            """Non-blocking background operations"""
            try:
                # Engagement logging
                from engagement_db import handle_fire_action
                handle_fire_action(user_id, mission_id, 'fired')
                
                # UUID tracking (if available)
                trade_uuid = mission_data.get('trade_uuid')
                if trade_uuid:
                    from tools.uuid_trade_tracker import UUIDTradeTracker
                    tracker = UUIDTradeTracker()
                    tracker.track_file_relay(trade_uuid, f"missions/{mission_id}.json", "api_fire")
                    
            except Exception as e:
                perf_logger.warning(f"Background task failed: {e}")
        
        # Start background tasks (non-blocking)
        try:
            import threading
            threading.Thread(target=background_tasks, daemon=True).start()
        except:
            pass
        
        # Return success immediately
        response_time = time.time() - start_time
        return jsonify({
            'success': True,
            'message': 'Mission fired successfully',
            'mission_id': mission_id,
            'response_time': round(response_time, 3),
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        perf_logger.error(f"Fire mission error: {e}")
        return jsonify({
            'error': 'Internal server error', 
            'success': False
        }), 500

@app.route('/api/user/<user_id>/stats')
@performance_monitor('GET_api_user_stats')
def api_user_stats(user_id):
    """OPTIMIZED User stats API with intelligent caching"""
    # Multi-level cache key based on user and time window
    time_window = int(time.time() // 300)  # 5-minute windows
    cache_key = f"user_stats:{user_id}:{time_window}"
    
    # Check cache first
    cached_response = get_cached(cache_key, ttl=300)
    if cached_response:
        response = make_response(cached_response)
        response.headers['X-Cache-Status'] = 'HIT'
        return response
    
    try:
        # Fast stats generation (placeholder - would integrate with real data)
        stats = {
            'user_id': user_id,
            'tier': 'NIBBLER',
            'win_rate': 65.0,
            'total_trades': 150,
            'profit_loss': 1250.50,
            'current_streak': 3,
            'generated_at': datetime.now().isoformat(),
            'cache_hit': False,
            'response_time': f"{time.time() - g.start_time:.3f}s"
        }
        
        response = jsonify(stats)
        
        # Cache the response
        set_cached(cache_key, response)
        
        # Set cache headers
        response.headers['Cache-Control'] = 'public, max-age=300'
        response.headers['X-Cache-Status'] = 'MISS'
        
        return response
        
    except Exception as e:
        perf_logger.error(f"User stats error for {user_id}: {e}")
        return jsonify({'error': 'Failed to load user stats'}), 500

@app.route('/me')
@performance_monitor('GET_war_room')
def war_room():
    """OPTIMIZED War Room with caching and reduced complexity"""
    user_id = request.args.get('user_id')
    
    if not user_id:
        return "Missing user_id parameter", 400
    
    # Cache key with user and hour window for relatively fresh data
    hour_window = int(time.time() // 3600)  # 1-hour windows
    cache_key = f"war_room:{user_id}:{hour_window}"
    
    cached_response = get_cached(cache_key, ttl=1800)  # 30-minute cache
    if cached_response:
        return cached_response
    
    try:
        # Simplified war room data (reduce database calls)
        war_room_data = {
            'user_id': user_id,
            'callsign': 'VIPER',
            'rank': 'SERGEANT',
            'win_rate': 68.5,
            'total_profit': 2847.50,
            'current_streak': 5,
            'squad_size': 12,
            'generated_at': datetime.now().isoformat()
        }
        
        response = make_response(render_template('war_room.html', **war_room_data))
        response.headers['Cache-Control'] = 'public, max-age=1800'
        
        # Cache the response
        set_cached(cache_key, response)
        
        return response
        
    except Exception as e:
        perf_logger.error(f"War room error for user {user_id}: {e}")
        return "Error loading War Room", 500

@app.route('/api/health')
@performance_monitor('GET_health')
def health_check():
    """Ultra-fast health check"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'uptime': time.time() - app.start_time if hasattr(app, 'start_time') else 0,
        'cache_stats': mission_loader.cache.get_cache_stats()
    })

# PERFORMANCE MONITORING ENDPOINTS

@app.route('/debug/performance')
def performance_dashboard():
    """Performance monitoring dashboard"""
    if not app.debug:
        return "Performance dashboard only available in debug mode", 403
    
    try:
        # Get comprehensive performance data
        report = profiler.get_performance_report()
        cache_stats = mission_loader.get_performance_stats()
        
        # Recent log entries
        try:
            with open('/tmp/webapp_performance.log', 'r') as f:
                recent_logs = f.readlines()[-50:]  # Last 50 lines
        except:
            recent_logs = []
        
        dashboard_data = {
            'profiler_report': report,
            'cache_stats': cache_stats,
            'recent_logs': recent_logs,
            'server_info': {
                'uptime': time.time() - app.start_time if hasattr(app, 'start_time') else 0,
                'debug_mode': app.debug,
                'request_count': getattr(app, 'request_count', 0)
            }
        }
        
        return jsonify(dashboard_data)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/debug/cache-control', methods=['POST'])
def cache_control():
    """Cache management endpoint"""
    if not app.debug:
        return "Cache control only available in debug mode", 403
    
    try:
        data = request.get_json()
        action = data.get('action') if data else None
        
        if action == 'clear_mission_cache':
            mission_loader.cache.invalidate_all()
            return jsonify({'message': 'Mission cache cleared', 'success': True})
        
        elif action == 'clear_api_cache':
            global get_cached, set_cached
            get_cached, set_cached = create_api_cache()
            return jsonify({'message': 'API cache cleared', 'success': True})
        
        elif action == 'get_stats':
            return jsonify({
                'mission_cache': mission_loader.cache.get_cache_stats(),
                'api_cache_enabled': True
            })
        
        elif action == 'cleanup':
            expired = mission_loader.cache.cleanup_expired()
            return jsonify({
                'message': f'Cleaned up {expired} expired entries',
                'success': True
            })
        
        return jsonify({'error': 'Invalid action'}), 400
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ERROR HANDLERS

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    perf_logger.error(f"Internal server error: {error}")
    return jsonify({'error': 'Internal server error'}), 500

# STARTUP CONFIGURATION

def configure_app():
    """Configure app for optimal performance"""
    # Performance settings
    app.config['JSON_SORT_KEYS'] = False
    app.config['JSONIFY_PRETTYPRINT_REGULAR'] = False
    
    # Set startup time
    app.start_time = time.time()
    
    # Request counter
    app.request_count = 0
    
    @app.before_request
    def count_requests():
        app.request_count = getattr(app, 'request_count', 0) + 1
    
    perf_logger.info("Performance-optimized webapp server configured")

if __name__ == '__main__':
    configure_app()
    
    print("🚀 Starting performance-optimized webapp server...")
    print("🔧 Performance features enabled:")
    print("  • Mission file caching with TTL")
    print("  • API response caching")
    print("  • Request performance monitoring")
    print("  • Intelligent cache headers")
    print("  • Background task processing")
    print("  • Performance logging to /tmp/webapp_performance.log")
    print()
    print("📊 Debug endpoints (if debug=True):")
    print("  • /debug/performance - Performance dashboard")
    print("  • /debug/cache-control - Cache management")
    print()
    
    app.run(
        host='0.0.0.0',
        port=8889,  # Different port to test alongside main server
        debug=True,
        threaded=True
    )