import os
import json
from dotenv import load_dotenv
from fact_checker import fact_check_claim
from model_config import get_llm_client, get_max_chunk_chars

# Load environment variables from .env file
load_dotenv()

# Get LLM client (automatically uses configured provider and model)
groq_llm = get_llm_client()

def extract_claims(transcript_file):
    with open(transcript_file, 'r', encoding='utf-8') as f:
        transcript = f.read()
    
    # Get dynamic chunk size based on current model's token limit
    max_chars = get_max_chunk_chars()
    
    if len(transcript) <= max_chars:
        # Process normally if transcript is small enough
        return _extract_claims_from_chunk(transcript)
    else:
        # Split into chunks and process separately
        print(f"Transcript is large ({len(transcript)} chars). Splitting into chunks...")
        chunks = []
        lines = transcript.split('\n')
        current_chunk = ""
        
        for line in lines:
            if len(current_chunk) + len(line) + 1 <= max_chars:
                current_chunk += line + '\n'
            else:
                if current_chunk:
                    chunks.append(current_chunk)
                current_chunk = line + '\n'
        
        if current_chunk:
            chunks.append(current_chunk)
        
        print(f"Processing {len(chunks)} chunks...")
        all_claims = []
        
        for i, chunk in enumerate(chunks, 1):
            print(f"Processing chunk {i}/{len(chunks)}...")
            try:
                chunk_claims = _extract_claims_from_chunk(chunk)
                all_claims.extend(chunk_claims)
            except Exception as e:
                print(f"Error processing chunk {i}: {e}")
                continue
        
        return all_claims


def _extract_claims_from_chunk(transcript):
    """Helper function to extract claims from a single transcript chunk"""
    prompt = f"""You are a JSON generator. Extract factual claims from the transcript below.

IMPORTANT: Return ONLY a valid JSON array. Do not include any explanations, comments, or text outside the JSON.

Format (copy this structure exactly):
[
  {{"time": "0.13s", "claim": "specific factual claim here"}},
  {{"time": "5.20s", "claim": "another factual claim"}}
]

Rules:
- Only include factual claims (statements that can be verified as true or false)
- GROUP RELATED CLAIMS: If multiple claims are about the same topic or event, combine them into ONE comprehensive claim
- Skip greetings, opinions, and non-factual statements
- Skip sponsors, advertisements, promotional content, and product placements
- Skip calls-to-action like "subscribe", "like", "share", etc.
- Use the timestamp of the FIRST mention when grouping related claims
- Return ONLY the JSON array, nothing else

Example of grouping:
Instead of:
  {{"time": "26s", "claim": "The ash cloud was massive"}},
  {{"time": "31s", "claim": "The ash cloud spread to India"}},
  {{"time": "44s", "claim": "Flights were canceled due to ash"}}

Do this:
  {{"time": "26s", "claim": "The volcanic ash cloud was massive, visible from space, spread to Oman, Yemen, Pakistan, and India, causing flight cancellations in Delhi and the Middle East"}}

Transcript:
{transcript}

JSON array (no other text):"""
    
    response = groq_llm.invoke(prompt)
    content = response.content.strip()
    
    # Debug: print first 200 chars of response
    print(f"LLM Response preview: {content[:200]}...")
    
    # Clean response if wrapped in markdown
    if content.startswith("```"):
        # Find the JSON content between code fences
        parts = content.split("```")
        if len(parts) >= 2:
            content = parts[1]
            # Remove language identifier if present
            if content.startswith("json") or content.startswith("JSON"):
                content = content[4:]
            content = content.strip()
    
    # Try to find JSON array in the response - be very aggressive
    if not content.startswith('['):
        # Look for the first [ and last ]
        start_idx = content.find('[')
        end_idx = content.rfind(']')
        if start_idx != -1 and end_idx != -1:
            content = content[start_idx:end_idx+1]
        else:
            # No JSON array found at all
            print(f"ERROR: No JSON array found in response")
            print(f"Full response: {content}")
            return []
    
    # Parse JSON
    try:
        claims = json.loads(content)
        if not isinstance(claims, list):
            print(f"ERROR: Parsed JSON is not a list: {type(claims)}")
            return []
        print(f"Successfully extracted {len(claims)} claims")
        return claims
    except json.JSONDecodeError as e:
        # If parsing fails, try to extract JSON more aggressively
        import re
        print(f"JSON decode error: {e}")
        
        # Look for array pattern with more flexibility
        match = re.search(r'\[\s*\{.*?\}\s*\]', content, re.DOTALL)
        if match:
            try:
                claims = json.loads(match.group(0))
                print(f"Successfully extracted {len(claims)} claims using regex")
                return claims
            except:
                pass
        
        # Try to find individual claim objects and build array
        claim_pattern = r'\{\s*"time"\s*:\s*"[^"]+"\s*,\s*"claim"\s*:\s*"[^"]+"\s*\}'
        claim_matches = re.findall(claim_pattern, content)
        if claim_matches:
            try:
                claims = [json.loads(match) for match in claim_matches]
                print(f"Successfully extracted {len(claims)} claims using pattern matching")
                return claims
            except:
                pass
        
        # Last resort: return empty array with error message
        print(f"Failed to parse JSON response.")
        print(f"Content preview: {content[:500]}...")
        return []

def fact_check_all_claims(claims_file="claims.json", output_file="fact_checked_report.json"):
    """
    Process all claims through the fact-checker and generate a report.
    
    Args:
        claims_file: Path to the claims JSON file
        output_file: Path to save the fact-checked report
    """
    # Load claims
    with open(claims_file, 'r', encoding='utf-8') as f:
        claims = json.load(f)
    
    print(f"\n{'='*60}")
    print(f"Starting fact-check of {len(claims)} claims...")
    print(f"{'='*60}\n")
    
    # Process each claim in parallel
    fact_checked_claims = [None] * len(claims)
    
    import concurrent.futures
    
    def process_and_store(index, claim):
        print(f"[{index}/{len(claims)}] Processing claim...")
        result = fact_check_claim(claim)
        print(f"[{index}/{len(claims)}] ✓ Done: {result['status']}")
        return index, result

    # Use ThreadPoolExecutor for parallel processing
    # Limit workers to 2 to avoid rate limits (Groq has strict limits)
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
        futures = {executor.submit(process_and_store, i, claim): i for i, claim in enumerate(claims, 1)}
        
        for future in concurrent.futures.as_completed(futures):
            try:
                index, result = future.result()
                fact_checked_claims[index-1] = result
            except Exception as e:
                print(f"Error processing claim: {e}")
    
    # Filter out any None results (in case of errors)
    fact_checked_claims = [c for c in fact_checked_claims if c is not None]
    
    # Generate summary statistics
    verdicts = [c['status'] for c in fact_checked_claims]
    summary = {
        'total_claims': len(fact_checked_claims),
        'true': verdicts.count('TRUE'),
        'false': verdicts.count('FALSE'),
        'misleading': verdicts.count('MISLEADING'),
        'unverifiable': verdicts.count('UNVERIFIABLE'),
        'errors': verdicts.count('ERROR')
    }
    
    # Create final report
    report = {
        'summary': summary,
        'claims': fact_checked_claims
    }
    
    # Save report
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    print(f"\n{'='*60}")
    print(f"Fact-checking complete!")
    print(f"{'='*60}")
    print(f"Summary:")
    print(f"  ✓ TRUE: {summary['true']}")
    print(f"  ✗ FALSE: {summary['false']}")
    print(f"  ⚠ MISLEADING: {summary['misleading']}")
    print(f"  ? UNVERIFIABLE: {summary['unverifiable']}")
    print(f"  ! ERRORS: {summary['errors']}")
    print(f"\nReport saved to: {output_file}")
    
    return report

if __name__ == "__main__":
    import sys
    
    # Check command line arguments
    if len(sys.argv) > 1 and sys.argv[1] == "extract":
        # Extract claims from transcript
        transcript_file = "transcript.txt"
        print("Extracting claims from transcript...")
        claims = extract_claims(transcript_file)
        
        print(json.dumps(claims, indent=2, ensure_ascii=False))
        
        # Save to file
        with open("claims.json", 'w', encoding='utf-8') as f:
            json.dump(claims, f, indent=2, ensure_ascii=False)
        print(f"\nExtracted {len(claims)} claims and saved to claims.json")
    
    elif len(sys.argv) > 1 and sys.argv[1] == "factcheck":
        # Fact-check existing claims
        fact_check_all_claims()
    
    else:
        # Default: do both
        print("Step 1: Extracting claims from transcript...")
        transcript_file = "transcript.txt"
        claims = extract_claims(transcript_file)
        
        with open("claims.json", 'w', encoding='utf-8') as f:
            json.dump(claims, f, indent=2, ensure_ascii=False)
        print(f"✓ Extracted {len(claims)} claims\n")
        
        print("Step 2: Fact-checking all claims...")
        fact_check_all_claims()
