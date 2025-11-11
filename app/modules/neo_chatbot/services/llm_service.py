"""
LLM Service - Integration with Large Language Models (OpenAI/Anthropic)
Handles AI interactions for the chatbot
"""

import os
import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)


class LLMService:
    """
    Service for interacting with Large Language Models
    Supports OpenAI GPT and Anthropic Claude with automatic fallback
    """
    
    def __init__(self):
        """Initialize LLM service with API keys from environment"""
        self.groq_api_key = os.getenv("GROQ_API_KEY") or os.getenv("GROK_API_KEY")  # Groq (fast inference) - Priority 1
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")
        
        # Determine which provider to use (Groq has priority)
        self.provider = None
        self.groq_client = None
        self.openai_client = None
        self.anthropic_client = None
        
        # Try Groq first (Fast inference API - OpenAI-compatible)
        if self.groq_api_key:
            try:
                from openai import OpenAI
                self.groq_client = OpenAI(
                    api_key=self.groq_api_key,
                    base_url="https://api.groq.com/openai/v1"
                )
                self.provider = "groq"
                logger.info("✅ Groq (Fast Inference) LLM initialized")
            except ImportError:
                logger.warning("⚠️ OpenAI package not installed. Run: pip install openai")
            except Exception as e:
                logger.warning(f"⚠️ Groq initialization failed: {e}")
        
        # Fallback to OpenAI
        if not self.provider and self.openai_api_key:
            try:
                from openai import OpenAI
                self.openai_client = OpenAI(api_key=self.openai_api_key)
                self.provider = "openai"
                logger.info("✅ OpenAI LLM initialized")
            except ImportError:
                logger.warning("⚠️ OpenAI package not installed. Run: pip install openai")
            except Exception as e:
                logger.warning(f"⚠️ OpenAI initialization failed: {e}")
        
        # Fallback to Anthropic
        if not self.provider and self.anthropic_api_key:
            try:
                import anthropic
                self.anthropic_client = anthropic.Anthropic(api_key=self.anthropic_api_key)
                self.provider = "anthropic"
                logger.info("✅ Anthropic Claude LLM initialized")
            except ImportError:
                logger.warning("⚠️ Anthropic package not installed. Run: pip install anthropic")
            except Exception as e:
                logger.warning(f"⚠️ Anthropic initialization failed: {e}")
        
        if not self.provider:
            logger.warning("⚠️ No LLM API keys found - using mock responses")
            logger.warning("   Add GROQ_API_KEY, OPENAI_API_KEY, or ANTHROPIC_API_KEY to .env file")
            self.provider = "mock"
    
    def generate_response(
        self, 
        messages: List[Dict[str, str]], 
        system_prompt: Optional[str] = None,
        max_tokens: int = 1000,
        temperature: float = 0.7
    ) -> str:
        """
        Generate response from LLM
        
        Args:
            messages: Conversation messages [{"role": "user", "content": "..."}]
            system_prompt: System instructions for the LLM
            max_tokens: Maximum response length
            temperature: Creativity (0.0 = deterministic, 1.0 = creative)
            
        Returns:
            Generated response text
        """
        try:
            if self.provider == "groq":
                return self._generate_groq(messages, system_prompt, max_tokens, temperature)
            elif self.provider == "openai":
                return self._generate_openai(messages, system_prompt, max_tokens, temperature)
            elif self.provider == "anthropic":
                return self._generate_anthropic(messages, system_prompt, max_tokens, temperature)
            else:
                return self._generate_mock(messages)
        except Exception as e:
            logger.error(f"❌ Error generating LLM response: {e}", exc_info=True)
            return "I apologize, but I encountered an error processing your request. Please try again."
    
    def _generate_groq(
        self, 
        messages: List[Dict[str, str]], 
        system_prompt: Optional[str],
        max_tokens: int,
        temperature: float
    ) -> str:
        """Generate response using Groq (Fast Inference API)"""
        full_messages = []
        if system_prompt:
            full_messages.append({"role": "system", "content": system_prompt})
        full_messages.extend(messages)
        
        response = self.groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",  # Fast Llama model on Groq
            messages=full_messages,
            max_tokens=max_tokens,
            temperature=temperature
        )
        
        return response.choices[0].message.content
    
    def _generate_openai(
        self, 
        messages: List[Dict[str, str]], 
        system_prompt: Optional[str],
        max_tokens: int,
        temperature: float
    ) -> str:
        """Generate response using OpenAI GPT"""
        full_messages = []
        if system_prompt:
            full_messages.append({"role": "system", "content": system_prompt})
        full_messages.extend(messages)
        
        response = self.openai_client.chat.completions.create(
            model="gpt-4o-mini",  # Fast and cost-effective
            messages=full_messages,
            max_tokens=max_tokens,
            temperature=temperature
        )
        
        return response.choices[0].message.content
    
    def _generate_anthropic(
        self, 
        messages: List[Dict[str, str]], 
        system_prompt: Optional[str],
        max_tokens: int,
        temperature: float
    ) -> str:
        """Generate response using Anthropic Claude"""
        response = self.anthropic_client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=max_tokens,
            temperature=temperature,
            system=system_prompt or "You are NEO, an intelligent assistant for warehouse management.",
            messages=messages
        )
        
        return response.content[0].text
    
    def _generate_mock(self, messages: List[Dict[str, str]]) -> str:
        """Generate mock response when no API key is available"""
        user_message = messages[-1]["content"].lower()
        
        # Simple keyword-based responses
        if "database" in user_message or "sql" in user_message:
            return """To use the SQL assistant feature, I need access to an AI model. 
            
Please configure either:
- OpenAI API key: Add OPENAI_API_KEY to your .env file
- Anthropic API key: Add ANTHROPIC_API_KEY to your .env file

For database queries, I can help you:
- Generate SQL queries from natural language
- Explain database structure
- Show data insights

Once configured, just ask me questions like "Show me top 10 SKUs" and I'll generate the SQL for you!"""
        
        elif "scheduler" in user_message or "mining" in user_message:
            return """I can help with scheduler and mining issues!

Common issues I can diagnose:
- Scheduler not running
- Mining jobs not executing
- Custom parameters not working
- Database connection issues

Please describe your issue in detail, and I'll guide you through troubleshooting steps.

Note: For full AI capabilities, please add OPENAI_API_KEY or ANTHROPIC_API_KEY to your .env file."""
        
        elif "help" in user_message:
            return """Hi! I'm NEO Assistant. I can help you with:

**📚 Documentation Q&A**
- Answer questions about NEO system
- Explain features and configurations
- Provide examples and best practices

**💾 Database Assistant**  
- Convert questions to SQL queries
- Show data insights
- Explain database structure

**🔧 Diagnostic Support**
- Troubleshoot system issues
- Guide through problem resolution
- Provide solutions and prevention tips

**⚠️ Note**: Currently running in mock mode. For full AI capabilities:
1. Get an API key from OpenAI or Anthropic
2. Add to .env file: OPENAI_API_KEY=your_key
3. Restart the application

What would you like help with?"""
        
        else:
            return f"""I understand you're asking about: "{messages[-1]['content']}"

This is a mock response since no AI API key is configured.

To enable full chatbot functionality:
1. Obtain API key from OpenAI (https://platform.openai.com) or Anthropic
2. Add to .env file: OPENAI_API_KEY=sk-your-key-here
3. Restart the application

Currently available (with limited functionality):
- Issue diagnostics based on support knowledge base
- Database schema information
- System status checks

How can I help you today?"""
    
    def generate_embedding(self, text: str) -> List[float]:
        """
        Generate embedding vector for text (for vector search)
        
        Args:
            text: Text to embed
            
        Returns:
            Embedding vector (1536 dimensions for OpenAI)
        """
        try:
            # Note: Groq doesn't support embeddings, fall back to OpenAI or simple method
            if self.provider == "openai" and self.openai_client:
                response = self.openai_client.embeddings.create(
                    model="text-embedding-3-small",
                    input=text
                )
                return response.data[0].embedding
            else:
                # Return mock embedding for testing
                logger.debug("⚠️ Using mock embeddings - install OpenAI for real embeddings")
                # Simple hash-based mock embedding
                import hashlib
                hash_val = int(hashlib.md5(text.encode()).hexdigest(), 16)
                # Generate 1536 dimensions from hash
                embedding = [(hash_val >> (i % 128)) % 1000 / 1000.0 for i in range(1536)]
                return embedding
        except Exception as e:
            logger.error(f"❌ Error generating embedding: {e}")
            return [0.0] * 1536
    
    def is_available(self) -> bool:
        """Check if LLM service is available with real API"""
        return self.provider in ["openai", "anthropic"]
    
    def get_provider_info(self) -> Dict[str, Any]:
        """Get information about current LLM provider"""
        return {
            "provider": self.provider,
            "is_mock": self.provider == "mock",
            "has_openai": self.openai_api_key is not None,
            "has_anthropic": self.anthropic_api_key is not None,
            "model": "gpt-4o-mini" if self.provider == "openai" else "claude-3-5-sonnet" if self.provider == "anthropic" else "mock"
        }
