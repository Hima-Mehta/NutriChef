"""
agent.py — NutriChef Generator (RAG Pipeline)
-----------------------------------------------
This is the Generator layer of the RAG pipeline.

RAG Component Map:
  knowledge_base.json  → [Knowledge Base]
  rag._chunk()         → [Chunking]
  rag.HFEmbedding      → [Embedding Model]
  rag.ChromaDB         → [Vector Store]
  rag.retrieve()       → [Retriever]
  rag.build_context_blocks() → [Context Formatter + Prompt Caching]
  agent.run()          → [Generator]  ← THIS FILE

Responsibilities:
  1. Accept user message + condition + cuisine + history from app.py
  2. Call rag.build_context_blocks() to get cached + dynamic context
  3. Build the full message payload for Claude API
  4. Call Claude API with prompt caching
  5. Parse and return the structured response
  6. Maintain conversation memory across turns

Prompt Caching:
  System prompt         → cache_control: ephemeral (cached)
  Condition rules       → cache_control: ephemeral (cached, from rag.py)
  Cuisine profile       → cache_control: ephemeral (cached, from rag.py)
  Retrieved RAG chunks  → no cache (dynamic, changes per query)
  User message          → no cache (dynamic)
  Conversation history  → no cache (grows each turn)
"""

import os
import json
import re
from pathlib import Path
from dotenv import load_dotenv
from anthropic import Anthropic
from src.rag import build_context_blocks, init_rag

# ── Load secrets ─────────────────────────────────────────────────────────────
# Priority order:
#   1. Streamlit Cloud secrets  (st.secrets) — production
#   2. .env file                (dotenv)     — local dev
#   3. os.environ               (fallback)   — devcontainer / CI

def _load_secrets():
    """Load secrets from Streamlit Cloud or .env file."""
    # Try Streamlit secrets first (Streamlit Cloud sets these)
    try:
        import streamlit as st
        for key in ["ANTHROPIC_API_KEY", "ANTHROPIC_WORKSPACE_ID"]:
            if key in st.secrets:
                os.environ[key] = st.secrets[key]
        return
    except Exception:
        pass

    # Fallback to .env for local dev / devcontainer
    load_dotenv(Path(__file__).resolve().parent.parent / ".env")

_load_secrets()

# ── Opik observability (optional) ─────────────────────────────────────────────
try:
    from opik.integrations.anthropic import track_anthropic
    _OPIK_AVAILABLE = True
except ImportError:
    _OPIK_AVAILABLE = False

# ── Anthropic client ──────────────────────────────────────────────────────────
def _make_client() -> Anthropic:
    api_key      = os.environ.get("ANTHROPIC_API_KEY")
    workspace_id = os.environ.get("ANTHROPIC_WORKSPACE_ID")

    if not api_key:
        raise ValueError(
            "ANTHROPIC_API_KEY not found. "
            "Add it to Streamlit secrets or your .env file."
        )

    default_headers = {}
    if workspace_id:
        default_headers["anthropic-workspace-id"] = workspace_id

    client = Anthropic(
        api_key         = api_key,
        default_headers = default_headers if default_headers else None
    )
    if _OPIK_AVAILABLE:
        client = track_anthropic(client)
        print("✅ Opik observability enabled")
    return client

client = _make_client()

# ── Session-level cumulative tracking — resets on process restart ─────────────
_session = {
    "requests":           0,
    "tokens_input":       0,
    "tokens_output":      0,
    "tokens_cache_write": 0,
    "tokens_cache_read":  0,
    "tokens_total":       0,
    "cost_total":         0.0,
    "savings_total":      0.0,
}

# ── Pricing — claude-sonnet-4-6 (per 1M tokens) ──────────────────────────────
MODEL_NAME          = "claude-sonnet-4-6"
PRICE_INPUT         = 3.00   # $/1M input tokens
PRICE_OUTPUT        = 15.00  # $/1M output tokens
PRICE_CACHE_WRITE   = 3.75   # $/1M cache write tokens (first time, 25% more)
PRICE_CACHE_READ    = 0.30   # $/1M cache read tokens  (90% cheaper than input)

def calculate_cost(usage) -> dict:
    """
    Calculate exact cost from Anthropic usage object.
    Returns breakdown in USD with 6 decimal places for accuracy.
    """
    input_tokens       = getattr(usage, "input_tokens",             0)
    output_tokens      = getattr(usage, "output_tokens",            0)
    cache_write_tokens = getattr(usage, "cache_creation_input_tokens", 0)
    cache_read_tokens  = getattr(usage, "cache_read_input_tokens",  0)

    # Tokens actually billed at full input rate =
    # total input minus cache writes (billed separately) minus cache reads
    billed_input = max(0, input_tokens - cache_write_tokens - cache_read_tokens)

    cost_input       = (billed_input       / 1_000_000) * PRICE_INPUT
    cost_output      = (output_tokens      / 1_000_000) * PRICE_OUTPUT
    cost_cache_write = (cache_write_tokens / 1_000_000) * PRICE_CACHE_WRITE
    cost_cache_read  = (cache_read_tokens  / 1_000_000) * PRICE_CACHE_READ
    total_cost       = cost_input + cost_output + cost_cache_write + cost_cache_read

    # What it would have cost WITHOUT caching
    cost_without_cache = ((input_tokens + cache_write_tokens) / 1_000_000) * PRICE_INPUT                        + (output_tokens / 1_000_000) * PRICE_OUTPUT
    savings = max(0, cost_without_cache - total_cost)

    return {
        "model":              MODEL_NAME,
        "tokens_input":       input_tokens,
        "tokens_output":      output_tokens,
        "tokens_cache_write": cache_write_tokens,
        "tokens_cache_read":  cache_read_tokens,
        "tokens_total":       input_tokens + output_tokens,
        "cost_input":         round(cost_input,       6),
        "cost_output":        round(cost_output,      6),
        "cost_cache_write":   round(cost_cache_write, 6),
        "cost_cache_read":    round(cost_cache_read,  6),
        "cost_total":         round(total_cost,       6),
        "cost_without_cache": round(cost_without_cache, 6),
        "savings":            round(savings,           6),
        "cache_hit":          cache_read_tokens > 0,
    }


# ── System prompt — CACHED ────────────────────────────────────────────────────
SYSTEM_PROMPT = """
You are NutriChef — a condition-aware Indian vegetarian recipe assistant.

Your job:
- Generate healthy, personalised recipes for Indian vegetarian households
- Every response must respect the user's health condition rules provided in context
- Stay rooted in the Indian kitchen — use ingredients people actually have
- Never recommend quinoa, kale, or Western superfoods unless specifically asked
- Always explain WHY each swap is made — educate, don't just instruct

IMPORTANT: You must ALWAYS respond in valid JSON format.
Do NOT wrap in markdown code fences. Do NOT add ```json or ```. Do NOT add any text before or after.
Return ONLY the raw JSON object, nothing else. Start your response with { and end with }.
Return exactly this structure:

{
  "recipe_name": "string",
  "description": "1-2 lines on why this works for the condition",
  "ingredients": ["ingredient 1", "ingredient 2", "..."],
  "steps": ["Step 1: ...", "Step 2: ...", "..."],
  "nutrition": {
    "calories": 320,
    "protein_g": 18,
    "fat_g": 8,
    "carbs_g": 34
  },
  "health_score": 8,
  "health_score_reason": "1 line explaining the score",
  "why_it_works": "2-3 lines explaining nutritional logic for the condition",
  "swap_tip": "one practical swap if missing an ingredient",
  "mode": "fridge | transform | label | general"
}

Health score rules (score out of 10):
- 9-10: Perfectly aligned with condition, all ingredients therapeutic
- 7-8:  Well aligned, minor compromises
- 5-6:  Moderate — some condition-friendly choices, room to improve
- 3-4:  Weak alignment — acceptable but not ideal for the condition
- 1-2:  Poor fit — use only if no alternatives exist

For label reading requests, return:
{
  "recipe_name": "Label Analysis",
  "description": "plain English summary of what this label means",
  "ingredients": ["claim 1", "claim 2", "..."],
  "steps": ["What to watch: ...", "Red flag: ...", "..."],
  "nutrition": { "calories": 0, "protein_g": 0, "fat_g": 0, "carbs_g": 0 },
  "health_score": 5,
  "health_score_reason": "Overall verdict on this product",
  "why_it_works": "Bottom line recommendation",
  "swap_tip": "Better alternative to this product",
  "mode": "label"
}

Rules:
- ALWAYS return valid JSON — never plain text
- Never use medical language or make diagnostic claims
- Keep the tone warm and encouraging
- If no condition mentioned, apply general healthy eating principles
""".strip()


# ── Mode detection ─────────────────────────────────────────────────────────────
def _detect_mode(message: str) -> str:
    """
    Detect what kind of request this is.
    Returns: 'fridge' | 'transform' | 'label' | 'general'
    """
    msg = message.lower()

    label_keywords = ["label", "nutrition facts", "packaged", "ingredients list",
                      "what does this mean", "how to read"]
    fridge_keywords = ["i have", "in my fridge", "available", "using what",
                       "make something with", "what can i make"]
    transform_keywords = ["make", "healthier", "healthy version", "transform",
                          "substitute", "replace", "convert"]

    if any(k in msg for k in label_keywords):
        return "label"
    if any(k in msg for k in fridge_keywords):
        return "fridge"
    if any(k in msg for k in transform_keywords):
        return "transform"
    return "general"


def _get_category_filter(mode: str) -> str | None:
    """Map mode to RAG category filter for more precise retrieval."""
    return {
        "fridge":    "ingredient",
        "transform": "swap",
        "label":     "label_reading",
        "general":   None
    }.get(mode)


# ── Memory helpers ─────────────────────────────────────────────────────────────
def build_history(messages: list[dict]) -> list[dict]:
    """
    Convert app.py message format to Anthropic API format.
    Keeps last 10 turns to avoid context window overflow.

    app.py format:   [{"role": "user"|"assistant", "content": "text"}]
    Anthropic format: same, but content must be a list of blocks
    """
    history = []
    # Keep last 10 turns (5 user + 5 assistant)
    recent = messages[-10:] if len(messages) > 10 else messages

    for msg in recent:
        history.append({
            "role": msg["role"],
            "content": [{"type": "text", "text": msg["content"]}]
        })
    return history


# ── JSON parser — robust extraction regardless of Claude's formatting ────────
def _parse_json(text: str, mode: str) -> dict:
    """
    Robustly extract JSON from Claude's response.
    Handles:
      - Clean JSON
      - JSON wrapped in ```json ... ```
      - JSON wrapped in ``` ... ```
      - JSON embedded in surrounding text
    """
    # Strategy 1: direct parse
    try:
        return json.loads(text.strip())
    except json.JSONDecodeError:
        pass

    # Strategy 2: extract from markdown code fences using regex
    # Matches ```json { ... } ``` or ``` { ... } ```
    fence_match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    if fence_match:
        try:
            return json.loads(fence_match.group(1))
        except json.JSONDecodeError:
            pass

    # Strategy 3: find first { ... } block in the response
    brace_match = re.search(r"\{.*\}", text, re.DOTALL)
    if brace_match:
        try:
            return json.loads(brace_match.group())
        except json.JSONDecodeError:
            pass

    # Strategy 4: fallback — wrap raw text so UI still renders something
    return {
        "recipe_name":         "NutriChef Suggestion",
        "description":         text[:300],
        "ingredients":         [],
        "steps":               [text],
        "nutrition":           {"calories": 0, "protein_g": 0, "fat_g": 0, "carbs_g": 0},
        "health_score":        7,
        "health_score_reason": "Parsing error — raw response shown",
        "why_it_works":        "",
        "swap_tip":            "",
        "mode":                mode
    }


# ── Main run function — called by app.py ──────────────────────────────────────
def run(
    message:   str,
    condition: str,
    cuisine:   str | None  = None,
    history:   list[dict]  = None
) -> dict:
    """
    Main entry point — called by app.py on every user message.

    Args:
        message:   User's input text
        condition: Health condition key e.g. "diabetes", "pcos", "general_wellbeing"
        cuisine:   Cuisine preference e.g. "north_indian", "south_indian"
        history:   List of previous messages [{"role": ..., "content": ...}]

    Returns:
        {
            "response":  str,   ← the recipe / answer text
            "mode":      str,   ← detected mode (fridge/transform/label/general)
            "cached":    bool,  ← whether context was served from cache
            "tokens_in": int,   ← input tokens used
            "tokens_out": int   ← output tokens used
        }
    """
    if history is None:
        history = []

    # ── Step 1: Detect mode ──────────────────────────────────────────────────
    mode            = _detect_mode(message)
    category_filter = _get_category_filter(mode)

    # ── Step 2: RAG retrieval + context formatting ───────────────────────────
    # Returns [condition_block(cached), cuisine_block(cached), rag_block(dynamic)]
    context_blocks = build_context_blocks(
        query           = message,
        condition       = condition,
        cuisine         = cuisine,
        category_filter = category_filter,
        top_k           = 5
    )

    # ── Step 3: Build conversation history ──────────────────────────────────
    api_history = build_history(history)

    # ── Step 4: Build current user message ──────────────────────────────────
    # Order matters for caching:
    # cached blocks first, then dynamic content, then user message
    current_message = {
        "role": "user",
        "content": context_blocks + [{"type": "text", "text": message}]
    }

    # ── Step 5: Call Claude API ──────────────────────────────────────────────
    response = client.messages.create(
        model      = "claude-sonnet-4-6",
        max_tokens = 2048,
        system     = [
            {
                "type": "text",
                "text": SYSTEM_PROMPT,
                "cache_control": {"type": "ephemeral"}   # ← system prompt cached
            }
        ],
        messages = api_history + [current_message]
    )

    # ── Step 6: Parse response ───────────────────────────────────────────────
    response_text = response.content[0].text
    usage         = response.usage
    cache_hit     = getattr(usage, "cache_read_input_tokens", 0) > 0

    # ── Parse structured JSON from Claude ──────────────────────────────────────
    # Claude sometimes wraps JSON in ```json ... ``` markdown fences
    # Use regex to extract the JSON object reliably regardless of wrapping
    structured = _parse_json(response_text, mode)

    cost = calculate_cost(usage)

    # ── Update cumulative session totals ────────────────────────────────────
    _session["requests"]           += 1
    _session["tokens_input"]       += cost["tokens_input"]
    _session["tokens_output"]      += cost["tokens_output"]
    _session["tokens_cache_write"] += cost["tokens_cache_write"]
    _session["tokens_cache_read"]  += cost["tokens_cache_read"]
    _session["tokens_total"]       += cost["tokens_total"]
    _session["cost_total"]         += cost["cost_total"]
    _session["savings_total"]      += cost["savings"]

    # ── Backend cost logging — visible in terminal, never in UI ──────────────
    cache_status = "⚡ CACHE HIT" if cost["cache_hit"] else "  cache miss"
    print(f"\n{'─'*55}")
    print(f"  NutriChef · Request #{_session['requests']}")
    print(f"{'─'*55}")
    print(f"  Model      : {cost['model']}")
    print(f"  Mode       : {mode}")
    print(f"  Condition  : {condition}")
    print(f"  Cache      : {cache_status}")
    print(f"{'─'*55}")
    print(f"  This request")
    print(f"    Input        : {cost['tokens_input']:>8,}")
    print(f"    Output       : {cost['tokens_output']:>8,}")
    if cost['tokens_cache_write']:
        print(f"    Cache write  : {cost['tokens_cache_write']:>8,}")
    if cost['tokens_cache_read']:
        print(f"    Cache read   : {cost['tokens_cache_read']:>8,}")
    print(f"    Total tokens : {cost['tokens_total']:>8,}")
    print(f"    Cost         : ${cost['cost_total']:.6f}")
    if cost['savings'] > 0:
        print(f"    Saved        : ${cost['savings']:.6f}  (vs no cache)")
    print(f"{'─'*55}")
    print(f"  Session cumulative  (requests: {_session['requests']})")
    print(f"    Total tokens : {_session['tokens_total']:>8,}")
    print(f"    Total cost   : ${_session['cost_total']:.6f}")
    print(f"    Total saved  : ${_session['savings_total']:.6f}")
    print(f"{'─'*55}\n")

    return {
        "structured": structured,    # ← parsed JSON for visual rendering
        "response":   response_text, # ← raw text (fallback)
        "mode":       mode,
        "cost":       cost,          # ← available if needed elsewhere
    }


# ── Initialise RAG on import ──────────────────────────────────────────────────
# This runs once when agent.py is first imported by app.py
# Builds ChromaDB index if not already built, skips if hash unchanged
init_rag()


# ── Quick test ────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("Testing NutriChef agent...\n")

    test_cases = [
        {
            "message":   "I have spinach, moong dal, garlic and ragi flour. What can I make?",
            "condition": "pcos",
            "cuisine":   "south_indian"
        },
        {
            "message":   "Make dal makhani healthier",
            "condition": "diabetes",
            "cuisine":   "north_indian"
        },
        {
            "message":   "What does high sodium on a label mean?",
            "condition": "hypertension",
            "cuisine":   None
        }
    ]

    for i, test in enumerate(test_cases):
        print(f"--- Test {i+1}: {test['message'][:50]}...")
        print(f"    Condition: {test['condition']} | Mode: {_detect_mode(test['message'])}")
        print(f"    Category filter: {_get_category_filter(_detect_mode(test['message']))}")

        context = build_context_blocks(
            query           = test["message"],
            condition       = test["condition"],
            cuisine         = test.get("cuisine"),
            category_filter = _get_category_filter(_detect_mode(test["message"]))
        )
        print(f"    Context blocks: {len(context)} "
              f"({sum(1 for b in context if 'cache_control' in b)} cached, "
              f"{sum(1 for b in context if 'cache_control' not in b)} dynamic)")
        print()