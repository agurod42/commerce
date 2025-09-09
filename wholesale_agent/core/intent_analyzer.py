"""
LLM-powered intent analysis for wholesale agent.
Uses LLM to understand user intent instead of regex patterns.
"""
import json
import logging
from typing import Dict, Any, Optional
from dataclasses import dataclass

from .llm_client import LLMClient


@dataclass
class IntentResult:
    """Result of intent analysis."""
    intent_type: str
    confidence: float
    entities: Dict[str, Any]
    needs_clarification: bool
    clarification_question: Optional[str] = None
    raw_query: str = ""


class IntentAnalyzer:
    """LLM-powered intent analyzer for wholesale business queries."""
    
    def __init__(self, llm_client: Optional[LLMClient] = None):
        self.llm_client = llm_client or LLMClient()
        self.logger = logging.getLogger(__name__)
        
        # Define available intents and their descriptions
        self.available_intents = {
            "inventory_query": "Check stock levels, inventory status, or product availability",
            "product_search": "Find specific products or browse product catalog",
            "inventory_management": "Add, remove, or adjust stock quantities",
            "inventory_history": "Check last update time, movement history, or when products were last modified",
            "analytics": "Business analytics, sales data, trends, or reporting",
            "supplier_query": "Information about suppliers or vendor management",
            "price_query": "Product pricing information or price updates",
            "low_stock_alert": "Check products with low or out-of-stock status",
            "help_capabilities": "Ask about what the agent can do, available commands, or how to use the system",
            "general": "General questions or unclear requests that need clarification"
        }
    
    def analyze_intent(self, user_query: str, context: Dict[str, Any] = None) -> IntentResult:
        """Analyze user query to determine intent and extract entities."""
        try:
            # Use LLM to analyze intent with context
            intent_analysis = self._llm_analyze_intent(user_query, context)
            
            # Parse the LLM response
            return self._parse_intent_response(intent_analysis, user_query)
            
        except Exception as e:
            self.logger.error(f"Intent analysis error: {str(e)}")
            # Fallback to general intent with clarification needed
            return IntentResult(
                intent_type="general",
                confidence=0.0,
                entities={},
                needs_clarification=True,
                clarification_question="I'm having trouble understanding your request. Could you please rephrase or provide more details about what you're looking for?",
                raw_query=user_query
            )
    
    def _llm_analyze_intent(self, user_query: str, context: Dict[str, Any] = None) -> str:
        """Use LLM to analyze user intent."""
        system_prompt = """You are an expert intent classifier for a wholesale business management system. 
Your job is to analyze user queries and determine their intent, extract relevant entities, and identify when clarification is needed.

Always respond with a valid JSON object in this exact format:
{
    "intent_type": "one of the available intents",
    "confidence": 0.0-1.0,
    "entities": {
        "product_name": "extracted product name if any",
        "quantity": "extracted quantity if any",
        "action": "extracted action (add, remove, check, etc.) if any",
        "category": "product category if mentioned",
        "supplier": "supplier name if mentioned",
        "price": "price value if mentioned"
    },
    "needs_clarification": true/false,
    "clarification_question": "question to ask user if clarification needed"
}

IMPORTANT GUIDELINES:
- BE DECISIVE: If you can extract action, product, and quantity, DO NOT ask for confirmation
- For inventory management queries with clear action + product + quantity, set needs_clarification to false
- Examples of CLEAR queries that need NO clarification:
  * "add 5 units of laptop stand" → inventory_management
  * "remove 100 brake pads as I lost them" → inventory_management  
  * "adjust phone ring holder stock to 50" → inventory_management
  * "what's the last time we updated brake pads?" → inventory_history
  * "when did we last modify gaming keyboard stock?" → inventory_history
  * "what can I ask you?" → help_capabilities
  * "what are your capabilities?" → help_capabilities
  * "help me understand what I can do" → help_capabilities
  * "how many products we have" → inventory_query (general overview)
  * "list the entire stock" → inventory_query (general overview)  
  * "show me all products" → inventory_query (general overview)
  * "what's our total inventory" → inventory_query (general overview)
- For inventory_history queries, extract the product name and set action to "check_history"
- For help_capabilities queries, no specific entities needed, just intent recognition
- For GENERAL INVENTORY queries (total products, entire stock, all products), DO NOT ask for clarification - leave entities empty for overview
- Only ask for clarification if truly missing critical information:
  * Vague queries like "help me" without context  
  * Ambiguous product names that could match multiple items
  * Missing quantities when needed for inventory operations
- Extract entities even if they're incomplete (partial product names, etc.)
- Use high confidence (0.8+) for clear inventory operations and history queries
- Use medium confidence (0.5-0.8) for somewhat clear queries  
- Use low confidence (0.0-0.5) only for truly unclear queries"""

        intents_list = "\n".join([f"- {intent}: {desc}" for intent, desc in self.available_intents.items()])
        
        # Add context information if available
        context_info = ""
        if context and context.get('has_history'):
            context_parts = []
            
            if context.get('recent_products'):
                context_parts.append(f"Recently mentioned products: {', '.join(context['recent_products'])}")
            
            if context.get('last_action_type'):
                context_parts.append(f"Last action performed: {context['last_action_type']}")
            
            if context.get('conversation_summary'):
                context_parts.append(f"Recent context: {context['conversation_summary']}")
            
            if context.get('refers_to_previous') or context.get('is_follow_up'):
                context_parts.append("Note: This query appears to reference previous conversation")
            
            if context_parts:
                context_info = f"\nConversation Context:\n" + "\n".join([f"- {part}" for part in context_parts])
        
        prompt = f"""Available intents:
{intents_list}

User Query: "{user_query}"{context_info}

Analyze this query and respond with the JSON format specified in the system prompt.

CONTEXT HANDLING:
- If the query references "it", "that", or "them" and recent products are available, use the most recent product
- If this appears to be a follow-up question, consider the previous context
- For vague references like "check that" or "what about it", infer from recent products/actions"""

        return self.llm_client.generate_response(prompt, system_prompt)
    
    def _parse_intent_response(self, llm_response: str, original_query: str) -> IntentResult:
        """Parse LLM response into IntentResult."""
        try:
            # Try to extract JSON from the response
            response = llm_response.strip()
            
            # Handle cases where LLM might include extra text around JSON
            if '```json' in response:
                start = response.find('```json') + 7
                end = response.find('```', start)
                json_str = response[start:end].strip()
            elif response.startswith('{') and response.endswith('}'):
                json_str = response
            else:
                # Try to find JSON within the response
                start = response.find('{')
                end = response.rfind('}') + 1
                if start != -1 and end > start:
                    json_str = response[start:end]
                else:
                    raise ValueError("No JSON found in response")
            
            # Clean up common JSON formatting issues
            # Remove trailing commas before closing brackets/braces
            import re
            json_str = re.sub(r',(\s*[}\]])', r'\1', json_str)
            
            parsed = json.loads(json_str)
            
            # Validate required fields
            intent_type = parsed.get('intent_type', 'general')
            confidence = float(parsed.get('confidence', 0.5))
            entities = parsed.get('entities', {})
            needs_clarification = parsed.get('needs_clarification', False)
            clarification_question = parsed.get('clarification_question')
            
            # Ensure intent type is valid
            if intent_type not in self.available_intents:
                intent_type = 'general'
                needs_clarification = True
                clarification_question = "I'm not sure how to help with that. Could you please be more specific about what you're looking for?"
            
            # Clean up entities (remove None/empty values)
            entities = {k: v for k, v in entities.items() if v is not None and v != ""}
            
            return IntentResult(
                intent_type=intent_type,
                confidence=confidence,
                entities=entities,
                needs_clarification=needs_clarification,
                clarification_question=clarification_question,
                raw_query=original_query
            )
            
        except (json.JSONDecodeError, ValueError, KeyError) as e:
            self.logger.error(f"Error parsing intent response: {str(e)}")
            self.logger.debug(f"Raw LLM response: {llm_response}")
            
            # Fallback response
            return IntentResult(
                intent_type="general",
                confidence=0.0,
                entities={},
                needs_clarification=True,
                clarification_question="I'm having trouble understanding your request. Could you please rephrase it or provide more specific details?",
                raw_query=original_query
            )