# invoice_client.py
import asyncio

from rpcframework.client.client import JSONRPCTransport  # assume this is your transport class

RPC_URL = "http://127.0.0.1:8002/jsonrpc"
transport = JSONRPCTransport(RPC_URL)

async def demo_flow():
    try:
        # 1) Create two invoices (sequential)
        inv1 = await transport.call_method("create_invoice", {"client": "ACME Corp", "amount": 150.0})
        print("Created invoice 1:", inv1)

        inv2 = await transport.call_method("create_invoice", {"client": "Beta LLC", "amount": 200.5})
        print("Created invoice 2:", inv2)

        # 2) Get outstanding balance
        bal = await transport.call_method("get_balance")
        print("Outstanding balance:", bal)

        ## 3) Batch: fetch both invoices in one request (if transport supports batch)
        ## prepare batch calls according to JSON-RPC batch format
        # batch_calls = [
        #     {"jsonrpc": "2.0", "method": "get_invoice", "params": {"invoice_id": inv1["id"]}, "id": "1"},
        #     {"jsonrpc": "2.0", "method": "get_invoice", "params": {"invoice_id": inv2["id"]}, "id": "2"},
        # ]
        # batch_results = await transport.batch(batch_calls)
        # print("Batch results:", batch_results)

        ## 4) Send a notification to process a payment for invoice1 (fire-and-forget)
        ## notifications should have id = None; using transport.notify helper
        # await transport.notify("process_payment", {"invoice_id": inv1["id"], "amount": inv1["amount"]})
        # print("Sent payment notification for invoice1 (notification)")

        # 5) After small delay, check invoice status
        await asyncio.sleep(1.0)
        inv1_after = await transport.call_method("get_invoice", {"invoice_id": inv1["id"]})
        print("Invoice1 after payment attempt:", inv1_after)

    finally:
        await transport.close()

if __name__ == "__main__":
    asyncio.run(demo_flow())
