# 🥗 NutriChef — Condition-Aware Healthy Recipes from Your Indian Kitchen

> No more endless YouTube rabbit holes hunting for healthy alternatives. No more staring at a half-empty fridge feeling like you're compromising on the dish you actually want. Cooking from limited ingredients isn't a constraint — it's an art. And NutriChef is your creative partner in it.

Built specifically for **Indian vegetarian households** managing lifestyle diseases — diabetes, PCOS, hypertension, high cholesterol, thyroid, obesity, or simply eating better. NutriChef gives you healthy recipes rooted in your actual kitchen, not a Western pantry.

---

## 🚀 Live Demo

🔗 [NutriChef on Hugging Face Spaces](#) *(link coming soon)*  
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

NutriChef is a **multi-agent LangGraph system with RAG-augmented specialist agents, tool use, and persistent condition-aware memory** — not a simple chatbot or a basic RAG pipeline.

```
User Input (dish OR ingredients + condition + cuisine)
    │
    ▼
┌─────────────────────────────────────────┐
│           Streamlit Frontend            │
│  - Condition selector                   │
│  - Image upload (fridge / label)        │
└────────────────┬────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────┐
│        LangGraph Orchestrator           │
│  - Routes to specialist agent           │
│  - Manages condition-aware memory       │
└──┬──────────┬──────────┬───────────┬───┘
   │          │          │           │
   ▼          ▼          ▼           ▼
🧺 Fridge  🔄 Transform 📸 Vision  🏷️ Label
Agent      Agent        Agent      Reader
                                   Agent
   └──────────────────────────────────┘
                    │
                    ▼
     ┌──────────────────────────────┐
     │        Shared Tools          │
     │  - USDA Nutrition API        │
     │  - Calorie Comparator        │
     │  - Ingredient Substituter    │
     └──────────────────────────────┘
                    │
                    ▼
     ┌──────────────────────────────┐
     │  ChromaDB — RAG Knowledge    │
     │  Condition rules · Swaps     │
     │  Ingredients · Cuisines      │
     └──────────────────────────────┘
                    │
                    ▼
     ┌──────────────────────────────┐
     │     LangSmith (Tracing)      │
     └──────────────────────────────┘
```

### Why Multi-Agent and not a single LLM call?

A single LLM call with a big system prompt can't specialise. When someone uploads a nutrition label, you need a nutritionist-advocate who knows Indian food marketing tricks. When someone asks for a fridge recipe, you need a creative Indian chef. These are different personas, different retrieval strategies, different tool sets — handled cleanly by separate agents.

### Agentic Pattern: Orchestrator → Specialist

The **Orchestrator** is a router. It reads the user's message, classifies intent (transform / fridge / image / label), and delegates to the right specialist agent. It never answers directly. Condition and dietary memory live here and are injected into every specialist agent's context.

Each **Specialist Agent** has:
- A focused system prompt tuned to its task
- Access to the shared RAG retriever
- Its own subset of tools
- A structured output schema so the frontend renders nutrition pills consistently

### RAG — Not just retrieval, condition-filtered retrieval

ChromaDB stores every entry from `knowledge_base.json` as an embedding. When an agent queries it, the retrieval is filtered by the user's condition — a diabetic user never gets hypertension-specific swap suggestions mixed into their context. The retriever returns the top-k most relevant chunks: condition rules + matching ingredients + applicable swaps.

### Tool Use — Grounding responses in real data

Agents decide autonomously whether to call a tool. If a user asks about a specific packaged ingredient, the agent calls the USDA API to fetch real macros rather than relying on the LLM's general knowledge. The Calorie Comparator tool computes the before/after macro delta for the nutrition breakdown shown in every response.

### State Management with LangGraph

LangGraph manages the conversation as a **stateful graph** — each node is an agent or tool, edges are conditional routing decisions. State (condition, preferences, conversation history, last retrieved context) persists across all nodes. This is what allows a user to say "I'm diabetic" once and have every subsequent agent response account for it automatically.

---

## ✨ Key Features

| Feature | Description |
|---|---|
| 🔄 Dish Transformation | Make any recipe healthier with condition-aware swaps |
| 🧺 Fridge-first Recipes | Generate healthy recipes from available ingredients |
| 🏥 Condition Personalisation | Every recipe filtered through your specific health condition |
| 📸 Snap your fridge | Upload a photo — NutriChef detects ingredients automatically |
| 🏷️ Label Reader | Upload any nutrition label — get a plain-language breakdown that calls out misleading claims |
| 🌍 Indian Cuisine First | North Indian, South Indian, Gujarati, Maharashtrian — not quinoa and kale |
| 💬 Conversation Memory | Remembers your condition and preferences across the session |
| 📊 Nutrition Breakdown | Calories, protein, fat, carbs — original vs healthy |
| 🔍 RAG-Powered | Retrieves from a curated condition-aware knowledge base |
| 🛠️ Tool-Augmented | Live USDA API for accurate nutritional data |
| 🤖 Agentic Framework | LangGraph multi-agent — specialist agents for each mode |
| 📡 Tracing | Full LangSmith observability for every agent call |

---

## 🗂️ Project Structure

```
nutrichef/
├── data/
│   └── knowledge_base.json      # 7 conditions · 44 ingredients · 19 swaps · 4 cuisine profiles
├── src/
│   ├── rag.py                   # ChromaDB setup, embeddings, retrieval
│   ├── agent.py                 # LangGraph orchestrator + specialist agents
│   └── tools.py                 # USDA API, calorie comparator, ingredient substituter
├── app.py                       # Streamlit frontend with condition selector + image upload
├── requirements.txt
└── .env                         # API keys (not committed)
```

---

## 🛠️ Tech Stack

- **LLM:** Claude (via Anthropic API)
- **Agentic Framework:** LangGraph
- **Orchestration:** LangChain
- **Vector Store:** ChromaDB
- **Frontend:** Streamlit
- **Nutrition Data:** USDA FoodData Central API
- **Observability:** LangSmith
- **Deployment:** Hugging Face Spaces

---

## ⚡ Getting Started

### 1. Clone the repo
```bash
git clone https://github.com/yourusername/nutrichef.git
cd nutrichef
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Set up environment variables
```bash
cp .env.example .env
# Add your keys:
# ANTHROPIC_API_KEY=
# USDA_API_KEY=        (free at https://fdc.nal.usda.gov/api-key-signup)
# LANGCHAIN_API_KEY=   (free at https://smith.langchain.com)
```

### 4. Run the app
```bash
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
- [x] LangGraph multi-agent architecture

### 🚧 v2 — In Progress
- [ ] 📸 Fridge photo — snap ingredients, skip the typing
- [ ] 🏷️ Nutrition label reader — upload any label, get a plain-language breakdown
- [ ] Weekly meal planner — 7-day plan based on condition + fridge
- [ ] Grocery gap filler — "you're 2 ingredients away from this recipe"

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
[LinkedIn](https://www.linkedin.com/in/hima-mehta-46322237/) · [GitHub](#)

I built NutriChef because I lived the problem.

I'm passionate about cooking and deeply health-conscious — and I've watched people close to me manage lifestyle diseases while trying to hold on to the food they love. The advice was always the same: "eat healthy." But nobody explained what that meant for someone who grew up eating dal-chawal, who finds comfort in a bowl of khichdi, who doesn't know what quinoa tastes like and doesn't want to.

So I started researching. Every time someone asked me "can I eat this with diabetes?" or "what do I make with PCOS?", I'd spend hours reading — clinical studies, ICMR guidelines, nutrition research on Indian millets and spices, GI indices of Indian foods that Western databases don't even list. I'd read thousands of references to arrive at one confident, personalised answer.

NutriChef is that research, made accessible. Every swap, every caution flag, every condition-specific rule in the knowledge base was earned through that process — not scraped or generated. It's the kind of tool I wished existed when I started.

---

## 📄 License

MIT License — use freely, credit appreciated.
