module.exports = {
  apps: [{
    name: "webapp",
    script: "/root/HydraX-v2/start_webapp_gunicorn.sh",
    cwd: "/root/HydraX-v2",
    env: {
      BITTEN_DB: "/root/HydraX-v2/bitten.db",
      PYTHONUNBUFFERED: "1"
    },
    autorestart: true,
    watch: false,
    kill_timeout: 5000,
    restart_delay: 2000,
    max_restarts: 20,
    out_file: "/root/.pm2/logs/webapp-out.log",
    err_file: "/root/.pm2/logs/webapp-error.log"
  }]
}