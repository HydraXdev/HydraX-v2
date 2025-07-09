module.exports = {
  apps: [
    {
      name: 'bitten-webapp',
      script: 'webapp_server.py',
      interpreter: 'python3',
      cwd: '/root/HydraX-v2',
      instances: 1,
      autorestart: true,
      watch: false,
      max_memory_restart: '2G',
      env: {
        NODE_ENV: 'production',
        PYTHONPATH: '/root/HydraX-v2',
        FLASK_APP: 'webapp_server.py',
        FLASK_ENV: 'production',
        LOG_LEVEL: 'INFO',
        WEBAPP_PORT: '8888',
        WEBAPP_HOST: '0.0.0.0',
        WEBAPP_DEBUG: 'false',
        MONITORING_ENABLED: 'true'
      },
      // Logging configuration
      log_date_format: 'YYYY-MM-DD HH:mm:ss Z',
      log_file: '/var/log/bitten/webapp/combined.log',
      out_file: '/var/log/bitten/webapp/out.log',
      error_file: '/var/log/bitten/webapp/error.log',
      log_type: 'json',
      
      // Process management
      min_uptime: '10s',
      max_restarts: 10,
      restart_delay: 4000,
      
      // Health monitoring
      health_check_grace_period: 30000,
      health_check_fatal_exceptions: true,
      
      // Performance monitoring
      pmx: true,
      
      // Advanced features
      source_map_support: false,
      instance_var: 'INSTANCE_ID',
      
      // Error handling
      exp_backoff_restart_delay: 100,
      
      // Process limits
      kill_timeout: 5000,
      listen_timeout: 3000,
      
      // Environment specific settings
      env_production: {
        NODE_ENV: 'production',
        WEBAPP_DEBUG: 'false',
        LOG_LEVEL: 'INFO'
      },
      env_development: {
        NODE_ENV: 'development',
        WEBAPP_DEBUG: 'true',
        LOG_LEVEL: 'DEBUG'
      }
    },
    {
      name: 'bitten-monitoring',
      script: 'src/monitoring/main_monitor.py',
      interpreter: 'python3',
      cwd: '/root/HydraX-v2',
      instances: 1,
      autorestart: true,
      watch: false,
      max_memory_restart: '1G',
      env: {
        NODE_ENV: 'production',
        PYTHONPATH: '/root/HydraX-v2/src',
        LOG_LEVEL: 'INFO',
        MONITORING_CONFIG: '/etc/bitten/monitoring.conf'
      },
      // Logging configuration
      log_date_format: 'YYYY-MM-DD HH:mm:ss Z',
      log_file: '/var/log/bitten/monitoring/combined.log',
      out_file: '/var/log/bitten/monitoring/out.log',
      error_file: '/var/log/bitten/monitoring/error.log',
      log_type: 'json',
      
      // Process management
      min_uptime: '10s',
      max_restarts: 10,
      restart_delay: 4000,
      
      // Health monitoring
      health_check_grace_period: 30000,
      health_check_fatal_exceptions: true,
      
      // Performance monitoring
      pmx: true,
      
      // Process limits
      kill_timeout: 5000,
      listen_timeout: 3000
    }
  ],
  
  // PM2 deployment configuration
  deploy: {
    production: {
      user: 'root',
      host: 'localhost',
      ref: 'origin/main',
      repo: 'git@github.com:bitten-trading/HydraX-v2.git',
      path: '/root/HydraX-v2',
      'post-deploy': 'npm install && pm2 reload pm2.config.js --env production',
      'pre-setup': 'apt-get update && apt-get install -y python3 python3-pip',
      'post-setup': 'pip3 install -r requirements.txt'
    }
  }
};