module.exports = {
  apps: [{
    name: 'webapp',
    script: '/usr/local/bin/gunicorn',
    args: [
      'webapp_server_optimized:app',
      '-w', '2',  // Start with 2 workers (conservative)
      '-b', '0.0.0.0:8888',
      '--timeout', '120',
      '--access-logfile', '-',
      '--error-logfile', '-',
      '--preload'  // Load app before forking workers
    ],
    cwd: '/root/HydraX-v2',
    interpreter: 'none',  // Don't use node interpreter
    error_file: '/root/.pm2/logs/webapp-error.log',
    out_file: '/root/.pm2/logs/webapp-out.log',
    merge_logs: true,
    
    // Crash protection settings
    max_restarts: 5,  // Max 5 restarts
    min_uptime: '10s',  // Consider app crashed if it dies within 10s
    max_memory_restart: '500M',  // Restart if memory exceeds 500MB
    autorestart: true,
    
    // Exponential backoff for restarts
    restart_delay: 4000,  // 4 seconds initial delay
    exp_backoff_restart_delay: 100000,  // Max 100 seconds between restarts
    
    // Environment variables
    env: {
      PYTHONUNBUFFERED: '1',  // Ensure logs are not buffered
      PORT: '8888'
    },
    
    // Stop signal
    kill_timeout: 5000,  // Give 5 seconds for graceful shutdown
    listen_timeout: 3000,
    
    // Watch for file changes (disabled for production)
    watch: false,
    
    // PM2 clustering disabled (gunicorn handles workers)
    instances: 1,
    exec_mode: 'fork'
  }]
};