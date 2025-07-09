
import asyncio
import websockets
import json
import subprocess
from datetime import datetime

class WebSocketAgent:
    def __init__(self):
        self.clients = set()
        self.commands_processed = 0
    
    async def handle_client(self, websocket, path):
        """Handle WebSocket client connections"""
        self.clients.add(websocket)
        try:
            async for message in websocket:
                try:
                    data = json.loads(message)
                    result = await self.execute_command(data)
                    await websocket.send(json.dumps(result))
                except Exception as e:
                    await websocket.send(json.dumps({'error': str(e)}))
        finally:
            self.clients.remove(websocket)
    
    async def execute_command(self, data):
        """Execute command asynchronously"""
        command = data.get('command')
        command_type = data.get('type', 'powershell')
        
        self.commands_processed += 1
        
        if command_type == 'powershell':
            proc = await asyncio.create_subprocess_exec(
                'powershell', '-Command', command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
        else:
            proc = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
        
        stdout, stderr = await proc.communicate()
        
        return {
            'success': True,
            'stdout': stdout.decode(),
            'stderr': stderr.decode(),
            'returncode': proc.returncode,
            'timestamp': datetime.now().isoformat(),
            'agent_id': 'websocket_5557'
        }

agent = WebSocketAgent()

# Start WebSocket server
start_server = websockets.serve(agent.handle_client, "0.0.0.0", 5557)

print("WebSocket Agent starting on port 5557...")
asyncio.get_event_loop().run_until_complete(start_server)
asyncio.get_event_loop().run_forever()
