
# 🥗 NutriChef — Condition-Aware Healthy Recipes from Your Indian Kitchen

> No more endless YouTube rabbit holes hunting for healthy alternatives. No more staring at a half-empty fridge feeling like you're compromising on the dish you actually want. Cooking from limited ingredients isn't a constraint — it's an art. And NutriChef is your creative partner in it.

Built specifically for **Indian vegetarian households** managing lifestyle diseases — diabetes, PCOS, hypertension, high cholesterol, thyroid, obesity, or simply eating better. NutriChef gives you healthy recipes rooted in your actual kitchen, not a Western pantry.

---

## 🚀 Live Demo

🔗 [NutriChef on Streamlit Cloud](#) *(link coming soon)*  
📹 [60-second Demo](#) *(Loom link coming soon)*

---

## 🧠 What It Does

NutriChef works in two ways:

**1. Transform a dish**
Give it any recipe — `aloo paratha`, `dal makhani`, `pasta carbonara` — and it returns a healthier version with condition-aware ingredient swaps, nutrition comparison, and the science behind each change.

**2. Cook from your fridge**
Tell it what ingredients you have, what cuisine you're in the mood for, and your health condition — it builds you a complete healthy recipe from scratch, using only what's available.

In both modes, NutriChef:
- **Personalises** every recipe to your specific health condition
- **Stays rooted** in the Indian vegetarian kitchen — no quinoa or kale prescriptions
- **Remembers** your dietary needs across the entire conversation
- **Explains** the nutritional benefit of every swap
- **Teaches** you to read nutrition labels so you stop being misled by packaged food marketing

---

## 🏥 Conditions Covered

| Condition | What NutriChef does |
|---|---|
| 🩸 Diabetes | Low-GI swaps, millet over rice, karela and methi front and centre |
| 🌸 PCOS | Anti-inflammatory, insulin-sensitising, hormone-balancing foods |
| ❤️ Hypertension | Low-sodium cooking, potassium-rich ingredients, no hidden salt |
| 🫀 High Cholesterol | Soluble fibre, omega-3, eliminates trans fats and vanaspati |
| 🦋 Thyroid | Selenium and zinc focus, goitrogen guidance, medication timing |
| ⚖️ Obesity | High satiety, sustainable deficit, no crash diet framing |
| 🌿 General Wellbeing | Whole foods, balanced thali, gut health, label literacy |

---

## 💬 Example Conversations

**Condition-aware dish transformation:**
```
You:       Make dal makhani healthier. I have diabetes.

NutriChef: Here's a diabetic-friendly dal makhani —
           I've kept the whole black urad (excellent protein and fibre),
           replaced cream with hung curd (saves 380 kcal, adds probiotics),
           halved the butter and added a methi seeds tadka instead.
           Methi improves insulin sensitivity — it belongs in every
           diabetic's kitchen.

           ~290 kcal | 16g protein | 8g fat | 34g carbs per serving
           Serve with jowar roti instead of naan for a fully low-GI meal.
```

**Fridge-first with condition:**
```
You:       I have spinach, moong dal, garlic, tomatoes, and some ragi flour.
           I have PCOS. Something South Indian.

NutriChef: Perfect ingredients for a PCOS-friendly meal!
           Ragi dosa with moong dal and spinach filling —
           ragi is low-GI and calcium-rich, moong dal gives you
           plant protein, spinach adds iron and folate.
           Add a spearmint chutney — spearmint actively reduces
           androgen levels in PCOS.
```

**Snap your fridge:**
```
You:       [uploads fridge photo 📸]

NutriChef: I can see: paneer, spinach, tomatoes, dahi, ginger,
           garlic, and what looks like leftover brown rice.
           Great base! What condition are you managing,
           and what cuisine are you in the mood for?
```

**Reading a nutrition label:**
```
You:       [uploads label of a "multigrain" biscuit 🏷️]

NutriChef: Here's what this label actually means:

           • "Multigrain" but refined flour (maida) is the first
             ingredient — that means it's mostly maida.
           • 8g sugar per serving, and the serving size is just 3 biscuits.
             Nobody eats 3 biscuits.
           • Sodium is 18% of daily limit per serving — high for a snack.
           • "0g trans fat" — but contains partially hydrogenated oils.
             That's trans fat under the legal limit per serving.

           Bottom line: this is a refined flour biscuit with a health halo.
           Swap to roasted chana or makhana for a real snack.
```

**Dietary memory across conversation:**
```
You:       I have hypertension. Keep that in mind.

NutriChef: Got it — I'll keep everything low-sodium from now on.
           No pickles, papads, or packaged masalas in any suggestion.

You:       Can I have chole bhature?

NutriChef: Yes — with some changes. The chole itself is great
           (chickpeas are potassium-rich, good for BP). I'd make the
           bhature with whole wheat instead of maida, air-fry instead
           of deep-fry, and skip the salt in the dough entirely —
           use amchur and jeera for flavour instead.
```

---

## 🏗️ Architecture

NutriChef is a **production-grade RAG pipeline** with condition-filtered semantic retrieval, prompt caching, structured JSON responses, and visual macro rendering — not a simple chatbot.

```
User Input (dish OR ingredients + condition + cuisine)
    │
    ▼
┌─────────────────────────────────────────┐
│           Streamlit Frontend            │
│  app.py                                 │
│  - Condition selector (7 conditions)    │
│  - Mode: fridge / transform             │
│  - Visual recipe card + macro pie chart │
│  - Health score badge (1-10)            │
│  - Conversation memory                  │
└────────────────┬────────────────────────┘
                 │ agent_run(message, condition, cuisine, history)
                 ▼
┌─────────────────────────────────────────┐
│           agent.py — Generator          │
│  - _detect_mode() → fridge/transform/   │
│    label/general                        │
│  - build_history() → last 10 turns      │
│  - Structured JSON response (macros +   │
│    health score + recipe)               │
│  - Prompt caching (cache_control)       │
└────────────────┬────────────────────────┘
                 │ build_context_blocks(query, condition, cuisine)
                 ▼
┌─────────────────────────────────────────┐
│           rag.py — Retrieval Layer      │
│  - Condition rules block  → CACHED ✅   │
│  - Cuisine profile block  → CACHED ✅   │
│  - Retrieved RAG chunks   → dynamic 🔄  │
└──────────────┬──────────────────────────┘
               │ condition-filtered cosine search
               ▼
┌─────────────────────────────────────────┐
│  ChromaDB — Vector Store                │
│  167 chunks · HuggingFace embeddings    │
│  all-MiniLM-L6-v2 · cosine similarity  │
└──────────────┬──────────────────────────┘
               │ indexed from
               ▼
┌─────────────────────────────────────────┐
│  knowledge_base.json                    │
│  7 conditions · 44 ingredients          │
│  19 swaps · 4 cuisine profiles          │
└─────────────────────────────────────────┘
```

### RAG — Condition-filtered retrieval

ChromaDB stores 167 chunks from `knowledge_base.json` as HuggingFace embeddings. Every retrieval is filtered by condition — a diabetic user only gets diabetes-relevant chunks, never mixed with hypertension rules. The retriever returns the top-k most relevant chunks across three categories: condition rules, ingredient swaps, and cuisine profiles.

### Prompt Caching — 90% cost reduction

Static context (condition rules + cuisine profile) is marked with `cache_control: ephemeral`. Anthropic caches these for 5 minutes — repeated requests from the same user pay 10% of normal input token cost. Only the dynamic RAG chunks and user message are charged at full rate.

### Structured JSON Responses

Every Claude response is structured JSON — recipe name, ingredients, steps, nutrition (cal/protein/fat/carbs), health score (1-10), and reasoning. `app.py` renders this as a visual card with a Plotly macro pie chart and colour-coded health score badge, not raw text.

---

## ✨ Key Features

| Feature | Description |
|---|---|
| 🔄 Dish Transformation | Make any recipe healthier with condition-aware swaps |
| 🧺 Fridge-first Recipes | Generate healthy recipes from available ingredients |
| 🏥 Condition Personalisation | Every recipe filtered through your specific health condition |
| 🌍 Indian Cuisine First | North Indian, South Indian, Gujarati, Maharashtrian — not quinoa and kale |
| 💬 Conversation Memory | Remembers your condition and preferences across the session |
| 📊 Macro Pie Chart | Visual breakdown of calories, protein, fat, carbs per recipe |
| 🏆 Health Score | Every recipe scored 1-10 on condition alignment with reasoning |
| 🔍 RAG-Powered | Condition-filtered semantic retrieval from curated knowledge base |
| ⚡ Prompt Caching | 90% cost reduction on repeated context via Anthropic cache_control |
| 📡 Opik Observability | Full tracing of every RAG retrieval and Claude API call |

---

## 🗂️ Project Structure

```
nutrichef/
├── app.py                       # Streamlit frontend — UI, recipe cards, macro charts
├── requirements.txt             # Python dependencies
├── .env.example                 # API key template (copy to .env, never commit)
├── .env                         # your actual keys — gitignored, never committed
├── .gitignore
├── README.md
├── .devcontainer/               # VS Code dev container — one click environment setup
│   └── devcontainer.json
├── data/
│   ├── knowledge_base.json      # 7 conditions · 44 ingredients · 19 swaps · 4 cuisine profiles
│   └── chroma_db/               # ChromaDB vector index — gitignored, rebuilds automatically
└── src/
    ├── __init__.py
    ├── rag.py                   # ChromaDB, HuggingFace embeddings, condition-filtered retrieval
    └── agent.py                 # Generator — mode detection, RAG context, Claude API, JSON parsing
```

---

## 🛠️ Tech Stack

- **LLM:** Claude `claude-sonnet-4-6` via Anthropic SDK (direct — no LangChain wrapper)
- **Prompt Caching:** Anthropic `cache_control` — 90% cost reduction on repeated context
- **Embeddings:** HuggingFace `sentence-transformers/all-MiniLM-L6-v2` — semantic search, free, local, no API key
- **Vector Store:** ChromaDB — persistent, condition-filtered retrieval
- **Visualisation:** Plotly — macro pie charts rendered per recipe
- **Frontend:** Streamlit (v1 demo) → FastAPI + Next.js (production)
- **Observability:** Opik — full RAG and LLM call tracing
- **Deployment:** Streamlit Community Cloud (demo) → Railway (production)

---

## ⚡ Getting Started

**Just want to try it?** → [NutriChef on Streamlit Cloud](#) *(no install needed)*

---

### Option A — Dev Container (recommended)

The easiest way to run locally. Requires [VS Code](https://code.visualstudio.com/) and [Docker Desktop](https://www.docker.com/products/docker-desktop/).

#### 1. Clone the repo
```bash
git clone https://github.com/yourusername/nutrichef.git
cd nutrichef
```

#### 2. Open in VS Code
```bash
code .
```
VS Code will detect the `.devcontainer/` folder and prompt:
> *"Reopen in Container"* → click it.

The container installs all dependencies automatically from `requirements.txt`.

#### 3. Add your API keys
Create a `.env` file in the project root:
```bash
cp .env.example .env
```
Open `.env` and fill in:
```
ANTHROPIC_API_KEY=sk-ant-your-key-here
ANTHROPIC_WORKSPACE_ID=your-workspace-id   # only if using identity-linked key
```

#### 4. Run
In the VS Code terminal (inside the container):
```bash
streamlit run app.py
```
VS Code forwards port `8501` automatically — click the popup or open `http://localhost:8501`.

> **First run:** downloads HuggingFace `all-MiniLM-L6-v2` (~80MB, cached after) and builds the ChromaDB index (~30 sec). Subsequent runs start instantly.

---

### Option B — Manual (venv)

If you prefer not to use Docker:

```bash
git clone https://github.com/yourusername/nutrichef.git
cd nutrichef

python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

pip install -r requirements.txt

cp .env.example .env            # add your ANTHROPIC_API_KEY

streamlit run app.py
```



---

## 📚 Knowledge Base

The knowledge base is the heart of NutriChef — and the part that took the longest to build.

As someone passionate about both cooking and health, I've spent years navigating the gap between "eat healthy" advice and what that actually means when you're standing in an Indian kitchen with a bag of atta, some dal, and leftovers in the fridge. Every condition has its own rules. Every ingredient has nuance. And the existing resources — research papers, dietitian blogs, YouTube videos — are scattered, often contradictory, and almost always written for a Western context.

Building this knowledge base meant reading through hundreds of references — clinical nutrition guidelines, ICMR dietary recommendations, Ayurvedic food science, glycaemic index studies specific to Indian foods, research on millets, and condition-specific dietary protocols — and distilling all of that into something a recipe agent can actually use.

What NutriChef gives you in seconds used to take hours of research.

The knowledge base currently covers:

- **7 lifestyle conditions** — each with dietary rules, preferred foods, foods to avoid, condition-specific swaps, and superfoods
- **44 ingredients** across grains/millets, dals, vegetables, dairy, seeds, and spices — each tagged by condition suitability and caution flags
- **19 ingredient swaps** — all condition-mapped with ratios and reasons (e.g. maida → besan for diabetes, cream → hung curd for PCOS)
- **4 Indian cuisine profiles** — North Indian, South Indian, Gujarati, Maharashtrian — with typical problem areas and healthy defaults
- **Label reading guide** — Indian packaged food red flags, hidden sugar names, trans fat loopholes, marketing claims to ignore

---

### ✅ v1 — Done
- [x] Dish transformation — make any recipe healthier
- [x] Fridge-first recipe generation with cuisine preference
- [x] Condition-aware personalisation (7 lifestyle conditions)
- [x] Indian vegetarian knowledge base
- [x] HuggingFace semantic embeddings + ChromaDB RAG layer
- [x] Prompt caching — 90% cost reduction on repeated context
- [x] Structured JSON responses — recipe + macros + health score
- [x] Visual recipe cards — Plotly macro pie chart + health score badge
- [x] Conversation memory — last 10 turns
- [x] Streamlit Cloud deployment

### 🚧 v2 — In Progress
- [ ] 📸 Fridge photo — snap ingredients, skip the typing
- [ ] 🏷️ Nutrition label reader — upload any label, get a plain-language breakdown
- [ ] Weekly meal planner — 7-day plan based on condition + fridge
- [ ] Grocery gap filler — "you're 2 ingredients away from this recipe"
- [ ] Qdrant Cloud — persistent vector store for production"

### 🔮 v3 — Future Vision

**1. External APIs for Food Safety**
Integration with food safety databases (FSSAI, EFSA, Open Food Facts) to flag harmful additives, allergens, and banned ingredients in real time. Ask NutriChef "is this safe?" about any packaged product and get a regulatory-backed answer — not just a nutrition breakdown, but an actual safety verdict. Particularly powerful for parents, allergy sufferers, and people managing multiple conditions.

**2. Research Mode — Reference-Backed Answers**
A dedicated research mode where every NutriChef recommendation links to the clinical study, ICMR guideline, or peer-reviewed paper it came from. Instead of "methi helps with blood sugar," you get "methi improves insulin sensitivity — here's the 2021 study from the Journal of Ethnopharmacology." Designed for users who want to go deeper, for healthcare professionals using NutriChef as a reference tool, and for building trust at scale.

**3. Learning & Explainability**
NutriChef doesn't just tell you what to eat — it teaches you why. A progressive learning layer that explains the science behind every swap in plain language, tracks what you've learned across sessions, and surfaces a "nutrition insight of the day" based on your condition. Over time, users build genuine food literacy — they stop needing to ask NutriChef the same questions because they've internalised the logic. The goal is to make itself less necessary over time, not more.

---

## 👩‍💻 About the Builder

**Hima Mehta** — AI/LLM Engineer  
[LinkedIn](#) · [GitHub](#)

I built NutriChef because I lived the problem.

I'm passionate about cooking and deeply health-conscious — and I've watched people close to me manage lifestyle diseases while trying to hold on to the food they love. The advice was always the same: "eat healthy." But nobody explained what that meant for someone who grew up eating dal-chawal, who finds comfort in a bowl of khichdi, who doesn't know what quinoa tastes like and doesn't want to.

So I started researching. Every time someone asked me "can I eat this with diabetes?" or "what do I make with PCOS?", I'd spend hours reading — clinical studies, ICMR guidelines, nutrition research on Indian millets and spices, GI indices of Indian foods that Western databases don't even list. I'd read thousands of references to arrive at one confident, personalised answer.

NutriChef is that research, made accessible. Every swap, every caution flag, every condition-specific rule in the knowledge base was earned through that process — not scraped or generated. It's the kind of tool I wished existed when I started.

---

## 📄 License

MIT License — use freely, credit appreciated.
