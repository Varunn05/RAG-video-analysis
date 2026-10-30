# Model Configuration
# Change these settings to switch between different LLM providers

# Provider options: "groq" or "huggingface". Both use GPT-OSS 120B.
LLM_PROVIDER = "groq"

# Model configurations for each provider
GROQ_MODELS = {
    "gpt_oss": "openai/gpt-oss-120b",
}

HUGGINGFACE_MODELS = {
    "gpt_oss": "openai/gpt-oss-120b",
}

# The model used by every legacy CLI/Streamlit provider configuration.
ACTIVE_MODEL = "gpt_oss"

# HuggingFace specific settings
HUGGINGFACE_API_KEY = None  # Will be loaded from .env
HUGGINGFACE_ENDPOINT = None  # Optional: custom inference endpoint

# Token limit for GPT-OSS 120B (approximate).
TOKEN_LIMITS = {
    "openai/gpt-oss-120b": 120000,
}


# ============================================================================
# LLM Utility Functions (merged from llm_utils.py)
# ============================================================================

import os
from dotenv import load_dotenv

load_dotenv()


def get_llm_client():
    """
    Get the appropriate LLM client based on configuration.
    
    Returns:
        LLM client instance (ChatGroq or HuggingFaceHub)
    """
    if LLM_PROVIDER == "groq":
        from langchain_groq import ChatGroq
        model_name = GROQ_MODELS.get(ACTIVE_MODEL)
        if not model_name:
            raise ValueError(f"Model '{ACTIVE_MODEL}' not found in GROQ_MODELS")
        
        return ChatGroq(
            model=model_name,
            api_key=os.environ.get("GROQ_API_KEY")
        )
    
    elif LLM_PROVIDER == "huggingface":
        from langchain_huggingface import HuggingFaceEndpoint
        model_name = HUGGINGFACE_MODELS.get(ACTIVE_MODEL)
        if not model_name:
            raise ValueError(f"Model '{ACTIVE_MODEL}' not found in HUGGINGFACE_MODELS")
        
        return HuggingFaceEndpoint(
            repo_id=model_name,
            huggingfacehub_api_token=os.environ.get("HUGGINGFACE_API_KEY"),
            temperature=0.7,
            max_new_tokens=2048
        )
    
    else:
        raise ValueError(f"Unknown LLM_PROVIDER: {LLM_PROVIDER}. Must be 'groq' or 'huggingface'")


def get_current_model_name():
    """Get the current model name being used"""
    if LLM_PROVIDER == "groq":
        return GROQ_MODELS.get(ACTIVE_MODEL, "unknown")
    elif LLM_PROVIDER == "huggingface":
        return HUGGINGFACE_MODELS.get(ACTIVE_MODEL, "unknown")
    return "unknown"


def get_token_limit():
    """Get the token limit for the current model"""
    model_name = get_current_model_name()
    return TOKEN_LIMITS.get(model_name, 6000)  # Default to 6000 if not found


def get_max_chunk_chars():
    """
    Calculate maximum characters per chunk based on token limit.
    Conservative estimate: 1 token ≈ 4 characters
    Reserve space for prompt overhead
    """
    token_limit = get_token_limit()
    # Use 60% of token limit for transcript, rest for prompt
    usable_tokens = int(token_limit * 0.6)
    return usable_tokens * 4  # Convert to characters
