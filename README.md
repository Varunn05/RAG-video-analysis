# YouTube Fact-Checker Bot

A Python-based tool that extracts claims from YouTube video transcripts and fact-checks them using AI and web search.

## Features

- **Claim Extraction**: Automatically extracts factual claims from video transcripts with timestamps
- **Three-Phase Fact-Checking**:
  1. **Researcher**: Searches the web for evidence using Tavily
  2. **Judge**: Analyzes claims against evidence using Groq LLM
  3. **Packager**: Generates structured fact-check reports
- **Interactive UI**: Streamlit dashboard with video sync, filters, and visual analytics

## Setup
ī
1. Install dependencies:
```bash
pip install python-dotenv langchain-groq langchain-huggingface tavily-python streamlit plotly youtube-transcript-api
```

2. Create a `.env` file with your API keys:
```
GROQ_API_KEY=your_groq_api_key_here
TAVILY_API_KEY=your_tavily_api_key_here
HUGGINGFACE_API_KEY=your_huggingface_api_key_here  # Optional, only if using HuggingFace
```

3. Configure your LLM model in `model_config.py`:
```python
# Choose provider: "groq" or "huggingface"
LLM_PROVIDER = "groq"

# Choose model: "qwen", "llama", "mixtral", etc.
ACTIVE_MODEL = "qwen"
```

## Usage

### Interactive UI (Recommended)

Launch the Streamlit dashboard:
```bash
streamlit run ui.py
```

Then open your browser to `http://localhost:8501`

**Features:**
- 📺 **Video Player**: Embedded YouTube player with timestamp sync
- 📊 **Truthometer**: Visual gauge showing overall trust score (0-100)
- 🔍 **Filter Pills**: Filter claims by status (All/True/False/Misleading/Unverifiable)
- 🎯 **Interactive Claim Cards**: 
  - Click "▶ Jump" to seek video to exact timestamp
  - Click "📂 View Evidence" to see sources and explanations
- 📈 **Summary Statistics**: Real-time stats on claim verdicts

### Command Line Interface

#### Extract Claims Only
```bash
python main.py extract
```
This will:
- Read `transcript.txt`
- Extract claims with timestamps
- Save to `claims.json`

#### Fact-Check Existing Claims
```bash
python main.py factcheck
```
This will:
- Read claims from `claims.json`
- Fact-check each claim
- Generate `fact_checked_report.json`

#### Full Pipeline (Extract + Fact-Check)
```bash
python main.py
```
This runs both steps automatically.

## Output Format

### claims.json
```json
[
  {
    "time": "0.13s",
    "claim": "Python was created in 1991"
  }
]
```

### fact_checked_report.json
```json
{
  "summary": {
    "total_claims": 10,
    "true": 5,
    "false": 1,
    "misleading": 2,
    "unverifiable": 2,
    "errors": 0
  },
  "claims": [
    {
      "timestamp": "0.13s",
      "claim": "Python was created in 1991",
      "status": "TRUE",
      "explanation": "Multiple sources confirm Python was released in 1991 by Guido van Rossum.",
      "confidence": "HIGH",
      "source_url": "https://wikipedia.org/...",
      "sources": [...]
    }
  ]
}
```

## Verdict Types

- **TRUE**: Evidence clearly supports the claim
- **FALSE**: Evidence clearly contradicts the claim
- **MISLEADING**: Claim is partially true but missing context
- **UNVERIFIABLE**: Insufficient evidence to make a determination
- **ERROR**: Technical error during fact-checking

## Files

- `ui.py` - Interactive Streamlit dashboard (includes UI helpers)
- `main.py` - Main script for claim extraction and orchestration
- `fact_checker.py` - Three-phase fact-checking system
- `model_config.py` - LLM configuration and utilities
- `transcript.txt` - Input transcript file
- `claims.json` - Extracted claims
- `fact_checked_report.json` - Final fact-check report

## How It Works

1. **Transcript Fetching**: Enter a YouTube URL in the UI, and it fetches the transcript
2. **Claim Extraction**: LLM analyzes the transcript and extracts factual claims with timestamps
3. **Fact-Checking Pipeline**:
   - **Researcher**: Tavily searches the web for evidence
   - **Judge**: Groq LLM compares claim against evidence
   - **Packager**: Structures the verdict with sources
4. **Interactive Display**: View results in the dashboard with video sync and filters

