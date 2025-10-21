#!/usr/bin/env python3
"""
Claude API Client - Complete Fixed Version

COMBINES:
- create_message() method (for bible_builder.py)
- Fixed cost estimation methods (matching dictionary formats)
- Prompt caching support
- Extended thinking support
- Long timeout for Bible generation

British English throughout.
"""

import os
import time
from typing import List, Dict, Optional, Any
from anthropic import Anthropic, APIError, RateLimitError, APITimeoutError
import logging

logger = logging.getLogger(__name__)


class ClaudeClient:
    """
    Complete Claude API wrapper
    
    Features:
    - create_message() method (for bible_builder)
    - Prompt caching (90% savings)
    - Extended thinking
    - Cost tracking
    - Long timeout (20 minutes)
    """
    
    # Pricing per 1M tokens (as of October 2025)
    PRICING = {
        'claude-sonnet-4-5-20250929': {
            'input': 3.0,      # $3 per 1M tokens
            'output': 15.0,    # $15 per 1M tokens
            'cache_write': 3.75,
            'cache_read': 0.30
        }
    }
    
    USD_TO_GBP = 0.79
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialise Claude client"""
        
        self.api_key = api_key or os.getenv('ANTHROPIC_API_KEY')
        
        if not self.api_key:
            raise ValueError(
                "ANTHROPIC_API_KEY not found! "
                "Set it in .env file or environment."
            )
        
        self.client = Anthropic(api_key=self.api_key)
        
        # Cost tracking
        self.total_cost_usd = 0.0
        self.total_cost_gbp = 0.0
        self.call_count = 0
        
        logger.info("Claude client initialised")
    
    def create_message(
        self,
        messages: List[Dict[str, str]],
        system: Optional[List[Dict[str, Any]]] = None,
        model: str = 'claude-sonnet-4-5-20250929',
        max_tokens: int = 32000,
        temperature: float = 1.0,
        thinking: Optional[Dict[str, Any]] = None,
        max_retries: int = 3
    ) -> Dict[str, Any]:
        """
        Create a message with Claude (for bible_builder.py)
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            system: Optional system blocks (for caching)
            model: Model name
            max_tokens: Maximum output tokens
            temperature: 0.0-1.0
            thinking: Extended thinking config
            max_retries: Number of retry attempts
        
        Returns:
            Dict with 'content' and 'usage' keys
        """
        
        for attempt in range(max_retries):
            try:
                request_params = {
                    'model': model,
                    'max_tokens': max_tokens,
                    'temperature': temperature,
                    'messages': messages,
                    'timeout': 1200.0  # 20 minute timeout
                }
                
                if system:
                    request_params['system'] = system
                
                if thinking:
                    request_params['thinking'] = thinking
                
                print(f"\n🤖 Calling Claude API...")
                print(f"   Model: {model}")
                print(f"   Max tokens: {max_tokens:,}")
                if thinking:
                    print(f"   Extended thinking: {thinking.get('budget_tokens', 0):,} tokens")
                
                start_time = time.time()
                
                response = self.client.messages.create(**request_params)
                
                elapsed = time.time() - start_time
                print(f"   ✅ Response received ({elapsed:.1f}s)")
                
                # Calculate cost
                usage_info = self._calculate_cost(response, model)
                
                self.total_cost_usd += usage_info['total_cost_usd']
                self.total_cost_gbp += usage_info['total_cost_gbp']
                self.call_count += 1
                
                print(f"\n💰 API COST:")
                print(f"   Input tokens: {usage_info['input_tokens']:,}")
                print(f"   Output tokens: {usage_info['output_tokens']:,}")
                if usage_info.get('cache_read_tokens', 0) > 0:
                    print(f"   Cache read tokens: {usage_info['cache_read_tokens']:,}")
                print(f"   This call: £{usage_info['total_cost_gbp']:.4f}")
                print(f"   Session total: £{self.total_cost_gbp:.2f}")
                
                # Extract content
                content = ""
                for block in response.content:
                    if block.type == 'text':
                        content += block.text
                
                return {
                    'content': content,
                    'usage': usage_info,
                    'response': response
                }
            
            except RateLimitError as e:
                if attempt < max_retries - 1:
                    wait = 2 ** attempt
                    print(f"   ⚠️ Rate limit hit, waiting {wait}s...")
                    time.sleep(wait)
                else:
                    raise
            
            except APITimeoutError as e:
                if attempt < max_retries - 1:
                    print(f"   ⚠️ Timeout, retrying...")
                else:
                    raise
            
            except Exception as e:
                logger.error(f"API call failed: {e}")
                raise
    
    def _calculate_cost(self, response, model: str) -> Dict[str, Any]:
        """
        Calculate cost from API response
        
        Args:
            response: Anthropic Message object
            model: Model name
        
        Returns:
            Dict with cost breakdown
        """
        
        usage = response.usage
        pricing = self.PRICING.get(model, self.PRICING['claude-sonnet-4-5-20250929'])
        
        # Input tokens
        input_tokens = usage.input_tokens
        input_cost_usd = (input_tokens / 1_000_000) * pricing['input']
        
        # Output tokens
        output_tokens = usage.output_tokens
        output_cost_usd = (output_tokens / 1_000_000) * pricing['output']
        
        # Cache tokens (if any)
        cache_read_tokens = getattr(usage, 'cache_read_input_tokens', 0)
        cache_cost_usd = (cache_read_tokens / 1_000_000) * pricing['cache_read']
        
        # Cache write tokens (if any)
        cache_write_tokens = getattr(usage, 'cache_creation_input_tokens', 0)
        cache_write_cost_usd = (cache_write_tokens / 1_000_000) * pricing['cache_write']
        
        # Total
        total_usd = input_cost_usd + output_cost_usd + cache_cost_usd + cache_write_cost_usd
        total_gbp = total_usd * self.USD_TO_GBP
        
        return {
            'input_tokens': input_tokens,
            'output_tokens': output_tokens,
            'cache_read_tokens': cache_read_tokens,
            'cache_write_tokens': cache_write_tokens,
            'total_cost_usd': total_usd,
            'total_cost_gbp': total_gbp
        }
    
    def count_tokens(self, text: str) -> int:
        """
        Estimate token count (character-based approximation)
        
        Args:
            text: Text to count
        
        Returns:
            Estimated token count
        """
        # Simple estimation: ~4 characters per token
        return len(text) // 4
    
    def estimate_cost_with_token_count(
        self,
        text: str,
        output_tokens: int,
        model: str = 'claude-sonnet-4-5-20250929',
        cached_tokens: int = 0
    ) -> Dict[str, Any]:
        """
        Estimate cost before API call (for bible_builder)
        
        CRITICAL: Returns format that matches what bible_builder expects
        
        Args:
            text: Input text
            output_tokens: Expected output tokens
            model: Model name
            cached_tokens: Expected cached tokens
        
        Returns:
            Dict with keys: input_tokens, output_tokens, cached_tokens, gbp
        """
        
        input_tokens = self.count_tokens(text)
        pricing = self.PRICING.get(model, self.PRICING['claude-sonnet-4-5-20250929'])
        
        input_cost_usd = (input_tokens / 1_000_000) * pricing['input']
        output_cost_usd = (output_tokens / 1_000_000) * pricing['output']
        cache_read_cost_usd = (cached_tokens / 1_000_000) * pricing['cache_read'] if cached_tokens > 0 else 0
        
        total_usd = input_cost_usd + output_cost_usd + cache_read_cost_usd
        total_gbp = total_usd * self.USD_TO_GBP
        
        # CRITICAL: Format matches what bible_builder.py line 419 expects
        return {
            'input_tokens': input_tokens,
            'output_tokens': output_tokens,
            'cached_tokens': cached_tokens,
            'gbp': total_gbp
        }
    
    def estimate_cost_simple(
        self,
        input_text: str,
        output_tokens: int,
        model: str = 'claude-sonnet-4-5-20250929',
        cached_tokens: int = 0
    ) -> Dict[str, Any]:
        """
        Simple fallback cost estimation
        
        FIXED: Returns IDENTICAL format to estimate_cost_with_token_count
        
        Args:
            input_text: Input text
            output_tokens: Expected output tokens
            model: Model name
            cached_tokens: Expected cached tokens
        
        Returns:
            Dict with SAME keys as estimate_cost_with_token_count
        """
        
        # Use same logic
        return self.estimate_cost_with_token_count(
            text=input_text,
            output_tokens=output_tokens,
            model=model,
            cached_tokens=cached_tokens
        )
    
    def get_session_stats(self) -> Dict[str, Any]:
        """Get session statistics"""
        
        return {
            'total_calls': self.call_count,
            'total_cost_usd': self.total_cost_usd,
            'total_cost_gbp': self.total_cost_gbp,
            'avg_cost_per_call_gbp': (
                self.total_cost_gbp / self.call_count if self.call_count > 0 else 0
            )
        }


if __name__ == '__main__':
    print("✅ Claude client module loaded successfully!")
    print("\nKey features:")
    print("  - create_message() for bible_builder")
    print("  - Fixed cost estimation methods")
    print("  - Prompt caching support")
    print("  - Extended thinking")
    print("  - Long timeout (20 minutes)")