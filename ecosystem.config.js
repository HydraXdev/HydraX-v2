module.exports = {
  apps: [
    {
      name: "hydrasocket-router",
      script: "venv/bin/gunicorn",
      args: "webapp_server_optimized:app -w 4 -k gevent --bind 0.0.0.0:8888 --timeout 90 --worker-connections 1000",
      cwd: "/root/HydraX-v2",
      instances: 1,
      autorestart: true,
      watch: false,
      max_memory_restart: "2G",
      max_restarts: 10,
      exp_backoff_restart_delay: 2000,
      out_file: "/var/log/hydrasocket/out.log",
      error_file: "/var/log/hydrasocket/err.log",
      merge_logs: true,
      kill_timeout: 5000,
      listen_timeout: 10000,
      env: {
        BITTEN_DB: "/root/HydraX-v2/bitten.db",
        PYTHONUNBUFFERED: "1",
        WS_ACK_WINDOW: "256",
        HYDRASOCKET_ENV: "production",
        FLASK_ENV: "production"
      }
    },
    {
      name: "elite_guard",
      script: "python3",
      args: "elite_guard_with_citadel.py",
      cwd: "/root/HydraX-v2",
      instances: 1,
      autorestart: true,
      watch: false
    },
    {
      name: "zmq_telemetry_bridge",
      script: "python3",
      args: "zmq_telemetry_bridge_debug.py",
      cwd: "/root/HydraX-v2",
      instances: 1,
      autorestart: true,
      watch: false
    },
    {
      name: "signals_zmq_to_redis",
      script: "python3",
      args: "tools/signals_zmq_to_redis.py",
      cwd: "/root/HydraX-v2",
      instances: 1,
      autorestart: true,
      watch: false
    },
    {
      name: "signals_to_alerts",
      script: "python3",
      args: "tools/signals_to_alerts.py",
      cwd: "/root/HydraX-v2",
      instances: 1,
      autorestart: true,
      watch: false
    },
    {
      name: "telegram_broadcaster_alerts",
      script: "python3",
      args: "tools/telegram_broadcaster_alerts.py",
      cwd: "/root/HydraX-v2",
      instances: 1,
      autorestart: true,
      watch: false
    },
    {
      name: "command_router",
      script: "python3",
      args: "command_router.py",
      cwd: "/root/HydraX-v2",
      instances: 1,
      autorestart: true,
      watch: false
    },
    {
      name: "confirm_listener",
      script: "python3",
      args: "confirm_listener.py",
      cwd: "/root/HydraX-v2",
      instances: 1,
      autorestart: true,
      watch: false
    },
    {
      name: "vcb_guard",
      script: "python3",
      args: "tools/vcb_guard.py",
      cwd: "/root/HydraX-v2",
      instances: 1,
      autorestart: true,
      watch: false
    },
    {
      name: "srl_guard",
      script: "python3",
      args: "tools/srl_guard.py",
      cwd: "/root/HydraX-v2",
      instances: 1,
      autorestart: true,
      watch: false
    }
  ]
}