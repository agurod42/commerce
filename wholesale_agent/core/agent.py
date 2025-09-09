"""
AI Agent core functionality for wholesale business operations.
New architecture: LLM for intent → App executes action → LLM formats response
"""
import logging
from typing import Optional, Dict, Any

from .llm_client import LLMClient
from .intent_analyzer import IntentAnalyzer
from .action_executor import ActionExecutor, ActionResult
from .response_formatter import ResponseFormatter
from .conversation_context import ConversationContext

try:
    from .rag_pipeline import RAGPipeline
    RAG_AVAILABLE = True
except ImportError:
    RAG_AVAILABLE = False
    RAGPipeline = None


class WholesaleAgent:
    """AI Agent for wholesale business operations.
    
    New Architecture:
    1. LLM analyzes user intent and extracts entities
    2. ActionExecutor performs business operations based on intent  
    3. LLM formats structured results into beautiful responses
    4. If intent is unclear, LLM asks follow-up questions
    """
    
    def __init__(self, llm_client: Optional[LLMClient] = None, enable_rag: bool = False):
        self.llm_client = llm_client or LLMClient()
        self.intent_analyzer = IntentAnalyzer(self.llm_client)
        self.action_executor = ActionExecutor()
        self.response_formatter = ResponseFormatter(self.llm_client)
        self.conversation_context = ConversationContext()
        self.logger = logging.getLogger(__name__)
        
        # Initialize RAG pipeline if requested and available
        self.rag_pipeline = None
        if enable_rag and RAG_AVAILABLE:
            try:
                self.rag_pipeline = RAGPipeline()
                self.rag_pipeline.load_index()  # Try to load existing index
                self.logger.info("RAG pipeline initialized successfully")
            except Exception as e:
                self.logger.warning(f"RAG pipeline initialization failed: {e}")
        elif enable_rag and not RAG_AVAILABLE:
            self.logger.warning("RAG requested but dependencies not installed. Install with: pip install sentence-transformers faiss-cpu")
    
    def process_query(self, user_query: str) -> str:
        """Process user query using new architecture with conversation context: LLM Intent → App Action → LLM Response."""
        try:
            self.logger.info(f"Processing query: {user_query}")
            
            # Step 0: Get conversation context for this query
            context = self.conversation_context.get_context_for_query(user_query)
            self.logger.debug(f"Conversation context: {context.get('has_history', False)}, recent_products: {len(context.get('recent_products', []))}")
            
            # Step 1: LLM analyzes user intent and extracts entities with context
            self.logger.debug("Step 1: Analyzing intent with LLM and conversation context")
            intent_result = self.intent_analyzer.analyze_intent(user_query, context)
            self.logger.debug(f"Intent analysis result: {intent_result.intent_type}, confidence: {intent_result.confidence}")
            
            # Step 2: App executes business action based on intent
            self.logger.debug("Step 2: Executing business action")
            action_result = self.action_executor.execute_action(intent_result)
            
            # Safety check for action_result
            if action_result is None:
                self.logger.error("ActionExecutor returned None - this should not happen")
                action_result = ActionResult(
                    success=False,
                    action_type="error",
                    error="Internal error: ActionExecutor returned None"
                )
            
            self.logger.debug(f"Action result: {action_result.action_type}, success: {action_result.success}")
            
            # Step 3: LLM formats structured results into beautiful response with context
            self.logger.debug("Step 3: Formatting response with LLM") 
            formatted_response = self.response_formatter.format_response(user_query, action_result, context)
            
            # Step 4: Add this turn to conversation context
            self.conversation_context.add_turn(user_query, intent_result, action_result, formatted_response)
            
            self.logger.info("Query processed successfully with context-aware architecture")
            return formatted_response
            
        except Exception as e:
            self.logger.error(f"Error processing query: {str(e)}")
            return f"I apologize, but I encountered an error processing your request: {str(e)}"
    
    def clear_conversation(self) -> None:
        """Clear conversation context (useful for starting fresh)."""
        self.conversation_context.clear_context()
        self.logger.info("Conversation context cleared")
    
    def get_conversation_stats(self) -> Dict[str, Any]:
        """Get conversation statistics."""
        return self.conversation_context.get_stats()
