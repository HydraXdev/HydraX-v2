#!/usr/bin/env python3
"""
Send fire command directly to port 5555
This bypasses Elite Guard and goes straight to EA
"""

import zmq
import json
import time
from datetime import datetime

context = zmq.Context()

# Connect to port 5555 where final_fire_publisher is PUSH server
pusher = context.socket(zmq.PULL)  # Wrong! EA is PULL, we need to match
# Actually, final_fire_publisher binds as PUSH, EA connects as PULL
# So we need to send to final_fire_publisher's queue

# Wait, let me check what final_fire_publisher does...
# It binds port 5555 as PUSH (server)
# EA connects to 5555 as PULL (client)
# To send to the queue, we need to connect as PUSH client? No...

# In ZMQ PUSH/PULL:
# - One side binds (server), other connects (client)
# - final_fire_publisher binds 5555 as PUSH
# - EA connects to 5555 as PULL
# - We can't inject into this stream directly!

# The only way is through the proper channel: Elite Guard format on 5557

print("This approach won't work - can't inject into PUSH/PULL stream")
print("The issue is that final_fire_publisher isn't receiving from 5557")
print("Need to debug the SUB connection")