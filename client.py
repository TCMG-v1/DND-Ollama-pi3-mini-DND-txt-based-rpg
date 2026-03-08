#!/usr/bin/env python3
"""
================================================================
  AI DUNGEON MASTER — Player Client
  Run this after SSH-ing into the Pi:
    python3 ~/dnd_game/client.py

  The server must already be running (start_server.sh)
================================================================
"""

import asyncio
import os
import sys
from dotenv import load_dotenv

load_dotenv()

HOST = os.getenv("DND_HOST", "127.0.0.1")
PORT = int(os.getenv("DND_PORT", "4000"))

async def main():
    print("═" * 78)
    print("  CONNECTING TO AI DUNGEON MASTER...")
    print(f"  Server: {HOST}:{PORT}")
    print("═" * 78)

    try:
        reader, writer = await asyncio.open_connection(HOST, PORT)
    except ConnectionRefusedError:
        print(f"\n  Could not connect to server at {HOST}:{PORT}")
        print("  Make sure the server is running: bash ~/dnd_game/start_server.sh")
        sys.exit(1)

    # Read from server and write to stdout
    async def receive():
        try:
            while True:
                data = await reader.read(4096)
                if not data:
                    print("\n  [Disconnected from server]")
                    break
                print(data.decode("utf-8", errors="replace"), end="", flush=True)
        except Exception:
            pass

    # Read from stdin and send to server
    async def send():
        try:
            loop = asyncio.get_event_loop()
            while True:
                line = await loop.run_in_executor(None, sys.stdin.readline)
                if not line:
                    break
                writer.write(line.encode("utf-8"))
                await writer.drain()
        except Exception:
            pass
        finally:
            writer.close()

    await asyncio.gather(receive(), send())

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n  Disconnected. Your progress has been saved.")
