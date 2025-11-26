# examples/openai_customer_support_agent.py
"""
OpenAI-Powered Customer Support Agent (Urdu + English + Hindi)

Features:
- Chat naturally, just like WhatsApp conversations
- Handles billing, technical support, refunds, deliveries—everything end-to-end
- Intelligent routing powered by OpenAI GPT-5
- Automatically registers with your RPCFramework
- Fully flexible, no vendor lock-in

Run:    python examples/openai_customer_support_agent.py
Call:   client.call("customer_support", {"message": "My payment didn't go through"})
"""

import asyncio
import os
from rpcframework.schemas import RPCResponse

from datetime import datetime, timezone
from typing import Dict, Any
from agents import set_default_openai_client, set_tracing_disabled

# ─────────────────────────────────────────────
# 1. OpenAI Agent SDK
# ─────────────────────────────────────────────
from agents import Agent, Runner, AsyncOpenAI, OpenAIChatCompletionsModel, RunConfig

# from agents.model_settings import ModelSettings
from rpcframework.server.registry import RPCMethodRegistry, RegistrySettings

# ─────────────────────────────────────────────
# 2. Environment & Client Setup
# ─────────────────────────────────────────────
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY is not set in your environment.")

external_client = AsyncOpenAI(
    api_key=GEMINI_API_KEY,
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/"
)

model = OpenAIChatCompletionsModel(
    model="gemini-2.5-flash",
    openai_client=external_client
)

config = RunConfig(
    model=model,
    model_provider=external_client,
)

# Disable tracing for OpenAI 
set_tracing_disabled(True)

# ─────────────────────────────────────────────
# 3. Expert Agents
# ─────────────────────────────────────────────
billing_expert = Agent(
    name="BillingExpert",
    instructions="""
    You are a super polite billing support agent.
    Handle: invoices, payments, refunds, pricing, discounts.
    Always be empathetic and professional.
    """
)

tech_expert = Agent(
    name="TechSupportExpert",
    instructions="""
    You are a technical support genius.
    Fix login issues, bugs, API errors, app crashes, etc.
    Give step-by-step solutions.
    """
)

refund_expert = Agent(
    name="RefundExpert",
    instructions="""
    You handle refund requests.
    Be kind, ask for order ID, and confirm policy.
    Never approve fake requests.
    """
)

# ─────────────────────────────────────────────
# 4. Main Support Router
# ─────────────────────────────────────────────
support_router = Agent(
    name="PakSupportPro",
    instructions="""
    You are Pakistan's best AI customer support agent.
    Speak fluent Urdu, Roman Urdu, English, and Hindi.
    Be super friendly, patient, and helpful.

    Route queries:
    - Payment, invoice, bill, refund → billing_expert or refund_expert
    - Login, app not working, error, bug → tech_expert
    - Delivery, shipping → respond yourself
    - Greeting, thanks → reply warmly

    Always end with: "Kuch aur madad chahiye? Main yahan hoon"
    """,
    tools=[
        billing_expert.as_tool("billing_help", "Billing/payment issues"),
        tech_expert.as_tool("tech_help", "Technical problems"),
        refund_expert.as_tool("process_refund", "Handle refund requests")
    ]
)

# ─────────────────────────────────────────────
# 5. Customer Support Function
# ─────────────────────────────────────────────
async def customer_support(message: str, user_id: str = "guest", session_id: str = None) -> Dict[str, Any]:
    print(f"Customer message: {message}")
    timestamp = datetime.now(timezone.utc).isoformat()

    result = await Runner.run(
        support_router,
        message,
        context={
            "user_id": user_id,
            "session_id": session_id or "new",
            "timestamp": timestamp,
        },
        run_config=config,
    )

    return {
        "status": "success",
        "reply": result.final_output,
        "handled_by": result.last_agent.name or "main_agent",
        "confidence": "high",
        "tip": "Kuch aur madad chahiye? Main yahan hoon"
    }

    # return RPCResponse(
    #     result={
    #         "reply": result.final_output,
    #         "handled_by": "billing_expert",
    #         "language_detected": "urdu"
    #     },
    #     id=req_id  # important!
    # ).dict(exclude_none=True)



# ─────────────────────────────────────────────
# 6. RPC Registry Setup
# ─────────────────────────────────────────────
registry = RPCMethodRegistry(
    name="PakSupport AI Agent",
    settings=RegistrySettings(
        host="127.0.0.1",
        port=8004,
        discovery_url="http://127.0.0.1:8000",
        auto_register=True
    )
)

# Version 1
@registry.register(
    name="customer_support",
    description="Full AI customer support (Urdu/English/Hindi) — WhatsApp style"
)
async def rpc_customer_support(message: str, user_id: str = "user123", session_id: str = None):
    return await customer_support(message, user_id, session_id)

# # Version 2
# @registry.register(name="customer_support", description="AI Customer Support in Urdu/English")
# async def rpc_customer_support(message: str, user_id: str = "guest", session_id: str = None):
#     reply_data = await customer_support(message, user_id, session_id)
    
#     # Return just the reply_data, not wrapped in a JSON-RPC response
#     return reply_data


@registry.register(description="Support agent health check")
def support_health():
    print(f"Methods registered: {registry.list_methods()}")
    return {
        "status": "ready_to_help",
        "language": "Urdu, English, Hindi",
        "model": "gpt-5",
        "message": "Assalam-o-Alaikum! Main aapki madad ke liye hazir hoon"
    }    



# ─────────────────────────────────────────────
# 7. Launch Server
# ─────────────────────────────────────────────
if __name__ == "__main__":
    print("="*70)
    print("PAKISTAN'S BEST AI CUSTOMER SUPPORT AGENT IS LIVE")
    print("Server: http://127.0.0.1:8004/jsonrpc")
    print("Call: customer_support('Bhai app crash ho raha hai')")
    print("Languages: Urdu, English, Hindi, Roman Urdu")
    print("="*70)
    registry.run(port=8004)

