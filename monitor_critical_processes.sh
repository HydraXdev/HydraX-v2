#!/bin/bash
# Critical Process Monitor - Alerts and auto-restarts if firestore_sync stops

CRITICAL_PROCESSES=("firestore_sync" "api_server" "unified_relay")

for process in "${CRITICAL_PROCESSES[@]}"; do
    STATUS=$(pm2 jlist | jq -r ".[] | select(.name==\"$process\") | .pm2_env.status")
    
    if [ "$STATUS" != "online" ]; then
        echo "🚨 CRITICAL: $process is $STATUS - AUTO-RESTARTING"
        pm2 restart $process
        pm2 save
        
        # Log the incident
        echo "$(date): $process was $STATUS - restarted" >> /root/HydraX-v2/critical_process_restarts.log
    fi
done
