# invoice_server.py
import asyncio
import uuid
from datetime import datetime

from rpcframework.server.registry import RPCMethodRegistry

# Simple in-memory DB (demo only)
INVOICES = {}  # invoice_id -> dict
UNPROCESSED_PAYMENTS = []  # just to simulate notifications

settings = {
    "host": "127.0.0.1",
    "port": 8002,
    "mount_path": "/jsonrpc",
}

rpc = RPCMethodRegistry(name="billing", settings=settings)

@rpc.register("create_invoice", description="Create an invoice. params: {client: str, amount: float}")
def create_invoice(client: str, amount: float):
    """Create invoice and return invoice_id"""
    try:
        amount = float(amount)
    except (TypeError, ValueError):
        raise ValueError("Invalid amount")

    invoice_id = str(uuid.uuid4())
    invoice = {
        "id": invoice_id,
        "client": client,
        "amount": amount,
        "created_at": datetime.utcnow().isoformat() + "Z",
        "paid": False,
    }
    INVOICES[invoice_id] = invoice
    return invoice

@rpc.register("get_invoice", description="Get invoice by id. params: {invoice_id: str}")
def get_invoice(invoice_id: str):
    inv = INVOICES.get(invoice_id)
    if not inv:
        # Use JSON-RPC server error factories in your framework; here raise generic
        raise ValueError("invoice not found")
    return inv

@rpc.register("list_invoices", description="List all invoices")
def list_invoices():
    return list(INVOICES.values())

@rpc.register("get_balance", description="Get total outstanding balance")
def get_balance():
    total = sum(inv["amount"] for inv in INVOICES.values() if not inv["paid"])
    return {"outstanding_balance": total, "count": len([i for i in INVOICES.values() if not i["paid"]])}

@rpc.register("process_payment", description="Notification to process payment asynchronously. params: {invoice_id: str, amount: float}")
async def process_payment(invoice_id: str, amount: float):
    """
    This method is designed to be used as a notification (id=None).
    Simulate asynchronous processing: mark invoice paid after delay.
    """
    # store for logging/demo
    UNPROCESSED_PAYMENTS.append({"invoice_id": invoice_id, "amount": amount})
    # simulate background work
    await asyncio.sleep(0.5)  # simulate IO / payment gateway
    inv = INVOICES.get(invoice_id)
    if inv and not inv["paid"] and float(amount) >= inv["amount"]:
        inv["paid"] = True
        inv["paid_at"] = datetime.utcnow().isoformat() + "Z"
        return {"status": "paid", "invoice_id": invoice_id}
    return {"status": "ignored", "invoice_id": invoice_id}

if __name__ == "__main__":
    print("Starting billing RPC server on http://127.0.0.1:8002/jsonrpc")
    rpc.run(host="127.0.0.1", port=8002)
