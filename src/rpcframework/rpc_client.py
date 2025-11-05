import asyncio
from rpcframework.client.client import JSONRPCTransport

transport = JSONRPCTransport("http://127.0.0.1:8001/jsonrpc")


async def call_add(x, y):
    try:
        result = await transport.call_method("add", [x, y])
        print(f"result: {result}")
    except Exception as e:
        print(f"Error: {e}")

async def call_divide(x, y):
    try:
        result = await transport.call_method("divide", [x, y])
        print(f"result: {result}")
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    
    # asyncio.run(call_add(3, 4))
    asyncio.run(call_divide(10, 2))
