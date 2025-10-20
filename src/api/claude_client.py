#!/usr/bin/env python3
"""
Claude API Client - Anthropic API Wrapper

FIXED VERSION with:
- Consistent return formats
- Long timeout (20 minutes) for Bible generation
- Proper error handling
- Token counting fallback

British English throughout.
"""

import os
import time
from pathlib import Path
from typing import List, Dict, Optional, Any
from dataclasses import dataclass
import anthropic
from anthropic import Anthropic, APIError, RateLimitError, APITimeoutError
import dotenv
dotenv.load_dotenv()


@dataclass
class APIUsage:
    """API usage statistics"""
    input_tokens: int
    output_tokens: int
    cache_creation_input_tokens: int
    cache_read_input_tokens: int
    total_cost_usd: float
    total_cost_gbp: float


class ClaudeClient:
    """
    Wrapper for Anthropic Claude API
    
    Features:
    - Prompt caching (90% cost reduction)
    - Extended thinking
    - Long timeout for Bible generation
    - Cost tracking
    """
    
    # Pricing (as of January 2025)
    PRICING = {
        'claude-sonnet-4-5-20250929': {
            'input': 0.000003,      # $3 per 1M tokens
            'output': 0.000015,     # $15 per 1M tokens
            'cache_write': 0.00000375,
            'cache_read': 0.0000003,
        }
    }
    
    USD_TO_GBP = 1.27
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialise Claude client"""
        
        self.api_key = api_key or os.getenv('ANTHROPIC_API_KEY')
        
        if not self.api_key:
            raise ValueError("Set ANTHROPIC_API_KEY environment variable")
        
        self.client = Anthropic(api_key=self.api_key)
        
        # Cost tracking
        self.total_cost_usd = 0.0
        self.total_cost_gbp = 0.0
        self.call_count = 0
    
    def create_message(
        self,
        messages: List[Dict[str, str]],
        system: Optional[List[Dict[str, Any]]] = None,
        model: str = 'claude-sonnet-4-5-20250929',
        max_tokens: int = 16000,
        temperature: float = 1.0,
        thinking: Optional[Dict[str, Any]] = None,
        max_retries: int = 3
    ) -> Dict[str, Any]:
        """Create a message with Claude"""
        
        for attempt in range(max_retries):
            try:
                request_params = {
                    'model': model,
                    'max_tokens': max_tokens,
                    'temperature': temperature,
                    'messages': messages
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
                
                # LONG TIMEOUT FOR BIBLE GENERATION
                response = self.client.messages.create(
                    **request_params,
                    timeout=1200.0  # 20 minutes
                )
                
                elapsed = time.time() - start_time
                print(f"   ✅ Response received ({elapsed:.1f}s)")
                
                usage = self._calculate_usage(response, model)
                
                self.total_cost_usd += usage.total_cost_usd
                self.total_cost_gbp += usage.total_cost_gbp
                self.call_count += 1
                
                print(f"\n💰 API COST:")
                print(f"   Input tokens: {usage.input_tokens:,}")
                print(f"   Output tokens: {usage.output_tokens:,}")
                print(f"   This call: £{usage.total_cost_gbp:.4f}")
                print(f"   Session total: £{self.total_cost_gbp:.2f}")
                
                content = ""
                for block in response.content:
                    if block.type == 'text':
                        content += block.text
                
                return {
                    'content': content,
                    'usage': usage,
                    'response': response
                }
                
            except (RateLimitError, APITimeoutError, APIError) as e:
                if attempt == max_retries - 1:
                    raise
                time.sleep(2 ** attempt)
        
        raise Exception(f"Failed after {max_retries} retries")
    
    def _calculate_usage(self, response: Any, model: str) -> APIUsage:
        """Calculate costs from API response"""
        
        usage = response.usage
        pricing = self.PRICING.get(model, self.PRICING['claude-sonnet-4-5-20250929'])
        
        input_cost = usage.input_tokens * pricing['input']
        output_cost = usage.output_tokens * pricing['output']
        
        cache_creation_tokens = getattr(usage, 'cache_creation_input_tokens', 0)
        cache_read_tokens = getattr(usage, 'cache_read_input_tokens', 0)
        
        cache_creation_cost = cache_creation_tokens * pricing['cache_write'] if cache_creation_tokens > 0 else 0
        cache_read_cost = cache_read_tokens * pricing['cache_read'] if cache_read_tokens > 0 else 0
        
        total_cost_usd = input_cost + output_cost + cache_creation_cost + cache_read_cost
        total_cost_gbp = total_cost_usd * self.USD_TO_GBP
        
        return APIUsage(
            input_tokens=usage.input_tokens,
            output_tokens=usage.output_tokens,
            cache_creation_input_tokens=cache_creation_tokens,
            cache_read_input_tokens=cache_read_tokens,
            total_cost_usd=total_cost_usd,
            total_cost_gbp=total_cost_gbp
        )
    
    def count_tokens(self, text: str) -> int:
        """
        Count tokens using character-based estimation
        
        Standard estimation: ~4 characters per token
        """
        return len(text) // 4
    
    def estimate_cost_with_token_count(
        self,
        text: str,
        output_tokens: int,
        model: str = 'claude-sonnet-4-5-20250929',
        cached_tokens: int = 0
    ) -> Dict[str, Any]:
        """
        Estimate cost with token counting
        
        Returns:
            Dict with keys: input_tokens, output_tokens, gbp
        """
        
        input_tokens = self.count_tokens(text)
        pricing = self.PRICING.get(model, self.PRICING['claude-sonnet-4-5-20250929'])
        
        input_cost_usd = input_tokens * pricing['input']
        output_cost_usd = output_tokens * pricing['output']
        cache_read_cost_usd = cached_tokens * pricing['cache_read'] if cached_tokens > 0 else 0
        
        total_usd = input_cost_usd + output_cost_usd + cache_read_cost_usd
        total_gbp = total_usd * self.USD_TO_GBP
        
        # RETURN FORMAT MATCHES bible_builder.py EXPECTATIONS
        return {
            'input_tokens': input_tokens,
            'output_tokens': output_tokens,
            'cached_tokens': cached_tokens,
            'usd': total_usd,
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
        
        Returns:
            Dict with SAME keys as estimate_cost_with_token_count
        """
        
        # Use same logic as estimate_cost_with_token_count
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
    print("Claude client loaded successfully!")