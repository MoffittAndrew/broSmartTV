host_ip = '0.0.0.0'
port = 9559

import asyncio
from websockets.asyncio.server import serve
import json

async def screen_share(websocket):
    print("Connected")
    connected = True
    while connected:
        async for message in websocket.recv_streaming():
            print(message)
            decoded = json.loads(message)
            if "leaving" in decoded and decoded["leaving"]:
                connected = False
    
    print("Disconnected")

async def main():
    async with serve(screen_share, "localhost", port) as server:
        await server.serve_forever()

if __name__ == "__main__":
    asyncio.run(main())
