#!/usr/bin/env python3
"""
Demonstration of the complete 3-stage architecture with conversation context:
1. LLM analyzes intent with conversation context
2. App executes business action based on intent
3. LLM formats response with context awareness
4. Conversation context is updated for next turn
"""

from wholesale_agent.core.agent import WholesaleAgent

def demonstrate_architecture():
    """Demonstrate the full architecture with conversation context."""
    
    print("🚀 Wholesale AI Agent - Context-Aware Architecture Demo")
    print("=" * 60)
    print("\nArchitecture: LLM Intent Analysis → App Action → LLM Response → Context Update")
    print("\nNOTE: This demo shows the system architecture even without LLM API keys.")
    print("In production with LLM_API_KEY, the context system would work seamlessly.\n")
    
    agent = WholesaleAgent()
    
    # Demo queries that show contextual understanding
    queries = [
        "how much stock of gaming keyboard do we have?",
        "what about its price?", 
        "remove 2 units of it",
        "show me all products with low stock",
        "what about the wireless mouse?",
        "adjust its stock to 100 units"
    ]
    
    print("🎯 DEMONSTRATION QUERIES:")
    for i, query in enumerate(queries, 1):
        print(f"   {i}. {query}")
    
    print("\n" + "="*60)
    
    for i, query in enumerate(queries, 1):
        print(f"\n🔹 QUERY {i}: {query}")
        print("-" * 40)
        
        # Show conversation stats before processing
        stats = agent.get_conversation_stats()
        if stats['has_context']:
            print(f"📋 Context: {stats['recent_products']} recent products, last action: {stats['last_action']}")
        
        # Process the query
        try:
            response = agent.process_query(query)
            print(f"🤖 Response: {response}")
        except Exception as e:
            print(f"❌ Error: {e}")
        
        print()
    
    # Final conversation statistics
    print("="*60)
    print("📊 FINAL CONVERSATION STATISTICS:")
    final_stats = agent.get_conversation_stats()
    for key, value in final_stats.items():
        print(f"   • {key.replace('_', ' ').title()}: {value}")
    
    print(f"\n💡 ARCHITECTURE BENEFITS:")
    print("   ✅ Contextual understanding (references like 'it', 'its', 'that')")
    print("   ✅ Follow-up query support ('what about...', 'also check...')")
    print("   ✅ Conversation memory across multiple turns")
    print("   ✅ Clean separation: LLM for language, App for business logic")
    print("   ✅ Graceful fallbacks when LLM unavailable")
    print("   ✅ Console-friendly formatting (no markdown tables)")

if __name__ == "__main__":
    demonstrate_architecture()