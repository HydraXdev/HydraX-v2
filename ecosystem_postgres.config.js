// BITTEN v2.1 - PM2 Ecosystem Configuration with Postgres Integration
// Date: 2025-09-16
// Purpose: Production PM2 configuration for Postgres-enabled BITTEN system

module.exports = {
  apps: [
    // Existing core services (keep running)
    {
      name: "elite_guard",
      script: "elite_guard_with_citadel.py",
      cwd: "/root/HydraX-v2",
      instances: 1,
      autorestart: true,
      max_restarts: 10,
      min_uptime: "10s",
      max_memory_restart: "1G",
      env: {
        PYTHONPATH: "/root/HydraX-v2",
        NODE_ENV: "production",
      },
    },
    {
      name: "command_router",
      script: "command_router.py",
      cwd: "/root/HydraX-v2",
      instances: 1,
      autorestart: true,
      max_restarts: 10,
      min_uptime: "10s",
    },
    {
      name: "confirm_listener",
      script: "confirm_listener.py",
      cwd: "/root/HydraX-v2",
      instances: 1,
      autorestart: true,
      max_restarts: 10,
      min_uptime: "10s",
    },
    {
      name: "relay_to_telegram",
      script: "elite_guard_zmq_relay.py",
      cwd: "/root/HydraX-v2",
      instances: 1,
      autorestart: true,
      max_restarts: 10,
      min_uptime: "10s",
    },
    {
      name: "zmq_telemetry_bridge",
      script: "zmq_telemetry_bridge_debug.py",
      cwd: "/root/HydraX-v2",
      instances: 1,
      autorestart: true,
      max_restarts: 10,
      min_uptime: "10s",
    },
    {
      name: "enhanced_slot_manager",
      script: "robust_slot_manager.py",
      cwd: "/root/HydraX-v2",
      args: "--monitor",
      instances: 1,
      autorestart: true,
      max_restarts: 10,
      min_uptime: "10s",
    },

    // NEW: Postgres Integration Services
    {
      name: "postgres_projector",
      script: "services/postgres_projector.py",
      cwd: "/root/HydraX-v2",
      instances: 1,
      autorestart: true,
      max_restarts: 10,
      min_uptime: "30s",
      max_memory_restart: "512M",
      env: {
        PYTHONPATH: "/root/HydraX-v2",
        POSTGRES_DSN:
          "postgresql://bitten:bitten_secure_2025@localhost:5432/bitten",
      },
      error_file: "/root/HydraX-v2/logs/postgres_projector_error.log",
      out_file: "/root/HydraX-v2/logs/postgres_projector_out.log",
      log_file: "/root/HydraX-v2/logs/postgres_projector.log",
    },

    // Enhanced WebApp with Admin Endpoints
    {
      name: "webapp",
      script: "webapp_server_optimized.py",
      cwd: "/root/HydraX-v2",
      instances: 1,
      autorestart: true,
      max_restarts: 10,
      min_uptime: "10s",
      max_memory_restart: "1G",
      env: {
        PYTHONPATH: "/root/HydraX-v2",
        POSTGRES_DSN:
          "postgresql://bitten:bitten_secure_2025@localhost:5432/bitten",
        FLASK_ENV: "production",
      },
    },

    // Materialized View Refresher (NEW)
    {
      name: "mv_refresher",
      script: "services/mv_refresher.py",
      cwd: "/root/HydraX-v2",
      instances: 1,
      autorestart: true,
      max_restarts: 10,
      min_uptime: "10s",
      env: {
        PYTHONPATH: "/root/HydraX-v2",
        POSTGRES_DSN:
          "postgresql://bitten:bitten_secure_2025@localhost:5432/bitten",
      },
    },
  ],

  // Deployment configuration
  deploy: {
    production: {
      user: "root",
      host: "134.199.204.67",
      ref: "origin/main",
      repo: "git@github.com:your-repo/bitten.git",
      path: "/root/HydraX-v2",
      "pre-deploy-local": "",
      "post-deploy":
        "pip install -r requirements_postgres.txt && pm2 reload ecosystem_postgres.config.js --env production",
      "pre-setup": "",
      ssh_options: "ForwardAgent=yes",
    },
  },
};
