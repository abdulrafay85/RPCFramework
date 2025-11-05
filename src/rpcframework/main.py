
from rpcframework.server.registry import RPCMethodRegistry

# settings = RegistrySettings(
#         host="127.0.0.1",
#         port=8000,
#         mount_path="/jsonrpc",
#     )

settings = {
    "host": "127.0.0.1",
    "port": 8000,
    "mount_path": "/jsonrpc",
}

rpc = RPCMethodRegistry(
    name="rpc",
    settings=settings,
)
# print(f"RPC Server: {rpc}")

# # --- Register example methods ------------------------------------------------
@rpc.register("add")
def add(a: float, b: float) -> float:
    """Add two numbers."""
    return a + b

@rpc.register("divide")
def divide(a: float, b: float) -> float:
    """Divide two numbers."""
    return a / b

if __name__ == "__main__":
    rpc.run(host="127.0.0.1", port=8001)  # ← 8001 ya 8080