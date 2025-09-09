"""
LLM-powered response formatter for wholesale agent.
Takes structured data and formats it into beautiful, user-friendly responses.
"""
import json
import logging
from typing import Dict, Any, Optional

from .llm_client import LLMClient
from .action_executor import ActionResult


class ResponseFormatter:
    """LLM-powered response formatter."""
    
    def __init__(self, llm_client: Optional[LLMClient] = None):
        self.llm_client = llm_client or LLMClient()
        self.logger = logging.getLogger(__name__)
    
    def format_response(self, user_query: str, action_result: ActionResult, context: Dict[str, Any] = None) -> str:
        """Format action result into a beautiful user-friendly response."""
        try:
            # Handle clarification requests directly
            if action_result.action_type == "clarification":
                return action_result.message
            
            # Handle errors
            if not action_result.success and action_result.error:
                return self._format_error_response(action_result.error)
            
            # Use LLM to format successful results
            return self._llm_format_response(user_query, action_result, context)
            
        except Exception as e:
            self.logger.error(f"Response formatting error: {str(e)}")
            return self._fallback_response(action_result)
    
    def _llm_format_response(self, user_query: str, action_result: ActionResult, context: Dict[str, Any] = None) -> str:
        """Use LLM to format the response beautifully."""
        system_prompt = """You are a professional assistant for a wholesale business management system. 
Your job is to take structured business data and present it in a clear, helpful, and console-friendly way to users.

CRITICAL FORMATTING RULES for console display:
- DO NOT use markdown tables, they don't render in console
- DO NOT use markdown headers (# ## ###), use simple text with colons
- Use simple bullet points with • or - 
- Use simple numbered lists with 1. 2. 3.
- Use spacing and indentation for clarity, not markdown formatting
- Present data in plain text format that looks good in a terminal

Content Guidelines:
- Be professional but friendly
- Present data clearly with bullet points and spacing
- Include relevant business insights
- If showing products, include key details like SKU, stock levels, and prices
- For inventory operations, confirm what was done and show the result
- Be concise but informative
- Use emojis sparingly and only when they add clarity (📦 for inventory, 💰 for prices, ⚠️ for alerts)

EXAMPLE GOOD FORMATTING:
📦 Product Information:
• SKU: ABC-123
• Name: Product Name
• Stock: 50 units
• Price: $25.99

Business Insight: Stock levels are healthy.

EXAMPLE BAD FORMATTING (DO NOT USE):
| SKU | Name | Stock |
|-----|------|-------|
| ABC | Product | 50 |

Do NOT include any JSON, markdown tables, or technical data structures in your response."""

        # Prepare data for the LLM
        data_str = self._format_data_for_llm(action_result.data) if action_result.data else "No data"
        
        # Add context information if available
        context_info = ""
        if context and context.get('has_history'):
            context_parts = []
            if context.get('is_follow_up'):
                context_parts.append("This appears to be a follow-up to a previous query")
            if context.get('recent_products'):
                context_parts.append(f"Recently discussed products: {', '.join(context['recent_products'][-3:])}")
            if context_parts:
                context_info = f"\nConversation Context: {'; '.join(context_parts)}"
        
        prompt = f"""User Query: "{user_query}"{context_info}

Action Type: {action_result.action_type}
Success: {action_result.success}
Message: {action_result.message}

Data:
{data_str}

Please format this information into a helpful, well-structured response for the user. Focus on presenting the data clearly and providing any relevant business insights.
If this is a follow-up query, acknowledge the context naturally in your response."""

        try:
            response = self.llm_client.generate_response(prompt, system_prompt)
            return response.strip()
        except Exception as e:
            self.logger.error(f"LLM formatting error: {str(e)}")
            return self._fallback_response(action_result)
    
    def _format_data_for_llm(self, data: Any) -> str:
        """Format data in a way that's easy for LLM to process."""
        if data is None:
            return "No data available"
        
        try:
            if isinstance(data, (dict, list)):
                return json.dumps(data, indent=2, default=str)
            else:
                return str(data)
        except Exception:
            return str(data)
    
    def _format_error_response(self, error: str) -> str:
        """Format error responses in a user-friendly way."""
        if "insufficient stock" in error.lower():
            return f"❌ {error}"
        elif "not found" in error.lower():
            return f"🔍 {error}"
        elif "invalid" in error.lower():
            return f"⚠️ {error}"
        else:
            return f"❌ I encountered an issue: {error}"
    
    def _fallback_response(self, action_result: ActionResult) -> str:
        """Fallback response when LLM formatting fails."""
        if action_result.action_type == "clarification":
            return action_result.message
        
        if not action_result.success:
            return f"❌ {action_result.error or 'Operation failed'}"
        
        # Generate basic structured response based on action type
        if action_result.action_type == "inventory_query":
            return self._fallback_inventory_response(action_result.data)
        elif action_result.action_type == "inventory_management":
            return self._fallback_inventory_management_response(action_result.data)
        elif action_result.action_type == "inventory_history":
            return self._fallback_inventory_history_response(action_result.data)
        elif action_result.action_type == "product_search":
            return self._fallback_product_search_response(action_result.data)
        elif action_result.action_type == "analytics":
            return self._fallback_analytics_response(action_result.data)
        elif action_result.action_type == "help_capabilities":
            return self._fallback_help_capabilities_response(action_result.data)
        elif action_result.action_type == "low_stock_alert":
            return self._fallback_low_stock_response(action_result.data)
        else:
            return f"✅ {action_result.message or 'Operation completed successfully'}"
    
    def _fallback_inventory_response(self, data: Any) -> str:
        """Fallback response for inventory queries."""
        if not data:
            return "📦 No inventory data found."
        
        if isinstance(data, list) and data:
            response_parts = [f"📦 Product Information ({len(data)} items):"]
            response_parts.append("")  # Empty line for spacing
            
            for i, item in enumerate(data[:10], 1):  # Show first 10
                name = item.get('name', 'Unknown')
                sku = item.get('sku', '')
                stock = item.get('current_stock', 0)
                wholesale_price = item.get('wholesale_price', 0)
                
                response_parts.append(f"{i}. **{name}**")
                response_parts.append(f"   • SKU: {sku}")
                response_parts.append(f"   • Stock: {stock} units")
                if wholesale_price:
                    response_parts.append(f"   • Price: ${float(wholesale_price):.2f}")
                response_parts.append("")  # Empty line between products
                
            if len(data) > 10:
                response_parts.append(f"... and {len(data) - 10} more products")
                
            response_parts.append("💡 Business Insight: Product information retrieved successfully.")
            return "\n".join(response_parts)
        
        elif isinstance(data, dict):
            if 'total_products' in data:
                # Overview response
                total = data.get('total_products', 0)
                low_stock = data.get('low_stock_count', 0)
                out_of_stock = data.get('out_of_stock_count', 0)
                
                response_parts = [f"📦 Inventory Overview:"]
                response_parts.append("")
                response_parts.append(f"• Total Products: {total:,}")
                response_parts.append(f"• Low Stock Items: {low_stock}")
                response_parts.append(f"• Out of Stock Items: {out_of_stock}")
                response_parts.append("")
                response_parts.append("💡 Business Insight: Your inventory includes a healthy mix of products across categories.")
                return "\n".join(response_parts)
        
        return "📦 Inventory information retrieved successfully."
    
    def _fallback_inventory_management_response(self, data: Any) -> str:
        """Fallback response for inventory management."""
        if isinstance(data, dict):
            if data.get('success'):
                return f"✅ {data.get('message', 'Inventory operation completed successfully')}"
            else:
                return f"❌ {data.get('error', 'Inventory operation failed')}"
        return "Inventory operation completed."
    
    def _fallback_product_search_response(self, data: Any) -> str:
        """Fallback response for product search."""
        if isinstance(data, list) and data:
            response_parts = [f"🔍 Product Search Results ({len(data)} items):"]
            response_parts.append("")
            
            for i, product in enumerate(data[:10], 1):
                name = product.get('name', 'Unknown')
                sku = product.get('sku', '')
                wholesale_price = product.get('wholesale_price', 0)
                retail_price = product.get('retail_price', 0)
                stock = product.get('current_stock', 0)
                category = product.get('category', 'Unknown')
                
                response_parts.append(f"{i}. **{name}**")
                response_parts.append(f"   • SKU: {sku}")
                response_parts.append(f"   • Stock: {stock} units")
                if wholesale_price:
                    price_info = f"${float(wholesale_price):.2f}"
                    if retail_price:
                        price_info += f" (wholesale), ${float(retail_price):.2f} (retail)"
                    response_parts.append(f"   • Price: {price_info}")
                if category and category != 'Unknown':
                    response_parts.append(f"   • Category: {category}")
                response_parts.append("")
                
            if len(data) > 10:
                response_parts.append(f"... and {len(data) - 10} more products")
                
            response_parts.append("💡 Business Insight: Product search completed successfully.")
            return "\n".join(response_parts)
        return "🔍 No products found matching your search criteria."
    
    def _fallback_analytics_response(self, data: Any) -> str:
        """Fallback response for analytics."""
        if isinstance(data, dict):
            total_products = data.get('total_products', 0)
            total_value = data.get('total_inventory_value', 0)
            return f"📊 Analytics:\n• Total Products: {total_products:,}\n• Total Inventory Value: ${total_value:,.2f}"
        return "Analytics data retrieved."
    
    def _fallback_low_stock_response(self, data: Any) -> str:
        """Fallback response for low stock alerts."""
        if isinstance(data, dict):
            low_stock_count = data.get('low_stock_count', 0)
            out_of_stock_count = data.get('out_of_stock_count', 0)
            
            response_parts = [f"⚠️ Stock Alert Summary:"]
            response_parts.append("")
            response_parts.append(f"• Low Stock Products: {low_stock_count}")
            response_parts.append(f"• Out of Stock Products: {out_of_stock_count}")
            response_parts.append("")
            
            low_stock_products = data.get('low_stock_products', [])
            if low_stock_products:
                response_parts.append("🔍 Low Stock Products:")
                for i, product in enumerate(low_stock_products[:5], 1):
                    name = product.get('name', 'Unknown')
                    sku = product.get('sku', '')
                    current = product.get('current_stock', 0)
                    minimum = product.get('minimum_stock', 0)
                    category = product.get('category', 'Unknown')
                    
                    response_parts.append(f"{i}. **{name}**")
                    response_parts.append(f"   • SKU: {sku}")
                    response_parts.append(f"   • Stock: {current}/{minimum} units")
                    response_parts.append(f"   • Category: {category}")
                    response_parts.append("")
                    
                if len(low_stock_products) > 5:
                    response_parts.append(f"... and {len(low_stock_products) - 5} more products need restocking")
            
            response_parts.append("💡 Business Insight: Consider restocking these items to maintain optimal inventory levels.")
            return "\n".join(response_parts)
        return "⚠️ Stock alert information retrieved."
    
    def _fallback_inventory_history_response(self, data: Any) -> str:
        """Fallback response for inventory history queries."""
        if not data or not isinstance(data, list):
            return "No inventory history data found."
        
        response_parts = [f"📅 Inventory History for {len(data)} products:"]
        
        for product in data:
            name = product.get('name', 'Unknown')
            sku = product.get('sku', '')
            current_stock = product.get('current_stock', 0)
            last_updated = product.get('last_updated')
            days_ago = product.get('last_update_days_ago')
            total_movements = product.get('total_movements', 0)
            
            response_parts.append(f"\n• {name} (SKU: {sku})")
            response_parts.append(f"  Current Stock: {current_stock} units")
            
            if last_updated:
                if days_ago is not None:
                    if days_ago == 0:
                        response_parts.append(f"  Last Updated: Today")
                    elif days_ago == 1:
                        response_parts.append(f"  Last Updated: Yesterday")
                    else:
                        response_parts.append(f"  Last Updated: {days_ago} days ago")
                else:
                    response_parts.append(f"  Last Updated: {last_updated[:10]}")
            else:
                response_parts.append(f"  Last Updated: No recent updates")
            
            response_parts.append(f"  Total Movements: {total_movements}")
            
            # Show recent movements if available
            recent_movements = product.get('recent_movements', [])
            if recent_movements:
                response_parts.append(f"  Recent Activity:")
                for movement in recent_movements[:3]:  # Show top 3
                    move_type = movement.get('movement_type', 'unknown')
                    quantity = movement.get('quantity', 0)
                    created_at = movement.get('created_at', '')[:10]  # Just date part
                    response_parts.append(f"    - {move_type.title()}: {quantity} units on {created_at}")
        
        return "\n".join(response_parts)
    
    def _fallback_help_capabilities_response(self, data: Any) -> str:
        """Fallback response for help capabilities queries."""
        if not data or not isinstance(data, dict):
            return "Help information is currently unavailable."
        
        response_parts = ["🤖 Wholesale AI Agent - What I Can Do For You:"]
        
        for category, info in data.items():
            # Format category name nicely
            category_name = category.replace('_', ' ').title()
            description = info.get('description', '')
            examples = info.get('examples', [])
            
            response_parts.append(f"\n🔹 {category_name}")
            response_parts.append(f"   {description}")
            
            if examples:
                response_parts.append("   Examples:")
                for example in examples[:3]:  # Show top 3 examples
                    if isinstance(example, str):
                        response_parts.append(f"   • \"{example}\"")
                    else:
                        response_parts.append(f"   • {example}")
        
        response_parts.append("\n💡 Pro Tips:")
        response_parts.append("• I understand follow-up questions - ask 'what about its price?' after checking stock")
        response_parts.append("• Use natural language - I'll understand 'remove 5 units' or 'add stock'")  
        response_parts.append("• I can handle partial product names - 'gaming key' will find 'gaming keyboard'")
        response_parts.append("• Ask me anything about your wholesale business - I'm here to help!")
        
        return "\n".join(response_parts)