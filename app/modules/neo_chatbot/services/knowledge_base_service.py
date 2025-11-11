"""
Knowledge Base Service - Document Q&A using RAG (Retrieval-Augmented Generation)
Answers questions about NEO documentation, code, and proposals
"""

import logging
import uuid
from typing import List, Dict, Any, Optional
from pathlib import Path

from .llm_service import LLMService
from .vector_store_service import VectorStoreService
from ..models.schemas import ChatRequest, ChatResponse, SourceDocument, ChatbotType, MessageRole

logger = logging.getLogger(__name__)


class KnowledgeBaseService:
    """
    Service for Knowledge Base Chatbot
    Uses RAG to answer questions about NEO documentation
    """
    
    def __init__(self):
        """Initialize knowledge base service"""
        self.llm_service = LLMService()
        self.vector_store = VectorStoreService()
        
        self.system_prompt = """You are NEO Assistant, an intelligent chatbot that helps users understand the NEO Warehouse Management System.

Your knowledge base includes:
- NEO system documentation
- Code examples and technical implementations
- Solution proposals and use cases

When answering questions:
1. Always cite your sources (mention which document the information came from)
2. Be accurate and specific based on the provided context
3. If the context doesn't contain enough information, say so clearly
4. Provide code examples when relevant
5. Suggest related topics the user might want to explore

Remember: You are helpful, professional, and focused on NEO system knowledge."""

        logger.info("✅ Knowledge Base Service initialized")
    
    def process_query(self, chat_request: ChatRequest) -> ChatResponse:
        """
        Process user query using RAG (Retrieval-Augmented Generation)
        
        Steps:
        1. Generate embedding for user query
        2. Search vector store for relevant documents
        3. Create context from retrieved documents
        4. Generate response using LLM with context
        
        Args:
            chat_request: User's chat request
            
        Returns:
            Chat response with answer and sources
        """
        try:
            logger.info(f"🔍 Processing knowledge base query: {chat_request.message[:50]}...")
            
            # Check if vector store has documents
            if len(self.vector_store.documents) == 0:
                return self._handle_empty_knowledge_base(chat_request)
            
            # Step 1: Generate query embedding
            query_embedding = self.llm_service.generate_embedding(chat_request.message)
            
            # Step 2: Search for relevant documents
            search_results = self.vector_store.search(
                query_embedding=query_embedding,
                top_k=5,
                filter_metadata=chat_request.context,
                min_similarity=0.3  # Only include reasonably relevant docs
            )
            
            # Step 3: Build context from retrieved documents
            context = self._build_context(search_results)
            source_documents = self._extract_source_documents(search_results)
            
            # Step 4: Generate response using LLM
            messages = self._build_messages(chat_request, context)
            response_text = self.llm_service.generate_response(
                messages=messages,
                system_prompt=self.system_prompt,
                max_tokens=1000,
                temperature=0.7
            )
            
            # Calculate confidence based on source relevance
            confidence = self._calculate_confidence(search_results)
            
            return ChatResponse(
                response=response_text,
                chatbot_type=ChatbotType.KNOWLEDGE_BASE,
                session_id=chat_request.session_id or str(uuid.uuid4()),
                sources=source_documents,
                confidence_score=confidence,
                suggested_actions=self._generate_suggested_actions(chat_request.message)
            )
            
        except Exception as e:
            logger.error(f"❌ Error processing knowledge base query: {e}", exc_info=True)
            return ChatResponse(
                response="I apologize, but I encountered an error while processing your question. Please try rephrasing or contact support.",
                chatbot_type=ChatbotType.KNOWLEDGE_BASE,
                session_id=chat_request.session_id or str(uuid.uuid4()),
                sources=[],
                confidence_score=0.0
            )
    
    def _handle_empty_knowledge_base(self, chat_request: ChatRequest) -> ChatResponse:
        """Handle case when no documents are in knowledge base"""
        return ChatResponse(
            response="""I don't have any documents in my knowledge base yet. 

To enable document Q&A:
1. Place your documentation files (PDF, DOCX, TXT) in: app/modules/neo_chatbot/data/documents/
2. Run the document ingestion process to index them
3. Then I'll be able to answer questions about your documentation!

Currently I can still help with:
- Database queries (SQL Assistant)
- System diagnostics and troubleshooting
- General NEO system questions (with limited context)

What would you like help with?""",
            chatbot_type=ChatbotType.KNOWLEDGE_BASE,
            session_id=chat_request.session_id or str(uuid.uuid4()),
            sources=[],
            confidence_score=0.0,
            suggested_actions=["Add documents to knowledge base", "Try SQL Assistant", "Ask about diagnostics"]
        )
    
    def _build_context(self, search_results: List[Dict[str, Any]]) -> str:
        """Build context string from search results"""
        if not search_results:
            return "No relevant documentation found."
        
        context_parts = []
        for i, result in enumerate(search_results, 1):
            doc = result["document"]
            context_parts.append(f"""
Document {i}: {doc['metadata'].get('filename', 'Unknown')}
Category: {doc['metadata'].get('category', 'Unknown')}
Relevance: {result['similarity']:.1%}

Content:
{doc['content'][:500]}{'...' if len(doc['content']) > 500 else ''}
---
""")
        
        return "\n".join(context_parts)
    
    def _extract_source_documents(self, search_results: List[Dict[str, Any]]) -> List[SourceDocument]:
        """Extract source documents from search results"""
        sources = []
        for result in search_results:
            doc = result["document"]
            sources.append(SourceDocument(
                document_name=doc['metadata'].get('filename', 'Unknown'),
                content_snippet=doc['content'][:200] + "..." if len(doc['content']) > 200 else doc['content'],
                relevance_score=result['similarity'],
                page_number=doc['metadata'].get('page_number'),
                document_type=doc['metadata'].get('category', 'unknown')
            ))
        return sources
    
    def _build_messages(self, chat_request: ChatRequest, context: str) -> List[Dict[str, str]]:
        """Build message list for LLM"""
        messages = []
        
        # Add conversation history if available (last 5 messages)
        if chat_request.conversation_history:
            for msg in chat_request.conversation_history[-5:]:
                messages.append({
                    "role": msg.role.value,
                    "content": msg.content
                })
        
        # Add current query with context
        user_message = f"""Based on the following NEO system documentation:

{context}

User Question: {chat_request.message}

Please provide a detailed answer based on the documentation above. Cite specific documents when possible. If the documentation doesn't fully answer the question, say so clearly."""

        messages.append({
            "role": "user",
            "content": user_message
        })
        
        return messages
    
    def _calculate_confidence(self, search_results: List[Dict[str, Any]]) -> float:
        """Calculate confidence score based on search results"""
        if not search_results:
            return 0.0
        
        # Average of top 3 similarities
        top_similarities = [r['similarity'] for r in search_results[:3]]
        return sum(top_similarities) / len(top_similarities) if top_similarities else 0.0
    
    def _generate_suggested_actions(self, query: str) -> List[str]:
        """Generate suggested follow-up actions"""
        suggestions = []
        
        query_lower = query.lower()
        
        if "install" in query_lower or "setup" in query_lower:
            suggestions.extend([
                "View installation documentation",
                "Check system requirements",
                "See configuration examples"
            ])
        elif "error" in query_lower or "issue" in query_lower:
            suggestions.extend([
                "Check diagnostic support",
                "View common issues",
                "Contact support"
            ])
        elif "code" in query_lower or "api" in query_lower:
            suggestions.extend([
                "See API documentation",
                "View code examples",
                "Explore technical guides"
            ])
        else:
            suggestions.extend([
                "Explore related topics",
                "View example use cases",
                "Read getting started guide"
            ])
        
        return suggestions[:3]
    
    def add_document(
        self,
        filename: str,
        content: str,
        category: str,
        additional_metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Add document to knowledge base
        
        Args:
            filename: Document filename
            content: Document text content
            category: Document category (documentation, code, proposal, support)
            additional_metadata: Additional metadata
            
        Returns:
            Success status
        """
        try:
            # Generate unique document ID
            doc_id = str(uuid.uuid4())
            
            # Generate embedding
            embedding = self.llm_service.generate_embedding(content)
            
            # Prepare metadata
            metadata = {
                "filename": filename,
                "category": category,
                **(additional_metadata or {})
            }
            
            # Add to vector store
            self.vector_store.add_document(
                document_id=doc_id,
                content=content,
                embedding=embedding,
                metadata=metadata
            )
            
            logger.info(f"✅ Added document to knowledge base: {filename}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error adding document to knowledge base: {e}")
            return False
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get knowledge base statistics"""
        stats = self.vector_store.get_statistics()
        stats["llm_provider"] = self.llm_service.get_provider_info()
        return stats
