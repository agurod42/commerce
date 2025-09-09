#!/usr/bin/env python3
"""
Test script to demonstrate conversation context functionality.
Simulates the full flow with mock LLM responses.
"""

from wholesale_agent.core.conversation_context import ConversationContext
from wholesale_agent.core.intent_analyzer import IntentResult  
from wholesale_agent.core.action_executor import ActionResult

def simulate_conversation_flow():
    """Simulate a full conversation with context."""
    context = ConversationContext()
    
    print("🧠 Testing Conversation Context Flow")
    print("=" * 50)
    
    # Turn 1: Initial query about gaming keyboard stock
    print("\n1️⃣ TURN 1: Initial Query")
    query1 = "how much stock of gaming keyboard do we have?"
    print(f"User: {query1}")
    
    # Simulate intent analysis result
    intent1 = IntentResult(
        intent_type='inventory_query',
        confidence=0.9,
        entities={'product_name': 'gaming keyboard', 'action': 'check'},
        needs_clarification=False,
        raw_query=query1
    )
    
    # Simulate action execution result  
    action1 = ActionResult(
        action_type='inventory_query',
        success=True,
        message='Found gaming keyboard stock info',
        data=[{
            'name': 'gaming keyboard',
            'sku': 'KB-GAME-001',
            'current_stock': 25,
            'minimum_stock': 10,
            'wholesale_price': 45.99
        }]
    )
    
    response1 = "📦 Gaming Keyboard Stock Information:\n• SKU: KB-GAME-001\n• Current Stock: 25 units\n• Minimum Required: 10 units\n• Status: Well stocked ✅"
    
    print(f"Agent: {response1}")
    
    # Add to context
    context.add_turn(query1, intent1, action1, response1)
    
    # Turn 2: Contextual follow-up about price
    print("\n2️⃣ TURN 2: Contextual Follow-up (Price)")
    query2 = "what about its price?"
    print(f"User: {query2}")
    
    # Get context for this query
    ctx2 = context.get_context_for_query(query2)
    print(f"📋 Context Detected:")
    print(f"   • Recent Products: {ctx2.get('recent_products')}")
    print(f"   • Is Follow-up: {ctx2.get('is_follow_up')}")
    print(f"   • Refers to Previous: {ctx2.get('refers_to_previous')}")
    
    # With context, system should understand "its" refers to gaming keyboard
    intent2 = IntentResult(
        intent_type='price_query',
        confidence=0.9,
        entities={
            'product_name': 'gaming keyboard',  # Inferred from context
            'action': 'check_price'
        },
        needs_clarification=False,
        raw_query=query2
    )
    
    action2 = ActionResult(
        action_type='price_query', 
        success=True,
        message='Retrieved pricing info',
        data={
            'name': 'gaming keyboard',
            'wholesale_price': 45.99,
            'retail_price': 79.99,
            'margin': 42.9
        }
    )
    
    response2 = "💰 Gaming Keyboard Pricing:\n• Wholesale Price: $45.99\n• Suggested Retail: $79.99\n• Margin: 42.9%"
    
    print(f"Agent: {response2}")
    
    context.add_turn(query2, intent2, action2, response2)
    
    # Turn 3: Contextual inventory management
    print("\n3️⃣ TURN 3: Contextual Inventory Management")
    query3 = "remove 2 units of it"
    print(f"User: {query3}")
    
    ctx3 = context.get_context_for_query(query3)
    print(f"📋 Context Detected:")
    print(f"   • Recent Products: {ctx3.get('recent_products')}")
    print(f"   • Refers to Previous: {ctx3.get('refers_to_previous')}")
    
    # System understands "it" refers to gaming keyboard from context
    intent3 = IntentResult(
        intent_type='inventory_management',
        confidence=0.9,
        entities={
            'product_name': 'gaming keyboard',  # Inferred from context
            'quantity': '2',
            'action': 'remove'
        },
        needs_clarification=False,
        raw_query=query3
    )
    
    action3 = ActionResult(
        action_type='inventory_management',
        success=True,
        message='Successfully removed 2 units',
        data={
            'product_name': 'gaming keyboard',
            'operation': 'remove',
            'quantity': 2,
            'previous_stock': 25,
            'new_stock': 23
        }
    )
    
    response3 = "✅ Inventory Updated:\n• Product: Gaming Keyboard\n• Removed: 2 units\n• Previous Stock: 25\n• New Stock: 23\n• Status: Still well stocked"
    
    print(f"Agent: {response3}")
    
    context.add_turn(query3, intent3, action3, response3)
    
    # Show final conversation stats
    print("\n📊 FINAL CONVERSATION STATS")
    print("=" * 30)
    stats = context.get_stats()
    for key, value in stats.items():
        print(f"• {key.replace('_', ' ').title()}: {value}")
    
    print(f"\n🧠 Recent Products in Memory: {context.last_mentioned_products}")
    print(f"💭 Conversation Summary: {context._get_conversation_summary()}")

if __name__ == "__main__":
    simulate_conversation_flow()