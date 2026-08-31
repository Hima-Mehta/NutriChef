"""
rag.py — NutriChef Retrieval Layer
-----------------------------------
Responsibilities:
  1. Load and parse knowledge_base.json
  2. Chunk and index all entries into ChromaDB
  3. Retrieve condition-filtered context for any query
  4. Format retrieved context as Anthropic cache_control blocks
     ready to be dropped into agent API calls

Prompt caching strategy:
  - Condition rules + ingredient data are static per condition
    -> marked with cache_control: ephemeral
  - Query-specific retrieved chunks are dynamic
    -> passed as normal (uncached) content

Embedding:
  - Primary: HuggingFace sentence-transformers/all-MiniLM-L6-v2
      * 384-dim dense embeddings, real semantic understanding
      * Understands "what can I eat instead of rice" -> matches millet swaps
      * Free, open source, no API key needed
      * ~80MB model, downloaded once, cached locally
  - Fallback: TF-IDF (keyword matching, offline, zero dependencies)
      * Activated automatically if sentence-transformers unavailable
"""

import json
import os
import hashlib
import numpy as np
from pathlib import Path
from typing import Optional

import chromadb
from chromadb.config import Settings
from chromadb import EmbeddingFunction, Documents, Embeddings
from sklearn.feature_extraction.text import TfidfVectorizer

try:
    from sentence_transformers import SentenceTransformer
    _HF_AVAILABLE = True
except ImportError:
    _HF_AVAILABLE = False


# ── Paths ─────────────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent.parent
KB_PATH  = BASE_DIR / "data" / "knowledge_base.json"
DB_PATH  = BASE_DIR / "data" / "chroma_db"


# ══════════════════════════════════════════════════════════════════════════════
# EMBEDDING FUNCTION
# ══════════════════════════════════════════════════════════════════════════════

HF_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"


class HuggingFaceEmbeddingFunction(EmbeddingFunction):
    """
    Primary embedding — HuggingFace sentence-transformers.

    Model: all-MiniLM-L6-v2
      - 384-dimensional dense vectors
      - Trained for semantic similarity tasks
      - Understands meaning, not just keyword overlap
      - Example: "substitute for white rice" matches "foxtail millet swap"
                  even with zero shared words
      - ~80MB, downloaded once to ~/.cache/huggingface/, reused forever
      - No API key, completely free, runs locally

    Why this model:
      - Best balance of speed vs quality for RAG use cases
      - Standard benchmark model for semantic search
      - Works well on nutrition/food domain out of the box
      - Fast enough for real-time retrieval (< 50ms per query)
    """
    def __init__(self, model_name: str = HF_MODEL_NAME):
        print(f"Loading HuggingFace embedding model: {model_name}")
        self._model = SentenceTransformer(model_name)
        print(f"✅ Embedding model loaded — dim: {self._model.get_sentence_embedding_dimension()}")

    def __call__(self, input: Documents) -> Embeddings:
        embeddings = self._model.encode(
            list(input),
            normalize_embeddings=True,   # L2 normalised for cosine similarity
            show_progress_bar=False
        )
        return embeddings.tolist()


class TfidfEmbeddingFunction(EmbeddingFunction):
    """
    Fallback embedding — TF-IDF keyword matching.
    Used only when sentence-transformers is not installed.
    Works offline, no downloads, but misses semantic relationships.
    Install sentence-transformers to upgrade: pip install sentence-transformers
    """
    def __init__(self, max_features: int = 512):
        self._vectorizer = TfidfVectorizer(
            max_features=max_features,
            ngram_range=(1, 2),
            strip_accents="unicode",
            lowercase=True
        )
        self._fitted = False

    def _fit_on_corpus(self, documents: list[str]):
        self._vectorizer.fit(documents)
        self._fitted = True

    def __call__(self, input: Documents) -> Embeddings:
        docs = list(input)
        if not self._fitted:
            self._fit_on_corpus(docs)
        vectors = self._vectorizer.transform(docs).toarray()
        norms = np.linalg.norm(vectors, axis=1, keepdims=True)
        norms[norms == 0] = 1
        return (vectors / norms).tolist()


def _make_embedding_fn() -> EmbeddingFunction:
    if _HF_AVAILABLE:
        try:
            return HuggingFaceEmbeddingFunction()
        except Exception as e:
            print(f"⚠️  HuggingFace model unavailable ({e.__class__.__name__}) — falling back to TF-IDF.")
            print("   On your machine: pip install sentence-transformers (model downloads automatically)")
            return TfidfEmbeddingFunction()
    else:
        print("⚠️  sentence-transformers not installed — falling back to TF-IDF.")
        print("   Install with: pip install sentence-transformers")
        return TfidfEmbeddingFunction()


_embedding_fn = _make_embedding_fn()


# ── ChromaDB client (persistent) ──────────────────────────────────────────────
_client = chromadb.PersistentClient(
    path=str(DB_PATH),
    settings=Settings(anonymized_telemetry=False)
)


# ══════════════════════════════════════════════════════════════════════════════
# 1. KNOWLEDGE BASE LOADER
# ══════════════════════════════════════════════════════════════════════════════

def load_knowledge_base() -> dict:
    """Load and return the full knowledge base as a dict."""
    if not KB_PATH.exists():
        raise FileNotFoundError(f"Knowledge base not found at {KB_PATH}")
    with open(KB_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


# ══════════════════════════════════════════════════════════════════════════════
# 2. CHUNKING — flatten KB into indexable documents
# ══════════════════════════════════════════════════════════════════════════════

def _chunk_knowledge_base(kb: dict) -> list[dict]:
    """
    Flatten the nested knowledge base into a list of chunks.
    Each chunk: { id, text, metadata }
    """
    chunks = []

    # ── Condition rules ──
    for condition_key, condition_data in kb.get("conditions", {}).items():
        label = condition_data.get("label", condition_key)

        chunks.append({
            "id":   f"condition_{condition_key}_principle",
            "text": f"{label} core principle: {condition_data.get('core_principle', '')}",
            "metadata": {"condition": condition_key, "category": "condition_rule", "type": "principle"}
        })

        rules = condition_data.get("dietary_rules", {})
        avoid_text = ", ".join(rules.get("avoid", []))
        if avoid_text:
            chunks.append({
                "id":   f"condition_{condition_key}_avoid",
                "text": f"{label} foods to avoid: {avoid_text}",
                "metadata": {"condition": condition_key, "category": "condition_rule", "type": "avoid"}
            })

        prefer_text = ", ".join(rules.get("prefer", []))
        if prefer_text:
            chunks.append({
                "id":   f"condition_{condition_key}_prefer",
                "text": f"{label} foods to prefer: {prefer_text}",
                "metadata": {"condition": condition_key, "category": "condition_rule", "type": "prefer"}
            })

        if rules.get("portion_guidance"):
            chunks.append({
                "id":   f"condition_{condition_key}_portion",
                "text": f"{label} portion guidance: {rules['portion_guidance']}",
                "metadata": {"condition": condition_key, "category": "condition_rule", "type": "portion"}
            })

        if rules.get("meal_timing"):
            chunks.append({
                "id":   f"condition_{condition_key}_timing",
                "text": f"{label} meal timing: {rules['meal_timing']}",
                "metadata": {"condition": condition_key, "category": "condition_rule", "type": "timing"}
            })

        for i, swap in enumerate(condition_data.get("condition_specific_swaps", [])):
            chunks.append({
                "id":   f"condition_{condition_key}_swap_{i}",
                "text": f"{label} swap: replace {swap['from']} with {swap['to']}. Reason: {swap['reason']}",
                "metadata": {"condition": condition_key, "category": "swap", "type": "condition_swap"}
            })

        superfoods = ", ".join(condition_data.get("superfoods", []))
        if superfoods:
            chunks.append({
                "id":   f"condition_{condition_key}_superfoods",
                "text": f"{label} superfoods: {superfoods}",
                "metadata": {"condition": condition_key, "category": "condition_rule", "type": "superfoods"}
            })

        # Label reading tips (general_wellbeing)
        for i, tip in enumerate(condition_data.get("label_reading_focus", {}).get("what_to_check", [])):
            chunks.append({
                "id":   f"condition_{condition_key}_label_tip_{i}",
                "text": f"Nutrition label reading: {tip}",
                "metadata": {"condition": condition_key, "category": "label_reading", "type": "label_tip"}
            })
        for i, flag in enumerate(condition_data.get("label_reading_focus", {}).get("red_flags_in_indian_packaged_foods", [])):
            chunks.append({
                "id":   f"condition_{condition_key}_label_flag_{i}",
                "text": f"Indian packaged food red flag: {flag}",
                "metadata": {"condition": condition_key, "category": "label_reading", "type": "red_flag"}
            })

    # ── Global ingredient swaps ──
    for i, swap in enumerate(kb.get("ingredient_swaps", [])):
        conditions_str = ", ".join(swap.get("conditions", []))
        chunks.append({
            "id":   f"global_swap_{i}",
            "text": (
                f"Swap: replace {swap['from']} with {swap['to']} "
                f"(ratio {swap.get('ratio', '1:1')}). "
                f"Benefit: {swap['benefit']}. For: {conditions_str}"
            ),
            "metadata": {"condition": "all", "category": "swap", "type": "global_swap"}
        })

    # ── Ingredients ──
    for category, items in kb.get("ingredients", {}).items():
        for item in items:
            parts = [f"Ingredient: {item['name']} ({category})."]
            if item.get("benefits"):
                parts.append(f"Benefits: {', '.join(item['benefits'])}.")
            if item.get("conditions_good_for"):
                parts.append(f"Good for: {', '.join(item['conditions_good_for'])}.")
            if item.get("conditions_caution"):
                parts.append(f"Caution for: {', '.join(item['conditions_caution'])}.")
            if item.get("gi"):
                parts.append(f"GI: {item['gi']}.")
            if item.get("protein_per_100g"):
                parts.append(f"Protein: {item['protein_per_100g']}g/100g.")
            if item.get("notes"):
                parts.append(f"Notes: {item['notes']}.")

            safe_name = item['name'].replace(' ', '_').replace('/', '_').replace('(', '').replace(')', '')
            chunks.append({
                "id":   f"ingredient_{category}_{safe_name}",
                "text": " ".join(parts),
                "metadata": {
                    "condition": ", ".join(item.get("conditions_good_for", ["all"])) or "all",
                    "category":  "ingredient",
                    "type":      category,
                    "name":      item["name"]
                }
            })

    # ── Cuisine profiles ──
    for cuisine_key, cd in kb.get("cuisine_profiles", {}).items():
        chunks.append({
            "id":   f"cuisine_{cuisine_key}",
            "text": (
                f"{cuisine_key.replace('_', ' ').title()} cuisine. "
                f"Staples: {', '.join(cd.get('staples', []))}. "
                f"Common issues: {', '.join(cd.get('typical_issues', []))}. "
                f"Healthy defaults: {', '.join(cd.get('healthy_defaults', []))}. "
                f"Signature dishes: {', '.join(cd.get('signature_healthy_dishes', []))}."
            ),
            "metadata": {"condition": "all", "category": "cuisine", "type": cuisine_key}
        })

    # ── Cooking methods ──
    for i, method in enumerate(kb.get("cooking_methods", [])):
        chunks.append({
            "id":   f"cooking_method_{i}",
            "text": (
                f"Cooking method: {method['method']}. "
                f"Benefit: {method['benefit']}. "
                f"Best for: {', '.join(method.get('preferred_for', []))}. "
                f"Healthier than: {method.get('vs', '')}."
            ),
            "metadata": {"condition": "all", "category": "cooking_method", "type": "method"}
        })

    return chunks


# ══════════════════════════════════════════════════════════════════════════════
# 3. INDEX — build or load ChromaDB collection
# ══════════════════════════════════════════════════════════════════════════════

def _get_collection():
    return _client.get_or_create_collection(
        name="nutrichef_knowledge",
        embedding_function=_embedding_fn,
        metadata={"hnsw:space": "cosine"}
    )


def build_index(force_rebuild: bool = False) -> None:
    """Build ChromaDB index. Skips if KB hash unchanged."""
    kb = load_knowledge_base()
    kb_hash = hashlib.md5(json.dumps(kb, sort_keys=True).encode()).hexdigest()
    hash_file = DB_PATH / "kb_hash.txt"

    if not force_rebuild and hash_file.exists():
        if hash_file.read_text().strip() == kb_hash:
            print("✅ Index up to date. Skipping rebuild.")
            return

    print("🔨 Building ChromaDB index...")
    chunks = _chunk_knowledge_base(kb)

    # Fit TF-IDF on full corpus if using fallback embedding
    if isinstance(_embedding_fn, TfidfEmbeddingFunction):
        all_texts = [c["text"] for c in chunks]
        _embedding_fn._fit_on_corpus(all_texts)

    collection = _get_collection()

    # Clear existing
    try:
        existing = collection.get()
        if existing["ids"]:
            collection.delete(ids=existing["ids"])
    except Exception:
        pass

    # Batch upsert
    batch_size = 50
    for i in range(0, len(chunks), batch_size):
        batch = chunks[i:i + batch_size]
        collection.upsert(
            ids       = [c["id"]       for c in batch],
            documents = [c["text"]     for c in batch],
            metadatas = [c["metadata"] for c in batch]
        )

    DB_PATH.mkdir(parents=True, exist_ok=True)
    hash_file.write_text(kb_hash)
    print(f"✅ Indexed {len(chunks)} chunks into ChromaDB.")


# ══════════════════════════════════════════════════════════════════════════════
# 4. RETRIEVAL — condition-filtered semantic search
# ══════════════════════════════════════════════════════════════════════════════

def retrieve(
    query: str,
    condition: Optional[str] = None,
    category: Optional[str] = None,
    top_k: int = 6
) -> list[dict]:
    """
    Retrieve top-k relevant chunks for a query.
    Filters by condition and/or category when provided.
    Always includes condition="all" chunks.
    """
    collection = _get_collection()

    where = None
    if condition and category:
        where = {"$or": [
            {"$and": [{"condition": {"$eq": condition}}, {"category": {"$eq": category}}]},
            {"$and": [{"condition": {"$eq": "all"}},     {"category": {"$eq": category}}]}
        ]}
    elif condition:
        where = {"$or": [
            {"condition": {"$eq": condition}},
            {"condition": {"$eq": "all"}}
        ]}
    elif category:
        where = {"category": {"$eq": category}}

    params = {
        "query_texts": [query],
        "n_results":   top_k,
        "include":     ["documents", "metadatas", "distances"]
    }
    if where:
        params["where"] = where

    results = collection.query(**params)

    return [
        {
            "id":       results["ids"][0][i],
            "text":     results["documents"][0][i],
            "metadata": results["metadatas"][0][i],
            "distance": results["distances"][0][i]
        }
        for i, _ in enumerate(results["documents"][0])
    ]


# ══════════════════════════════════════════════════════════════════════════════
# 5. CACHE-READY CONTEXT FORMATTERS
# ══════════════════════════════════════════════════════════════════════════════

def get_condition_context_block(condition: str) -> dict:
    """
    Full condition rules as a CACHED Anthropic content block.
    Static per condition — Anthropic caches this for 5 minutes.
    Saves ~90% on input token cost for repeated requests.
    """
    kb = load_knowledge_base()
    data = kb.get("conditions", {}).get(condition, {})

    if not data:
        return {
            "type": "text",
            "text": "No specific condition. Apply general healthy eating principles.",
            "cache_control": {"type": "ephemeral"}
        }

    label  = data.get("label", condition)
    rules  = data.get("dietary_rules", {})
    avoid  = "\n".join(f"  - {x}" for x in rules.get("avoid",  []))
    prefer = "\n".join(f"  - {x}" for x in rules.get("prefer", []))
    swaps  = "\n".join(
        f"  - Replace '{s['from']}' with '{s['to']}': {s['reason']}"
        for s in data.get("condition_specific_swaps", [])
    )

    text = f"""=== CONDITION: {label.upper()} ===
Core principle: {data.get('core_principle', '')}

Avoid:
{avoid}

Prefer:
{prefer}

Portion guidance: {rules.get('portion_guidance', '')}
Meal timing: {rules.get('meal_timing', '')}

Ingredient swaps:
{swaps}

Superfoods: {', '.join(data.get('superfoods', []))}"""

    return {
        "type": "text",
        "text": text,
        "cache_control": {"type": "ephemeral"}   # ← CACHED
    }


def get_cuisine_context_block(cuisine: str) -> dict:
    """Cuisine profile as a CACHED content block."""
    kb = load_knowledge_base()
    key = cuisine.lower().replace(" ", "_")
    cd  = kb.get("cuisine_profiles", {}).get(key)

    if not cd:
        return {
            "type": "text",
            "text": f"Cuisine: {cuisine}. Apply general Indian vegetarian principles.",
            "cache_control": {"type": "ephemeral"}
        }

    text = f"""=== CUISINE: {cuisine.upper()} ===
Staples: {', '.join(cd.get('staples', []))}
Common issues: {', '.join(cd.get('typical_issues', []))}
Healthy defaults: {', '.join(cd.get('healthy_defaults', []))}
Signature healthy dishes: {', '.join(cd.get('signature_healthy_dishes', []))}"""

    return {
        "type": "text",
        "text": text,
        "cache_control": {"type": "ephemeral"}   # ← CACHED
    }


def get_retrieved_context_block(chunks: list[dict]) -> dict:
    """
    Dynamically retrieved RAG chunks as a plain content block.
    NOT cached — changes with every query.
    """
    if not chunks:
        return {"type": "text", "text": "No additional context retrieved."}

    lines = ["=== RETRIEVED CONTEXT ==="]
    for chunk in chunks:
        lines.append(f"\n[{chunk['metadata'].get('category', 'info').upper()}]")
        lines.append(chunk["text"])

    return {"type": "text", "text": "\n".join(lines)}


# ══════════════════════════════════════════════════════════════════════════════
# 6. MAIN CONTEXT BUILDER — called by agents
# ══════════════════════════════════════════════════════════════════════════════

def build_context_blocks(
    query: str,
    condition: str,
    cuisine: Optional[str] = None,
    category_filter: Optional[str] = None,
    top_k: int = 5
) -> list[dict]:
    """
    Master function — called by every agent before an API call.

    Returns ordered Anthropic content blocks:
      [0] Condition rules      ← CACHED (static per condition)
      [1] Cuisine profile      ← CACHED (static per cuisine, if provided)
      [2] RAG chunks           ← NOT CACHED (dynamic, query-specific)

    Usage in agent.py:
        context_blocks = build_context_blocks(
            query     = user_message,
            condition = "diabetes",
            cuisine   = "north_indian"
        )
        response = client.messages.create(
            model  = "claude-sonnet-4-6",
            system = [{"type": "text", "text": SYSTEM_PROMPT,
                       "cache_control": {"type": "ephemeral"}}],
            messages = [{
                "role":    "user",
                "content": context_blocks + [{"type": "text", "text": user_message}]
            }]
        )
    """
    blocks = []
    blocks.append(get_condition_context_block(condition))
    if cuisine:
        blocks.append(get_cuisine_context_block(cuisine))
    chunks = retrieve(query, condition=condition, category=category_filter, top_k=top_k)
    blocks.append(get_retrieved_context_block(chunks))
    return blocks


# ══════════════════════════════════════════════════════════════════════════════
# 7. INIT — call once at app startup
# ══════════════════════════════════════════════════════════════════════════════

def init_rag():
    """Initialise RAG — build index if needed. Call once at startup."""
    DB_PATH.mkdir(parents=True, exist_ok=True)
    build_index()


# ── Quick test ────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("Initialising NutriChef RAG...\n")
    init_rag()

    print("\n--- Test 1: retrieve swaps for diabetes ---")
    results = retrieve(
        query     = "what can I replace white rice with",
        condition = "diabetes",
        category  = "swap",
        top_k     = 3
    )
    for r in results:
        print(f"  [{r['metadata']['type']}] {r['text'][:100]}...")

    print("\n--- Test 2: retrieve ingredients for PCOS ---")
    results = retrieve(
        query     = "high protein ingredients for PCOS",
        condition = "pcos",
        category  = "ingredient",
        top_k     = 3
    )
    for r in results:
        print(f"  [{r['metadata'].get('name','?')}] {r['text'][:100]}...")

    print("\n--- Test 3: build_context_blocks for agent ---")
    blocks = build_context_blocks(
        query     = "Make a healthy South Indian breakfast for diabetes",
        condition = "diabetes",
        cuisine   = "south_indian"
    )
    print(f"\nTotal blocks returned: {len(blocks)}")
    for b in blocks:
        cached = "CACHED ✅" if "cache_control" in b else "dynamic  "
        preview = b["text"][:70].replace("\n", " ")
        print(f"  [{cached}] {preview}...")
