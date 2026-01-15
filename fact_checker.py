import os
import json
from functools import lru_cache
from dotenv import load_dotenv
from tavily import TavilyClient
from model_config import get_llm_client

# Load environment variables
load_dotenv()

# Initialize clients
tavily_client = TavilyClient(api_key=os.environ.get("TAVILY_API_KEY"))
groq_llm = get_llm_client()  # Automatically uses configured provider and model


@lru_cache(maxsize=128)
def research_claim(claim: str) -> dict:
    """
    Phase 1: Researcher - Gather evidence from the web using Tavily.
    
    Args:
        claim: The claim string to research
        
    Returns:
        dict with 'snippets' (list of evidence) and 'error' (if any)
    """
    try:
        # Search the web for evidence
        search_result = tavily_client.search(
            query=claim, 
            search_depth="advanced",  # Use advanced for better quality
            max_results=5
        )
        
        # Extract relevant snippets with URLs
        snippets = []
        for result in search_result.get('results', [])[:5]:
            snippets.append({
                'content': result.get('content', ''),
                'url': result.get('url', ''),
                'title': result.get('title', '')
            })
        
        return {
            'snippets': snippets,
            'error': None
        }
        
    except Exception as e:
        return {
            'snippets': [],
            'error': f"Research failed: {str(e)}"
        }


def judge_claim(claim: str, evidence: dict) -> dict:
    """
    Phase 2: Judge - Analyze the claim against evidence using LLM.
    
    Args:
        claim: The original claim to verify
        evidence: Dictionary containing snippets from research phase
        
    Returns:
        dict with 'verdict', 'explanation', and 'confidence'
    """
    try:
        snippets = evidence.get('snippets', [])
        
        if not snippets:
            return {
                'verdict': 'UNVERIFIABLE',
                'explanation': 'No evidence found to verify this claim.',
                'confidence': 'LOW'
            }
        
        # Construct evidence text
        evidence_text = "\n\n".join([
            f"Source {i+1} ({snippet['title']}):\n{snippet['content']}"
            for i, snippet in enumerate(snippets)
        ])
        
        # Create prompt for LLM
        prompt = f"""You are a fact-checker. Analyze the following claim against the provided evidence.

CLAIM: {claim}

EVIDENCE FROM WEB SOURCES:
{evidence_text}

Based ONLY on the evidence provided above, determine if the claim is:
- TRUE: The evidence clearly supports the claim
- FALSE: The evidence clearly contradicts the claim
- MISLEADING: The claim is partially true but missing important context or is framed deceptively
- UNVERIFIABLE: The evidence is insufficient to make a determination

Respond in JSON format with this exact structure:
{{
  "verdict": "TRUE|FALSE|MISLEADING|UNVERIFIABLE",
  "explanation": "A clear 1-2 sentence explanation of your verdict",
  "confidence": "HIGH|MEDIUM|LOW"
}}

JSON response:"""
        
        # Get LLM response with retry logic
        max_retries = 3
        base_delay = 5  # seconds
        
        for attempt in range(max_retries):
            try:
                response = groq_llm.invoke(prompt)
                content = response.content.strip()
                break
            except Exception as e:
                error_str = str(e)
                if "429" in error_str or "rate limit" in error_str.lower():
                    if attempt < max_retries - 1:
                        wait_time = base_delay * (2 ** attempt)  # Exponential backoff: 5, 10, 20...
                        import time
                        print(f"  ⚠️ Rate limit hit. Retrying in {wait_time}s...")
                        time.sleep(wait_time)
                        continue
                # If not rate limit or max retries reached, re-raise
                raise e
        
        # Clean response if wrapped in markdown
        if content.startswith("```"):
            parts = content.split("```")
            if len(parts) >= 2:
                content = parts[1]
                if content.startswith("json") or content.startswith("JSON"):
                    content = content[4:]
                content = content.strip()
        
        # Try to find JSON object in the response
        if not content.startswith('{'):
            # Look for the first { and last }
            start_idx = content.find('{')
            end_idx = content.rfind('}')
            if start_idx != -1 and end_idx != -1:
                content = content[start_idx:end_idx+1]
        
        # Parse JSON response
        try:
            result = json.loads(content)
        except json.JSONDecodeError:
            # If parsing fails, try regex extraction
            import re
            match = re.search(r'\{.*\}', content, re.DOTALL)
            if match:
                try:
                    result = json.loads(match.group(0))
                except:
                    # If all else fails, return a default response
                    return {
                        'verdict': 'UNVERIFIABLE',
                        'explanation': 'Unable to parse LLM response.',
                        'confidence': 'LOW'
                    }
            else:
                return {
                    'verdict': 'UNVERIFIABLE',
                    'explanation': 'Unable to parse LLM response.',
                    'confidence': 'LOW'
                }
        
        return {
            'verdict': result.get('verdict', 'UNVERIFIABLE'),
            'explanation': result.get('explanation', 'Unable to determine verdict.'),
            'confidence': result.get('confidence', 'LOW')
        }
        
    except Exception as e:
        return {
            'verdict': 'ERROR',
            'explanation': f'Analysis failed: {str(e)}',
            'confidence': 'LOW'
        }


def fact_check_claim(claim_obj: dict) -> dict:
    """
    Phase 3: Packager - Orchestrate the full fact-checking pipeline.
    
    Args:
        claim_obj: Dictionary with 'time' and 'claim' keys
        
    Returns:
        Complete fact-check object with all metadata
    """
    claim_text = claim_obj.get('claim', '')
    timestamp = claim_obj.get('time', 'Unknown')
    
    print(f"Fact-checking: {claim_text[:60]}...")
    
    # Phase 1: Research
    evidence = research_claim(claim_text)
    
    if evidence.get('error'):
        return {
            'timestamp': timestamp,
            'claim': claim_text,
            'status': 'ERROR',
            'explanation': evidence['error'],
            'source_url': None,
            'confidence': 'N/A',
            'sources': []
        }
    
    # Phase 2: Judge
    judgment = judge_claim(claim_text, evidence)
    
    # Phase 3: Package
    # Get the most relevant source URL
    snippets = evidence.get('snippets', [])
    primary_source = snippets[0] if snippets else None
    
    return {
        'timestamp': timestamp,
        'claim': claim_text,
        'status': judgment['verdict'],
        'explanation': judgment['explanation'],
        'confidence': judgment['confidence'],
        'source_url': primary_source['url'] if primary_source else None,
        'sources': [
            {
                'title': s['title'],
                'url': s['url'],
                'snippet': s['content'][:200] + '...' if len(s['content']) > 200 else s['content']
            }
            for s in snippets[:3]  # Include top 3 sources
        ]
    }


if __name__ == "__main__":
    # Test with a sample claim
    test_claim = {
        'time': '00:15',
        'claim': 'Python was created in 1991'
    }
    
    result = fact_check_claim(test_claim)
    print(json.dumps(result, indent=2, ensure_ascii=False))
