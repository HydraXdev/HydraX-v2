module.exports = {
  apps: [{
    name: 'robust_slot_manager',
    script: '/root/HydraX-v2/robust_slot_manager.py',
    args: '--monitor',
    interpreter: 'python3',
    cwd: '/root/HydraX-v2',
    instances: 1,
    autorestart: true,
    watch: false,
    max_memory_restart: '200M',
    env: {
      PYTHONPATH: '/root/HydraX-v2:/root/HydraX-v2/src'
    },
    error_file: '/root/.pm2/logs/robust-slot-manager-error.log',
    out_file: '/root/.pm2/logs/robust-slot-manager-out.log',
    log_file: '/root/.pm2/logs/robust-slot-manager.log',
    time: true
  }]
};