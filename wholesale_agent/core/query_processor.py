"""
Query processing and intent recognition for wholesale agent.
"""
import re
from typing import Dict, Any, List, Optional
from dataclasses import dataclass


@dataclass
class QueryIntent:
    """Represents user query intent."""
    type: str
    confidence: float
    entities: Dict[str, Any]
    keywords: List[str]


class QueryProcessor:
    """Processes user queries to understand intent and extract entities."""
    
    def __init__(self):
        self.intent_patterns = {
            'inventory_query': [
                r'(?:how much|how many|stock|inventory|quantity).+(?:do we have|in stock|available)',
                r'(?:stock level|current stock|inventory level)',
                r'(?:how much stock|stock of)',
                r'(?:out of stock|low stock)',
                r'(?:list|show).+(?:all|every).+(?:products?|items?).+(?:stock|inventory)',
                r'(?:list|show).+(?:products?|items?).+(?:and|with).+(?:stock|inventory)',
                r'(?:all products?|every product).+(?:stock|inventory)'
            ],
            'product_search': [
                r'(?:find|search|look for|show me).+(?:product|item)',
                r'(?:what products|which products)',
                r'(?:product information|product details)',
                r'(?:tell me about|information on)'
            ],
            'analytics': [
                r'(?:top|best|highest|most).+(?:selling|sold|popular)',
                r'(?:revenue|sales|profit|earnings)',
                r'(?:analytics|statistics|stats|report)',
                r'(?:total|sum|count|average)',
                r'(?:performance|trends|analysis)'
            ],
            'supplier_query': [
                r'(?:supplier|vendor|manufacturer)',
                r'(?:who supplies|supplied by)',
                r'(?:contact|phone|email).+(?:supplier|vendor)'
            ],
            'price_query': [
                r'(?:price|cost|pricing)',
                r'(?:how much|what does).+(?:cost|price)',
                r'(?:wholesale|retail).+(?:price|cost)'
            ],
            'category_query': [
                r'(?:category|categories)',
                r'(?:what category|which category)',
                r'(?:product category|item category)'
            ],
            'inventory_management': [
                r'(?:add|increase|receive|restock).+(?:stock|inventory|units)',
                r'(?:remove|decrease|sell|ship|lost|damaged).+(?:stock|inventory|units)',
                r'(?:adjust|set|update).+(?:stock|inventory|quantity)',
                r'(?:create|add).+(?:product|item)',
                r'(?:update|change).+(?:price|pricing)',
                r'(?:stock movement|inventory movement|transaction)',
                r'(?:let\'s|we).+(?:remove|lose|sell|ship)',
                r'lost \d+ units',
                r'remove .+ as',
                r'we lost \d+'
            ]
        }
        
        self.entity_patterns = {
            'product_name': [
                r'(?:stock of|inventory of|find|search for|about)\s+([a-zA-Z\s]+?)(?:\s|$|,)',
                r'"([^"]+)"',  # Quoted product names
                r"'([^']+)'",   # Single quoted product names
                r'(?:let\'s|we)\s+(?:remove|add|adjust)\s+([^a]+?)\s+(?:as|because)',  # "let's remove X as/because"
                r'(?:remove|add|adjust|sell|ship)\s+([a-zA-Z\s]+?)\s+(?:as|because|from|to)',  # "remove X as/from"
                r'(?:add|remove|adjust|set)\s+\d+\s+units?\s+of\s+(.+?)(?:\s*$)',  # "add/remove N units of X"
            ],
            'sku': [
                r'\b([A-Z]{3}-\d{4}-\d{3})\b',  # Our SKU format
                r'\bsku:?\s*([a-zA-Z0-9-]+)\b',
                r'\bpart:?\s*([a-zA-Z0-9-]+)\b'
            ],
            'category': [
                r'(?:in|from|of)\s+([a-zA-Z\s&]+?)\s+category',
                r'category:?\s*([a-zA-Z\s&]+?)(?:\s|$|,)'
            ],
            'supplier': [
                r'(?:from|by|supplier:?)\s+([a-zA-Z\s]+?)(?:\s|$|,)',
                r'(?:manufactured by|supplied by)\s+([a-zA-Z\s]+?)(?:\s|$|,)'
            ],
            'quantity': [
                r'(\d+)\s*(?:units?|pieces?|items?)',
                r'quantity:?\s*(\d+)',
                r'(?:add|remove|adjust|set)\s+(\d+)',
                r'(\d+)\s*(?:to|into|from)'
            ],
            'action': [
                r'\b(add|increase|receive|restock|remove|decrease|sell|ship|adjust|set|update|create|lost|lose)\b',
                r'let\'s\s+(remove|add|update|adjust)'
            ],
            'price': [
                r'\$(\d+(?:\.\d{2})?)',
                r'(\d+(?:\.\d{2})?)\s*(?:dollars?|usd)',
                r'price:?\s*\$?(\d+(?:\.\d{2})?)'
            ]
        }
    
    def analyze_intent(self, query: str) -> Dict[str, Any]:
        """Analyze user query to determine intent and extract entities."""
        query_lower = query.lower().strip()
        
        # Determine intent
        intent_type = self._classify_intent(query_lower)
        
        # Extract entities
        entities = self._extract_entities(query, intent_type)
        
        # Extract keywords
        keywords = self._extract_keywords(query_lower)
        
        return {
            'type': intent_type,
            'entities': entities,
            'keywords': keywords,
            'original_query': query
        }
    
    def _classify_intent(self, query: str) -> str:
        """Classify the intent of the user query."""
        intent_scores = {}
        
        for intent, patterns in self.intent_patterns.items():
            score = 0
            for pattern in patterns:
                if re.search(pattern, query, re.IGNORECASE):
                    score += 1
            
            if score > 0:
                intent_scores[intent] = score
        
        # Return the intent with the highest score, or 'general' if none found
        if intent_scores:
            return max(intent_scores.keys(), key=intent_scores.get)
        
        return 'general'
    
    def _extract_entities(self, query: str, intent_type: str) -> Dict[str, Any]:
        """Extract relevant entities from the query."""
        entities = {}
        
        for entity_type, patterns in self.entity_patterns.items():
            for pattern in patterns:
                matches = re.findall(pattern, query, re.IGNORECASE)
                if matches:
                    # Take the first match for simplicity
                    entities[entity_type] = matches[0].strip()
                    break
        
        # Intent-specific entity extraction
        if intent_type == 'product_search':
            # If no explicit product name found, use the whole query as search term
            if 'product_name' not in entities:
                # Remove common query words to get search term
                search_term = re.sub(
                    r'\b(?:find|search|look for|show me|product|item|information|about|tell me)\b',
                    '', query, flags=re.IGNORECASE
                ).strip()
                if search_term:
                    entities['search_term'] = search_term
        
        return entities
    
    def _extract_keywords(self, query: str) -> List[str]:
        """Extract important keywords from the query."""
        # Remove common stop words and extract meaningful terms
        stop_words = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
            'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'being',
            'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could',
            'should', 'may', 'might', 'must', 'can', 'this', 'that', 'these',
            'those', 'i', 'you', 'he', 'she', 'it', 'we', 'they', 'me', 'him',
            'her', 'us', 'them', 'my', 'your', 'his', 'her', 'its', 'our', 'their'
        }
        
        # Extract words, filter out stop words and short words
        words = re.findall(r'\b\w+\b', query.lower())
        keywords = [
            word for word in words 
            if len(word) > 2 and word not in stop_words
        ]
        
        return list(set(keywords))  # Remove duplicates
    
    def get_query_suggestions(self, partial_query: str) -> List[str]:
        """Provide query suggestions based on partial input."""
        suggestions = []
        
        if len(partial_query) < 3:
            return []
        
        # Common query templates
        templates = [
            "How much stock of {query} do we have?",
            "Find products matching {query}",
            "Show me {query} inventory levels",
            "What is the price of {query}?",
            "Which supplier provides {query}?",
            "What category is {query} in?",
            "Show low stock {query} products",
            "Analytics for {query} sales"
        ]
        
        for template in templates:
            if any(keyword in template.lower() for keyword in partial_query.lower().split()):
                suggestions.append(template.format(query=partial_query))
        
        return suggestions[:5]  # Return top 5 suggestions
    
    def validate_query(self, query: str) -> Dict[str, Any]:
        """Validate if a query can be processed effectively."""
        if not query or not query.strip():
            return {
                'valid': False,
                'reason': 'Empty query'
            }
        
        if len(query.strip()) < 3:
            return {
                'valid': False,
                'reason': 'Query too short'
            }
        
        # Check for potentially problematic queries
        problematic_patterns = [
            r'^\s*[0-9\s\+\-\*\/\(\)]+\s*$',  # Only math expressions
            r'^[^a-zA-Z]*$'  # No alphabetic characters
        ]
        
        for pattern in problematic_patterns:
            if re.match(pattern, query):
                return {
                    'valid': False,
                    'reason': 'Query format not supported'
                }
        
        return {
            'valid': True,
            'reason': 'Query is valid'
        }