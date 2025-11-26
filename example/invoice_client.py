
# # invoice_client.py
import asyncio
# from typing import Dict
from rpcframework.client.rpc_client import RPCClient

# from rpcframework.client.client import JSONRPCTransport  # assume this is your transport class

# RPC_URL = "http://127.0.0.1:8002/jsonrpc"

# RPC_URL = "http://127.0.0.1:8002"

# transport = JSONRPCTransport(RPC_URL)

# # --- Extend transport with GET methods endpoint ---
# async def get_methods(transport: JSONRPCTransport):
#     """
#     Fetch available RPC methods from the server via GET /methods
#     """
#     try:
#         resp = await transport.get_methods()
#     except Exception as e:
#         raise RuntimeError(f"Failed to fetch methods: {e}") from e

#     # Return the list/dict of available methods
#     # return resp.get("result", {})
#     return resp


# async def invoice_management_demo():
#     """
#     Demonstrates creating invoices, fetching balances, and checking invoice status 
#     using the JSON-RPC transport client.
#     """
#     try:
#         # 1) Create two invoices (sequential)
#         inv1 = await transport.call_method("create_invoice", {"client": "ACME Corp", "amount": 150.0})
#         print("Created invoice 1:", inv1)

#         inv2 = await transport.call_method("create_invoice", {"client": "Beta LLC", "amount": 200.5})
#         print("Created invoice 2:", inv2)

#         # 2) Get outstanding balance
#         bal = await transport.call_method("get_balance")
#         print("Outstanding balance:", bal)

#         # 3) Optional: Batch fetch invoices (if transport supports batch)
#         # batch_calls = [
#         #     {"jsonrpc": "2.0", "method": "get_invoice", "params": {"invoice_id": inv1["id"]}, "id": "1"},
#         #     {"jsonrpc": "2.0", "method": "get_invoice", "params": {"invoice_id": inv2["id"]}, "id": "2"},
#         # ]
#         # batch_results = await transport.batch(batch_calls)
#         # print("Batch results:", batch_results)

#         # 4) Optional: Send payment notification for invoice1 (fire-and-forget)
#         # await transport.notify("process_payment", {"invoice_id": inv1["id"], "amount": inv1["amount"]})
#         # print("Sent payment notification for invoice1 (notification)")

#         # 5) After small delay, check invoice status
#         await asyncio.sleep(1.0)
#         inv1_after = await transport.call_method("get_invoice", {"invoice_id": inv1["id"]})
#         print("Invoice1 after payment attempt:", inv1_after)

#     finally:
#         await transport.close()


# # --- Demo client flow ---
# async def demo_flow():
#     # 1) Get list of methods
#     methods = await get_methods(transport)
#     print("Available RPC methods on server:")
#     print(f"methods: {methods}")
#     # for name, info in methods.items():
#     #     print(f" - {name}: {info.get('description', 'No description')}")

#     # # 2) Example: call a method if it exists
#     # if "get_balance" in methods:
#     #     balance = await transport.call("get_balance")
#     #     print("Outstanding balance:", balance)


# # Run demo
# if __name__ == "__main__":
#     asyncio.run(demo_flow())


# --- Discovery Client ---
async def discovery_demo():

    rpc_client = RPCClient()

    try:
        # methods = await rpc_client.find_agent("greet")
        # print("Available RPC method info:")
        # # Assuming methods is a dict, not a list
        # print(f"methods: {methods}")
        # # print(f"Name: {methods['name']}")
        # # print(f"Description: {methods.get('description', 'No description')}")

        res = await rpc_client.call('greet', {'name': 'rafay'})
        print(res)
        
    finally:
        # Remove or comment out close if not implemented
        pass
    

# Run demo
if __name__ == "__main__":
    asyncio.run(discovery_demo())
