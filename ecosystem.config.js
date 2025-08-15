module.exports = {
  apps: [
    {
      name: "webapp",
      script: "python3",
      args: "webapp_server_optimized.py",
      cwd: "/root/HydraX-v2",
      instances: 1,
      autorestart: true,
      watch: false,
      max_memory_restart: "1G",
      env: {
        BITTEN_DB: "/root/HydraX-v2/bitten.db",
        PYTHONUNBUFFERED: "1"
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