#!/usr/bin/env python3
"""
Claude API Client - Anthropic API Wrapper

Handles:
- API calls with prompt caching
- Extended thinking support
- Retry logic with exponential backoff
- Cost tracking
- Error handling

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
dotenv.load_dotenv()  # Load .env file if present


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
    - Retry logic
    - Cost tracking
    """
    
    # Pricing (as of Oct 2024)
    PRICING = {
        'claude-sonnet-4-5-20250929': {
            'input': 0.000003,      # $3 per 1M tokens
            'output': 0.000015,     # $15 per 1M tokens
            'cache_write': 0.00000375,  # $3.75 per 1M tokens
            'cache_read': 0.0000003,    # $0.30 per 1M tokens (90% discount!)
        }
    }
    
    USD_TO_GBP = 1.27  # Approximate exchange rate
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialise Claude client
        
        Args:
            api_key: Anthropic API key (or reads from ANTHROPIC_API_KEY env var)
        """
        
        self.api_key = api_key or os.getenv('ANTHROPIC_API_KEY')
        
        if not self.api_key:
            raise ValueError(
                "No API key provided. Either pass api_key parameter or "
                "set ANTHROPIC_API_KEY environment variable."
            )
        
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
        """
        Create a message with Claude
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            system: System prompt (can include cache_control)
            model: Model to use
            max_tokens: Maximum output tokens
            temperature: Sampling temperature (0-1)
            thinking: Extended thinking config (e.g., {'type': 'enabled', 'budget_tokens': 10000})
            max_retries: Number of retries on failure
        
        Returns:
            Response dict with 'content', 'usage', 'cost' keys
        """
        
        for attempt in range(max_retries):
            try:
                # Build request parameters
                request_params = {
                    'model': model,
                    'max_tokens': max_tokens,
                    'temperature': temperature,
                    'messages': messages
                }
                
                # Add system prompt if provided
                if system:
                    request_params['system'] = system
                
                # Add thinking if requested
                if thinking:
                    request_params['thinking'] = thinking
                
                # Make API call
                print(f"\n🤖 Calling Claude API...")
                print(f"   Model: {model}")
                print(f"   Max tokens: {max_tokens:,}")
                if thinking:
                    print(f"   Extended thinking: {thinking.get('budget_tokens', 0):,} tokens")
                if system:
                    cached_blocks = sum(1 for block in system if block.get('cache_control'))
                    print(f"   Cached blocks: {cached_blocks}")
                
                start_time = time.time()
                
                response = self.client.messages.create(**request_params)
                
                elapsed = time.time() - start_time
                print(f"   ✅ Response received ({elapsed:.1f}s)")
                
                # Calculate costs
                usage = self._calculate_usage(response, model)
                
                # Track totals
                self.total_cost_usd += usage.total_cost_usd
                self.total_cost_gbp += usage.total_cost_gbp
                self.call_count += 1
                
                # Print cost info
                print(f"\n💰 API COST:")
                print(f"   Input tokens: {usage.input_tokens:,}")
                print(f"   Output tokens: {usage.output_tokens:,}")
                
                if usage.cache_creation_input_tokens > 0:
                    print(f"   Cache write tokens: {usage.cache_creation_input_tokens:,}")
                
                if usage.cache_read_input_tokens > 0:
                    savings_pct = (usage.cache_read_input_tokens / 
                                 (usage.input_tokens + usage.cache_read_input_tokens) * 100)
                    print(f"   Cache read tokens: {usage.cache_read_input_tokens:,} "
                          f"(💰 {savings_pct:.0f}% cost saved!)")
                
                print(f"   This call: ${usage.total_cost_usd:.4f} (£{usage.total_cost_gbp:.4f})")
                print(f"   Total session: £{self.total_cost_gbp:.2f} ({self.call_count} calls)")
                
                # Extract text content
                text_content = ""
                thinking_content = ""
                
                for block in response.content:
                    if block.type == 'text':
                        text_content += block.text
                    elif block.type == 'thinking':
                        thinking_content += block.thinking
                
                return {
                    'content': text_content,
                    'thinking': thinking_content,
                    'usage': usage,
                    'raw_response': response
                }
            
            except RateLimitError as e:
                if attempt < max_retries - 1:
                    wait_time = 2 ** attempt  # Exponential backoff
                    print(f"   ⚠️  Rate limit hit. Retrying in {wait_time}s...")
                    time.sleep(wait_time)
                else:
                    raise Exception(f"Rate limit exceeded after {max_retries} retries") from e
            
            except APITimeoutError as e:
                if attempt < max_retries - 1:
                    wait_time = 2 ** attempt
                    print(f"   ⚠️  Timeout. Retrying in {wait_time}s...")
                    time.sleep(wait_time)
                else:
                    raise Exception(f"API timeout after {max_retries} retries") from e
            
            except APIError as e:
                # For other API errors, don't retry
                raise Exception(f"API error: {e}") from e
    
    def count_tokens(self, text: str) -> int:
        """
        Count tokens in text using Anthropic's token counting
        
        Args:
            text: Text to count
        
        Returns:
            Token count
        """
        
        # Use Anthropic's count_tokens method
        response = self.client.count_tokens(text)
        return response


    def estimate_cost_with_token_count(
        self,
        text: str,
        output_tokens: int = 4000,
        model: str = 'claude-sonnet-4-5-20250929'
    ) -> Dict[str, Any]:
        """
        Estimate cost with precise token counting
        
        Args:
            text: Input text
            output_tokens: Expected output tokens
            model: Model to use
        
        Returns:
            Dict with costs and accurate token count
        """
        
        # Get accurate token count
        try:
            input_tokens = self.count_tokens(text)
        except:
            # Fallback to estimate if API fails
            input_tokens = len(text) // 4
        
        pricing = self.PRICING.get(model, self.PRICING['claude-sonnet-4-5-20250929'])
        
        input_cost = input_tokens * pricing['input']
        output_cost = output_tokens * pricing['output']
        
        total_usd = input_cost + output_cost
        total_gbp = total_usd * self.USD_TO_GBP
        
        return {
            'usd': total_usd,
            'gbp': total_gbp,
            'input_tokens': input_tokens,
            'output_tokens': output_tokens
        }

    def _calculate_usage(self, response: Any, model: str) -> APIUsage:
        """
        Calculate costs from API response
        
        Args:
            response: Anthropic API response
            model: Model used
        
        Returns:
            APIUsage object with costs
        """
        
        usage = response.usage
        pricing = self.PRICING.get(model, self.PRICING['claude-sonnet-4-5-20250929'])
        
        # Calculate costs
        input_cost = usage.input_tokens * pricing['input']
        output_cost = usage.output_tokens * pricing['output']
        
        # Cache costs
        cache_creation_cost = 0.0
        cache_read_cost = 0.0
        
        cache_creation_tokens = getattr(usage, 'cache_creation_input_tokens', 0)
        cache_read_tokens = getattr(usage, 'cache_read_input_tokens', 0)
        
        if cache_creation_tokens > 0:
            cache_creation_cost = cache_creation_tokens * pricing['cache_write']
        
        if cache_read_tokens > 0:
            cache_read_cost = cache_read_tokens * pricing['cache_read']
        
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
    
    def create_cached_message(
        self,
        user_message: str,
        system_prompt: str,
        cached_context: str,
        model: str = 'claude-sonnet-4-5-20250929',
        max_tokens: int = 16000,
        thinking: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Create message with cached system context (Case Bible pattern)
        
        This is the optimal pattern for Case Bible queries:
        - System prompt (cached)
        - Case Bible context (cached)
        - User message (not cached - changes each time)
        
        Args:
            user_message: The user's query
            system_prompt: System instructions (will be cached)
            cached_context: Case Bible or other context (will be cached)
            model: Model to use
            max_tokens: Max output tokens
            thinking: Extended thinking config
        
        Returns:
            Response dict
        """
        
        # Build system prompt with cache control
        system = [
            {
                'type': 'text',
                'text': system_prompt,
                'cache_control': {'type': 'ephemeral'}
            },
            {
                'type': 'text',
                'text': cached_context,
                'cache_control': {'type': 'ephemeral'}
            }
        ]
        
        # Build messages
        messages = [
            {
                'role': 'user',
                'content': user_message
            }
        ]
        
        return self.create_message(
            messages=messages,
            system=system,
            model=model,
            max_tokens=max_tokens,
            thinking=thinking
        )
    
    def estimate_cost(
        self,
        input_text: str,
        output_tokens: int = 4000,
        cached_tokens: int = 0,
        model: str = 'claude-sonnet-4-5-20250929'
    ) -> Dict[str, float]:
        """
        Estimate cost before making API call
        
        Args:
            input_text: Input text to estimate tokens
            output_tokens: Expected output tokens
            cached_tokens: How many tokens will be cached
            model: Model to use
        
        Returns:
            Dict with 'usd' and 'gbp' costs
        """
        
        # Rough token estimate (4 chars ≈ 1 token)
        input_tokens = len(input_text) // 4
        
        pricing = self.PRICING.get(model, self.PRICING['claude-sonnet-4-5-20250929'])
        
        # Calculate costs
        input_cost = input_tokens * pricing['input']
        output_cost = output_tokens * pricing['output']
        
        # If using cache
        cache_read_cost = 0.0
        if cached_tokens > 0:
            cache_read_cost = cached_tokens * pricing['cache_read']
        
        total_usd = input_cost + output_cost + cache_read_cost
        total_gbp = total_usd * self.USD_TO_GBP
        
        return {
            'usd': total_usd,
            'gbp': total_gbp,
            'breakdown': {
                'input_tokens': input_tokens,
                'output_tokens': output_tokens,
                'cached_tokens': cached_tokens
            }
        }
    
    def get_session_stats(self) -> Dict[str, Any]:
        """
        Get session statistics
        
        Returns:
            Dict with total costs and call count
        """
        
        return {
            'total_calls': self.call_count,
            'total_cost_usd': self.total_cost_usd,
            'total_cost_gbp': self.total_cost_gbp,
            'avg_cost_per_call_gbp': (
                self.total_cost_gbp / self.call_count if self.call_count > 0 else 0
            )
        }


def test_client():
    """Test the Claude client"""
    
    print("="*70)
    print("TESTING CLAUDE API CLIENT")
    print("="*70)
    
    # Initialize client
    client = ClaudeClient()
    
    # Test 1: Simple message
    print("\n📝 TEST 1: Simple message")
    response = client.create_message(
        messages=[{
            'role': 'user',
            'content': 'Say hello in exactly 5 words using British English.'
        }],
        max_tokens=100
    )
    
    print(f"\nResponse: {response['content']}")
    
    # Test 2: With system prompt and caching
    print("\n📝 TEST 2: Cached system prompt")
    
    system_prompt = "You are a senior litigation barrister."
    case_context = """
    CASE: Lismore Capital v Process Holdings
    TRIBUNAL: LCIA
    CLAIM: Breach of warranty regarding disclosure of liabilities
    """
    
    response = client.create_cached_message(
        user_message="Summarise this case in one sentence.",
        system_prompt=system_prompt,
        cached_context=case_context,
        max_tokens=200
    )
    
    print(f"\nResponse: {response['content']}")
    
    # Test 3: Second query using cache (should show cache hit)
    print("\n📝 TEST 3: Second query (cache should be hit)")
    
    response = client.create_cached_message(
        user_message="What tribunal is this case in?",
        system_prompt=system_prompt,
        cached_context=case_context,
        max_tokens=100
    )
    
    print(f"\nResponse: {response['content']}")
    
    # Show session stats
    print("\n" + "="*70)
    print("SESSION STATISTICS")
    print("="*70)
    
    stats = client.get_session_stats()
    print(f"\nTotal calls: {stats['total_calls']}")
    print(f"Total cost: £{stats['total_cost_gbp']:.4f}")
    print(f"Average per call: £{stats['avg_cost_per_call_gbp']:.4f}")


if __name__ == '__main__':
    test_client()