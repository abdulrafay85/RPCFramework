"""
RPC Framework — Customer Support Agent Demo
================================================

This script demonstrates the full power of your decentralized agent network:

1. Client discovers the "customer_support" agent using the centralized Discovery Service
2. No hard-coded URLs — fully dynamic, resilient, and scalable
3. Uses SmartRetryClient under the hood (circuit breaker, retries, health-aware routing)
4. Supports natural language in Urdu, English, Hindi, Roman Urdu

Run this after starting:
→ discovery_service.py
→ openai_customer_support_agent.py (on port 8004)

Then watch the magic: just say anything, and AI responds like a real human!
"""

import asyncio
from rpcframework.client.rpc_client import RPCClient


async def main(service_name: str) -> None:
    # Initialize client — automatically connects to Discovery Service
    print("Initializing RPC Client (with auto-discovery)...")
    client = RPCClient()  # discovery_url defaults to http://127.0.0.1:8000

    # ──────────────────────────────────────────────────────────────
    # Step 1: Explicit Discovery — Find the agent dynamically
    # ──────────────────────────────────────────────────────────────
    # print(f"\nDiscovering agent: '{service_name}' via Discovery Service...")
    # try:
    #     agent_info = await client.find_agent(service_name)
    #     print(f"Agent discovered successfully!")
    #     print(f"   • Name       : {agent_info.get('name')}")
    #     print(f"   • Endpoint   : {agent_info.get('endpoint')}")
    #     print(f"   • Capabilities: {', '.join(agent_info.get('capabilities', []))}")
    #     print("   → Ready to chat!")
        
    #     # Agent found successfully return agent_info 
    #     return agent_info
    
    # except Exception as e:
    #     print(f"Discovery failed: {e}")
    #     print("   Make sure discovery_service.py and the support agent are running.")

    # print("\n" + "="*70)
    # print("   LIVE CUSTOMER SUPPORT CHAT (Powered by OpenAI + Your Framework)")
    # print("="*70)

    # # ──────────────────────────────────────────────────────────────
    # # Step 2: Interactive chat with real-time RPC calls
    # # ──────────────────────────────────────────────────────────────
    test_messages = [
        "Bro, my payment didn’t go through, invoice #INV-789",
        "The app isn’t opening, there’s a login issue",
        "Hey, please refund it, I didn’t like the product",
        "Order kab tak deliver hoga?",
        "Thanks bhai, bohat achhi service hai",
        "Assalamu Alaikum, my account has been locked",
        "ميرے انوائس میں غلط اماؤنٹ ہے",
        "Bhai ye app bohat slow chal raha hai",
    ]

    for msg in test_messages:
        print(f"\nYou → {msg}")
        try:
            response = await client.call(service_name, {"message": msg, "user_id": "guest", "session_id": None})
            print(f"Support → {response}")

            # Optional: show which expert handled it
            if "handled_by" in response:
                print(f"          (Handled by: {response['handled_by']})")

        except Exception as e:
            print(f"RPC Call Failed → {e}")

    # # ──────────────────────────────────────────────────────────────
    # # Bonus: Show health of the agent
    # # ──────────────────────────────────────────────────────────────
    print("\n" + "─"*70)
    try:
        health = await client.call("support_health")
        print(f"Agent Health Check: {health}")
    except:
        print("Health endpoint not available (optional)")

    print("\nDemo complete! Your framework just replaced a $50K/month support team.")


if __name__ == "__main__":
    asyncio.run(main(service_name="customer_support"))