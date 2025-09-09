"""
Conversation context management for wholesale agent.
Maintains conversation history to enable follow-up queries and contextual understanding.
"""
import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime

from .intent_analyzer import IntentResult
from .action_executor import ActionResult


@dataclass
class ConversationTurn:
    """Represents a single conversation turn."""
    timestamp: datetime
    user_query: str
    intent_result: IntentResult
    action_result: ActionResult
    response: str
    turn_id: int


class ConversationContext:
    """Manages conversation context and history for contextual understanding."""
    
    def __init__(self, max_turns: int = 10):
        """Initialize conversation context.
        
        Args:
            max_turns: Maximum number of conversation turns to remember
        """
        self.max_turns = max_turns
        self.history: List[ConversationTurn] = []
        self.turn_counter = 0
        self.logger = logging.getLogger(__name__)
        
        # Context tracking
        self.last_mentioned_products = []  # Products mentioned in recent turns
        self.last_action_type = None       # Last action performed
        self.last_entities = {}            # Last extracted entities
    
    def add_turn(self, user_query: str, intent_result: IntentResult, 
                 action_result: ActionResult, response: str) -> None:
        """Add a new conversation turn to the history."""
        self.turn_counter += 1
        
        turn = ConversationTurn(
            timestamp=datetime.now(),
            user_query=user_query,
            intent_result=intent_result,
            action_result=action_result,
            response=response,
            turn_id=self.turn_counter
        )
        
        self.history.append(turn)
        
        # Maintain maximum history size
        if len(self.history) > self.max_turns:
            self.history.pop(0)
        
        # Update context tracking
        self._update_context_tracking(intent_result, action_result)
        
        self.logger.debug(f"Added conversation turn {self.turn_counter}")
    
    def _update_context_tracking(self, intent_result: IntentResult, action_result: ActionResult) -> None:
        """Update context tracking variables."""
        self.last_action_type = action_result.action_type
        self.last_entities = intent_result.entities
        
        # Track mentioned products - but ONLY if they were actually found
        # Don't pollute context with non-existent products
        if (action_result.success and 
            'product_name' in intent_result.entities and
            action_result.data):  # Only track if we have actual data
            
            product_name = intent_result.entities['product_name']
            if product_name and product_name not in self.last_mentioned_products:
                # Additional check: make sure we actually found products
                if isinstance(action_result.data, list) and action_result.data:
                    # We found actual products, so this is a valid product to remember
                    self.last_mentioned_products.append(product_name)
                    # Keep only last 5 mentioned products
                    if len(self.last_mentioned_products) > 5:
                        self.last_mentioned_products.pop(0)
        
        # Extract products from action result data
        if action_result.data and isinstance(action_result.data, (list, dict)):
            self._extract_products_from_action_data(action_result.data)
    
    def _extract_products_from_action_data(self, data: Any) -> None:
        """Extract product names from action result data."""
        try:
            if isinstance(data, list):
                for item in data[:3]:  # Only check first 3 items
                    if isinstance(item, dict) and 'name' in item:
                        product_name = item['name']
                        if product_name not in self.last_mentioned_products:
                            self.last_mentioned_products.append(product_name)
            elif isinstance(data, dict):
                # Handle various data structures
                if 'name' in data:
                    product_name = data['name']
                    if product_name not in self.last_mentioned_products:
                        self.last_mentioned_products.append(product_name)
                elif 'sample_products' in data:
                    for item in data['sample_products'][:3]:
                        if 'name' in item:
                            product_name = item['name']
                            if product_name not in self.last_mentioned_products:
                                self.last_mentioned_products.append(product_name)
        except Exception as e:
            self.logger.debug(f"Error extracting products from action data: {e}")
    
    def get_context_for_query(self, user_query: str) -> Dict[str, Any]:
        """Get relevant context information for the current query."""
        context = {
            'has_history': len(self.history) > 0,
            'recent_products': self.last_mentioned_products.copy(),
            'last_action_type': self.last_action_type,
            'last_entities': self.last_entities.copy(),
            'conversation_summary': self._get_conversation_summary()
        }
        
        # Check for contextual references in the query
        contextual_indicators = self._detect_contextual_references(user_query)
        context.update(contextual_indicators)
        
        return context
    
    def _detect_contextual_references(self, user_query: str) -> Dict[str, Any]:
        """Detect if the query contains contextual references."""
        query_lower = user_query.lower().strip()
        
        indicators = {
            'refers_to_previous': False,
            'refers_to_that_product': False,
            'refers_to_same_action': False,
            'is_follow_up': False
        }
        
        # Detect pronouns and references that indicate context dependency
        contextual_words = [
            'it', 'that', 'those', 'them', 'this', 'these',
            'same', 'also', 'too', 'again', 'more',
            'what about', 'how about', 'and', 'also check',
            'now', 'then', 'after that', 'afterwards'
        ]
        
        follow_up_patterns = [
            'what about', 'how about', 'and the', 'also',
            'now show', 'then', 'after', 'next',
            'what is', 'how much', 'check the'
        ]
        
        for word in contextual_words:
            if word in query_lower:
                indicators['refers_to_previous'] = True
                break
        
        for pattern in follow_up_patterns:
            if pattern in query_lower:
                indicators['is_follow_up'] = True
                break
        
        # Check for product references
        if any(word in query_lower for word in ['that product', 'this product', 'it', 'that item']):
            indicators['refers_to_that_product'] = True
        
        # Check for action references
        if any(word in query_lower for word in ['again', 'same', 'also', 'more']):
            indicators['refers_to_same_action'] = True
        
        return indicators
    
    def _get_conversation_summary(self) -> str:
        """Generate a brief summary of recent conversation."""
        if not self.history:
            return "No previous conversation"
        
        recent_turns = self.history[-3:]  # Last 3 turns
        summary_parts = []
        
        for turn in recent_turns:
            # Create a brief summary of each turn
            intent_type = turn.intent_result.intent_type
            entities = turn.intent_result.entities
            
            if intent_type == 'inventory_management':
                action = entities.get('action', 'action')
                product = entities.get('product_name', 'product')
                quantity = entities.get('quantity', 'some')
                summary_parts.append(f"User performed {action} operation on {product} ({quantity} units)")
            elif intent_type == 'inventory_query':
                product = entities.get('product_name', 'products')
                summary_parts.append(f"User queried inventory for {product}")
            elif intent_type == 'product_search':
                search_term = entities.get('product_name', 'products')
                summary_parts.append(f"User searched for {search_term}")
            else:
                summary_parts.append(f"User made {intent_type} query")
        
        return "; ".join(summary_parts)
    
    def enhance_entities_with_context(self, entities: Dict[str, Any]) -> Dict[str, Any]:
        """Enhance extracted entities with context information."""
        enhanced = entities.copy()
        
        # If no product name was extracted, try to infer from context
        if not enhanced.get('product_name') and self.last_mentioned_products:
            # Use the most recently mentioned product
            enhanced['product_name'] = self.last_mentioned_products[-1]
            enhanced['_from_context'] = True
        
        # If no action was specified, try to infer from recent actions
        if not enhanced.get('action') and self.last_entities.get('action'):
            # Check if this might be a continuation of the same action
            enhanced['_suggested_action'] = self.last_entities['action']
        
        return enhanced
    
    def get_recent_history_text(self, turns: int = 3) -> str:
        """Get recent conversation history as text for LLM context."""
        if not self.history:
            return ""
        
        recent_turns = self.history[-turns:]
        history_text = []
        
        for turn in recent_turns:
            history_text.append(f"User: {turn.user_query}")
            # Truncate long responses
            response_preview = turn.response[:150] + "..." if len(turn.response) > 150 else turn.response
            history_text.append(f"Assistant: {response_preview}")
        
        return "\n".join(history_text)
    
    def clear_context(self) -> None:
        """Clear conversation context (useful for new conversations)."""
        self.history.clear()
        self.last_mentioned_products.clear()
        self.last_action_type = None
        self.last_entities = {}
        self.turn_counter = 0
        self.logger.debug("Conversation context cleared")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get conversation statistics."""
        return {
            'total_turns': len(self.history),
            'turn_counter': self.turn_counter,
            'recent_products': len(self.last_mentioned_products),
            'has_context': len(self.history) > 0,
            'last_action': self.last_action_type
        }