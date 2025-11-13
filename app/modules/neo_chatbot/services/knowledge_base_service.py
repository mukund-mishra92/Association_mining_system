"""
Knowledge Base Service - Document Q&A using RAG (Retrieval-Augmented Generation)
Answers questions about NEO documentation, code, and proposals
"""

import logging
import re
import uuid
from typing import List, Dict, Any, Optional
from pathlib import Path

from .llm_service import LLMService
from .vector_store_service import VectorStoreService
from .rlhf_service import RLHFService
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
        self.rlhf_service = RLHFService()
        
        self.system_prompt = """You are NEO Assistant, an expert on the NEO Warehouse Management System.

Your knowledge base includes:
- NEO system documentation and user manuals
- Technical specifications and proposals
- Code examples and implementations
- Standard Operating Procedures (SOPs)
- Safety guidelines and best practices

Response Guidelines:
1. **Structure your answers clearly** with headings and sections
2. **Use formatting** - bullet points, numbered lists, bold/italic for emphasis
3. **Be specific and accurate** - cite document names when referencing information
4. **Provide context** - explain technical terms when needed
5. **Be concise yet comprehensive** - break complex topics into digestible parts
6. **Include examples** when they help clarify concepts
7. **If information is incomplete**, clearly state what's missing
8. **Use professional tone** - helpful, clear, and authoritative

Formatting Standards:
- Use **bold** for key terms and section headers
- Use bullet points (•) or numbered lists for multi-item information
- Use line breaks between sections for readability
- Include relevant document references in [brackets]
- Use code blocks for technical examples when applicable

Always prioritize clarity and user understanding."""

        logger.info("✅ Knowledge Base Service initialized")
    
    def process_query(self, chat_request: ChatRequest) -> ChatResponse:
        """
        Process user query using RAG (Retrieval-Augmented Generation)
        
        Steps:
        1. Classify query type (factual, generative, conversational, unanswerable)
        2. Generate embedding for user query
        3. Search vector store for relevant documents
        4. Build adaptive context based on query type
        5. Generate response with appropriate strategy
        
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
            
            # Step 0: Classify query type for adaptive response strategy
            query_type = self._classify_query(chat_request.message)
            logger.info(f"📊 Query classified as: {query_type}")
            
            # Step 1: Generate query embedding
            query_embedding = self.llm_service.generate_embedding(chat_request.message)
            
            # Step 2: Search for relevant documents
            search_results = self.vector_store.search(
                query_embedding=query_embedding,
                top_k=8,  # Retrieve more documents for better context
                filter_metadata=chat_request.context,
                min_similarity=0.25  # Lower threshold to catch more relevant content
            )
            
            # Filter and re-rank results
            filtered_results = self._filter_and_rerank(search_results, chat_request.message)
            
            # Step 3: Build context from retrieved documents
            context = self._build_context(filtered_results)
            source_documents = self._extract_source_documents(filtered_results)
            
            # Step 4: Generate response using LLM with adaptive strategy
            messages = self._build_adaptive_messages(chat_request, context, query_type)
            
            # Adjust LLM parameters based on query type
            max_tokens, temperature = self._get_llm_parameters(query_type)
            
            response_text = self.llm_service.generate_response(
                messages=messages,
                system_prompt=self._get_adaptive_system_prompt(query_type),
                max_tokens=max_tokens,
                temperature=temperature
            )
            
            # Format response based on query type
            response_text = self._format_adaptive_response(response_text, query_type)
            
            # Calculate confidence based on source relevance
            confidence = self._calculate_confidence(filtered_results)
            
            # Record for RLHF learning
            try:
                self.rlhf_service.record_feedback(
                    chatbot_type="knowledge_base",
                    query=chat_request.message,
                    response=response_text,
                    feedback_type="neutral",  # Auto-logged on generation
                    rating=None,
                    comment=f"Auto-generated ({query_type} query)",
                    metadata={
                        "query_type": query_type,
                        "confidence": confidence,
                        "source_count": len(source_documents),
                        "document_names": [doc.document_name for doc in source_documents[:3]]
                    }
                )
            except Exception as e:
                logger.warning(f"Failed to record RLHF feedback: {e}")
            
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
    
    def _classify_query(self, query: str) -> str:
        """
        Classify query type to determine response strategy
        
        Types:
        - SIMPLE_FACT: Simple factual questions (What is X? How many? When?)
        - DEFINITION: Asking for definition/explanation (What does X mean?)
        - PROCEDURAL: How-to questions requiring steps (How to X?)
        - COMPARISON: Comparing multiple things (X vs Y, difference between)
        - EXPLORATORY: Open-ended exploration (Tell me about X)
        - GENERATIVE: Creating new content (Generate/Create/Write)
        - UNANSWERABLE: Questions outside knowledge base scope
        """
        query_lower = query.lower().strip()
        
        # Simple fact queries (short answers)
        simple_fact_patterns = [
            r'^what is (the |a )?(\w+)\??$',  # "What is X?"
            r'^how many\b',  # "How many..."
            r'^when (was|is|did)\b',  # "When..."
            r'^where (is|are)\b',  # "Where..."
            r'^who (is|are)\b',  # "Who..."
            r'^which\b',  # "Which..."
            r'^(yes|no),?\s',  # Yes/No questions
            r'\?(yes|no)\??$',  # Ending with yes/no
        ]
        
        for pattern in simple_fact_patterns:
            if re.search(pattern, query_lower):
                return "SIMPLE_FACT"
        
        # Definition queries
        if any(phrase in query_lower for phrase in [
            "what does", "define", "definition of", "meaning of", "what is meant by"
        ]):
            return "DEFINITION"
        
        # Procedural queries (step-by-step)
        if any(phrase in query_lower for phrase in [
            "how to", "how do i", "how can i", "steps to", "procedure for", 
            "process of", "way to", "method to"
        ]):
            return "PROCEDURAL"
        
        # Comparison queries
        if any(phrase in query_lower for phrase in [
            " vs ", " versus ", "difference between", "compare", "comparison",
            "better than", "advantages of", "disadvantages of"
        ]):
            return "COMPARISON"
        
        # Generative queries (cannot be answered from docs)
        if any(phrase in query_lower for phrase in [
            "generate", "create a", "write a", "make a", "design a",
            "develop a", "build me", "give me a new"
        ]):
            return "GENERATIVE"
        
        # Exploratory queries (detailed explanations)
        if any(phrase in query_lower for phrase in [
            "tell me about", "explain", "describe", "overview of",
            "information about", "details about", "all about"
        ]):
            return "EXPLORATORY"
        
        # Default to exploratory for longer queries
        return "EXPLORATORY" if len(query.split()) > 5 else "SIMPLE_FACT"
    
    def _get_adaptive_system_prompt(self, query_type: str) -> str:
        """Get system prompt based on query type"""
        
        base_prompt = "You are NEO Assistant, an expert on the NEO Warehouse Management System."
        
        if query_type == "SIMPLE_FACT":
            return base_prompt + """

TASK: Provide a direct, concise answer in 1-3 sentences.

RULES:
- Answer directly without unnecessary context
- No lengthy explanations unless asked
- No forced formatting with sections
- If it's a yes/no question, start with yes or no
- Cite the document source in [brackets] at the end

Example:
Q: "What is NEO?"
A: "NEO is an Automated Storage and Retrieval System (ASRS) that uses autonomous robots to store and retrieve bins efficiently. [NEO System Documentation]"
"""
        
        elif query_type == "DEFINITION":
            return base_prompt + """

TASK: Provide a clear definition followed by brief context.

FORMAT:
**Definition:** [Clear, concise definition in 1-2 sentences]

**Context:** [Brief explanation of why it matters or how it's used - 2-3 sentences]

[Source: Document name]
"""
        
        elif query_type == "PROCEDURAL":
            return base_prompt + """

TASK: Provide step-by-step instructions.

FORMAT:
**How to [Task]:**

1. [First step]
2. [Second step]
3. [Continue...]

**Important Notes:**
• [Any warnings or prerequisites]
• [Special considerations]

[Source: Document name]
"""
        
        elif query_type == "COMPARISON":
            return base_prompt + """

TASK: Provide a structured comparison.

FORMAT:
**Key Differences:**

| Aspect | Option A | Option B |
|--------|----------|----------|
| [Feature] | [Detail] | [Detail] |

**Summary:** [Which is better for what use case]

[Source: Document name]
"""
        
        elif query_type == "GENERATIVE":
            return base_prompt + """

TASK: Explain that you cannot generate new content, but can help with existing documentation.

RESPONSE STRATEGY:
1. Politely explain you can only provide information from existing documentation
2. Offer to share relevant examples/templates from the docs
3. Suggest what specific information you CAN provide

Be helpful, not rigid. Offer alternatives.
"""
        
        else:  # EXPLORATORY
            return base_prompt + """

TASK: Provide a comprehensive, well-structured explanation.

FORMAT:
**Overview**
[2-3 sentence summary]

**Key Points**
• [Main point 1]
• [Main point 2]
• [Main point 3]

**Additional Details**
[Relevant specifics, examples, or context]

**Source References**
[Document names]
"""
    
    def _get_llm_parameters(self, query_type: str) -> tuple:
        """Get max_tokens and temperature based on query type"""
        
        params = {
            "SIMPLE_FACT": (300, 0.2),      # Short, focused
            "DEFINITION": (500, 0.3),       # Medium, precise
            "PROCEDURAL": (1000, 0.3),      # Detailed, structured
            "COMPARISON": (800, 0.3),       # Analytical
            "GENERATIVE": (400, 0.5),       # Helpful redirection
            "EXPLORATORY": (1500, 0.4),     # Comprehensive
        }
        
        return params.get(query_type, (1000, 0.4))
    
    def _build_adaptive_messages(self, chat_request: ChatRequest, context: str, query_type: str) -> List[Dict[str, str]]:
        """Build messages with adaptive prompting based on query type"""
        messages = []
        
        # Add minimal conversation history for context
        if chat_request.conversation_history and query_type in ["PROCEDURAL", "EXPLORATORY"]:
            for msg in chat_request.conversation_history[-2:]:
                messages.append({
                    "role": msg.role.value,
                    "content": msg.content
                })
        
        # Build query-specific prompt
        if query_type == "SIMPLE_FACT":
            user_message = f"""Documentation:
{context}

Question: {chat_request.message}

Provide a direct, concise answer in 1-3 sentences. No extra formatting."""
        
        elif query_type == "GENERATIVE":
            user_message = f"""Documentation Available:
{context}

User Request: {chat_request.message}

The user is asking you to GENERATE/CREATE new content. You cannot do this.

Instead:
1. Politely explain you can only reference existing documentation
2. Offer relevant examples or templates from the documentation
3. Ask what specific information from existing docs would be helpful

Be conversational and helpful, not robotic."""
        
        else:
            user_message = f"""Documentation:
{context}

Question: {chat_request.message}

Provide a clear, well-structured answer using the documentation. Follow the response format for {query_type} queries."""
        
        messages.append({
            "role": "user",
            "content": user_message
        })
        
        return messages
    
    def _format_adaptive_response(self, response_text: str, query_type: str) -> str:
        """Format response based on query type"""
        
        # Minimal formatting for simple facts
        if query_type == "SIMPLE_FACT":
            # Just clean up extra newlines
            response_text = re.sub(r'\n{2,}', '\n', response_text)
            return response_text.strip()
        
        # Standard formatting for others
        response_text = re.sub(r'\n{3,}', '\n\n', response_text)
        response_text = response_text.strip()
        
        return response_text
    
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
        """Build context string from search results with improved formatting"""
        if not search_results:
            return "No relevant documentation found."
        
        context_parts = []
        for i, result in enumerate(search_results, 1):
            doc = result["document"]
            filename = doc['metadata'].get('filename', 'Unknown')
            category = doc['metadata'].get('category', 'Unknown')
            similarity = result['similarity']
            content = doc['content']
            
            # Include more content for high-relevance documents
            max_length = 800 if similarity > 0.5 else 500
            content_preview = content[:max_length]
            if len(content) > max_length:
                content_preview += "..."
            
            context_parts.append(f"""
[Document {i}] {filename}
Category: {category} | Relevance: {similarity:.1%}

{content_preview}
{'─' * 80}
""")
        
        return "\n".join(context_parts)
    
    def _filter_and_rerank(self, search_results: List[Dict[str, Any]], query: str) -> List[Dict[str, Any]]:
        """Filter and re-rank search results based on query relevance"""
        if not search_results:
            return []
        
        # Filter out very low similarity results
        filtered = [r for r in search_results if r['similarity'] > 0.2]
        
        # Re-rank by combining similarity with keyword matching
        query_keywords = set(query.lower().split())
        
        for result in filtered:
            content_lower = result['document']['content'].lower()
            keyword_matches = sum(1 for kw in query_keywords if kw in content_lower)
            
            # Boost score if content has many query keywords
            keyword_boost = min(keyword_matches * 0.05, 0.15)
            result['boosted_similarity'] = min(result['similarity'] + keyword_boost, 1.0)
        
        # Sort by boosted similarity
        filtered.sort(key=lambda x: x.get('boosted_similarity', x['similarity']), reverse=True)
        
        # Return top 5 most relevant
        return filtered[:5]
    
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
    
    def _calculate_confidence(self, search_results: List[Dict[str, Any]]) -> float:
        """Calculate confidence score based on search results quality"""
        if not search_results:
            return 0.0
        
        # Weighted confidence calculation
        # - Top result has most weight
        # - Consider number of high-quality results
        # - Penalize if only low-similarity results
        
        similarities = [r.get('boosted_similarity', r['similarity']) for r in search_results]
        
        if not similarities:
            return 0.0
        
        # Weight top results more heavily
        weights = [0.4, 0.3, 0.2, 0.1][:len(similarities)]
        weights.extend([0.05] * (len(similarities) - len(weights)))
        
        weighted_score = sum(s * w for s, w in zip(similarities, weights))
        
        # Boost confidence if we have multiple high-quality results
        high_quality_count = sum(1 for s in similarities if s > 0.5)
        quality_boost = min(high_quality_count * 0.05, 0.15)
        
        final_confidence = min(weighted_score + quality_boost, 1.0)
        
        return round(final_confidence, 2)
    
    def _generate_suggested_actions(self, query: str) -> List[str]:
        """Generate contextual suggested follow-up actions"""
        suggestions = []
        
        query_lower = query.lower()
        
        # Installation/Setup queries
        if any(word in query_lower for word in ["install", "setup", "configure", "deployment"]):
            suggestions.extend([
                "View system requirements and prerequisites",
                "Check step-by-step installation guide",
                "See configuration examples and best practices"
            ])
        
        # Error/Troubleshooting queries
        elif any(word in query_lower for word in ["error", "issue", "problem", "fix", "troubleshoot", "not working"]):
            suggestions.extend([
                "Check common issues and solutions",
                "View diagnostic procedures",
                "Access error code reference",
                "Contact technical support"
            ])
        
        # Technical/API queries
        elif any(word in query_lower for word in ["code", "api", "function", "method", "class", "interface"]):
            suggestions.extend([
                "View API documentation",
                "See code examples and snippets",
                "Explore technical integration guides"
            ])
        
        # Bot/Automation queries
        elif any(word in query_lower for word in ["bot", "robot", "agv", "automation"]):
            suggestions.extend([
                "Learn about bot operations",
                "View bot configuration guide",
                "Check bot maintenance procedures"
            ])
        
        # Safety/SOP queries
        elif any(word in query_lower for word in ["safety", "sop", "procedure", "guideline", "protocol"]):
            suggestions.extend([
                "Review safety guidelines",
                "Check standard operating procedures",
                "View emergency protocols"
            ])
        
        # Dashboard/UI queries
        elif any(word in query_lower for word in ["dashboard", "interface", "ui", "screen", "display"]):
            suggestions.extend([
                "Explore dashboard features",
                "View user interface guide",
                "Learn about report generation"
            ])
        
        # Default suggestions
        else:
            suggestions.extend([
                "Explore related documentation",
                "View practical examples",
                "Check getting started guide",
                "Ask about specific features"
            ])
        
        return suggestions[:4]  # Limit to 4 suggestions
        
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
