# Model Configuration
# Change these settings to switch between different LLM providers

# Provider options: "groq" or "huggingface"
LLM_PROVIDER = "groq"

# Model configurations for each provider
GROQ_MODELS = {
    "qwen": "qwen/qwen3-32b",
    "llama": "llama-3.3-70b-versatile",
    "mixtral": "mixtral-8x7b-32768",
    "gemma": "gemma2-9b-it"
}

HUGGINGFACE_MODELS = {
    "qwen": "Qwen/Qwen2.5-72B-Instruct",
    "llama": "meta-llama/Llama-3.1-70B-Instruct",
    "mistral": "mistralai/Mistral-7B-Instruct-v0.3"
}

# Select the active model (change this to switch models)
ACTIVE_MODEL = "qwen"  # Options: "qwen", "llama", "mixtral", "gemma" (for Groq) or "qwen", "llama", "mistral" (for HuggingFace)

# HuggingFace specific settings
HUGGINGFACE_API_KEY = None  # Will be loaded from .env
HUGGINGFACE_ENDPOINT = None  # Optional: custom inference endpoint

# Token limits for different models (approximate)
TOKEN_LIMITS = {
    "qwen/qwen3-32b": 6000,
    "llama-3.3-70b-versatile": 8000,
    "mixtral-8x7b-32768": 32000,
    "gemma2-9b-it": 8000,
    "Qwen/Qwen2.5-72B-Instruct": 32000,
    "meta-llama/Llama-3.1-70B-Instruct": 8000,
    "mistralai/Mistral-7B-Instruct-v0.3": 8000
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
