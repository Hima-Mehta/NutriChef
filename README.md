# 🥗 NutriChef — AI-Powered Healthy Recipe Assistant

> No more endless YouTube rabbit holes hunting for healthy alternatives. No more staring at a half-empty fridge feeling like you're compromising on the dish you actually want. Cooking from limited ingredients isn't a constraint — it's an art. And NutriChef is your creative partner in it.

Transform any dish into a healthier version, or tell NutriChef what's in your fridge and what cuisine you're craving — it does the rest. Smart ingredient swaps, nutrition tracking, and a conversational interface that remembers your dietary needs.

---

## 🚀 Live Demo

🔗 [NutriChef on Hugging Face Spaces](#) *(link coming soon)*  
📹 [60-second Demo](#) *(Loom link coming soon)*

---

## 🧠 What It Does

NutriChef works in two ways:

**1. Transform a dish**
Give it any recipe — `butter chicken`, `pasta carbonara`, `aloo paratha` — and it returns a healthier version with smart ingredient swaps, nutrition comparison, and the science behind each change.

**2. Cook from your fridge**
Tell it what ingredients you have and what cuisine you're in the mood for — it builds you a complete healthy recipe from scratch, using only what's available.

In both modes, NutriChef:
- **Remembers** your dietary preferences across the conversation (vegan, diabetic-friendly, low-carb, etc.)
- **Explains** the nutritional benefit of every swap
- **Compares** calories and macros: original vs healthy
- **Suggests** alternatives if you're missing an ingredient

---

## 💬 Example Conversations

**Dish transformation:**
```
You:       Make butter chicken healthier

NutriChef: Here's a lighter version — swapped heavy cream for Greek yogurt
           (saves ~400 kcal, adds probiotics), reduced butter by half using
           olive oil. Spices kept intact. Protein stays the same,
           saturated fat drops by 60%.
```

**Fridge-first recipe:**
```
You:       I have chicken, spinach, Greek yogurt, garlic, and tomatoes.
           Something Indian please.

NutriChef: Here's a healthy Chicken Saag!
           Uses all your ingredients — Greek yogurt replaces cream,
           spinach adds iron and fibre.
           ~320 kcal | 38g protein | 12g fat | 8g carbs per serving.
```

**With dietary memory:**
```
You:       I'm diabetic, keep that in mind going forward.

NutriChef: Got it — all suggestions will be low-GI from now on.

You:       What about biryani?

NutriChef: For a diabetic-friendly biryani, I'd use brown basmati or
           cauliflower rice instead of white rice, and a yogurt-based
           marinade to keep the GI low...
```

---

## 🏗️ Architecture

```
User Input (dish OR ingredients + cuisine + dietary needs)
    │
    ▼
┌─────────────────────────────────────────┐
│           Streamlit Frontend            │
└────────────────┬────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────┐
│         LangChain Agent (Core)          │
│  - Conversation memory                  │
│  - Dietary preference tracking          │
│  - Tool routing                         │
└──────┬──────────────┬───────────────────┘
       │              │
       ▼              ▼
┌────────────┐  ┌──────────────────────────┐
│  ChromaDB  │  │       Tool Calls          │
│  (RAG)     │  │  - USDA Nutrition API     │
│            │  │  - Calorie Comparator     │
│ Nutrition  │  │  - Ingredient Substituter │
│ Knowledge  │  └──────────────────────────┘
│    Base    │
└────────────┘
       │
       ▼
┌─────────────────────────────────────────┐
│         LangSmith (Tracing)             │
└─────────────────────────────────────────┘
```

---

## ✨ Key Features

| Feature | Description |
|---|---|
| 🔄 Dish Transformation | Make any recipe healthier with smart swaps |
| 🧺 Fridge-first Recipes | Generate healthy recipes from available ingredients |
| 🌍 Cuisine Preference | Indian, Italian, Chinese, Thai, Mediterranean & more |
| 🥦 Healthy by Default | Every output optimised for nutrition, not just taste |
| 💬 Conversation Memory | Remembers dietary needs across the session |
| 📊 Nutrition Breakdown | Calories, protein, fat, carbs — original vs healthy |
| 🔄 Smart Swaps | Substitutes if you're missing an ingredient |
| 🔍 RAG-Powered | Retrieves from a curated nutrition & cuisine knowledge base |
| 🛠️ Tool-Augmented | Live USDA API for accurate nutritional data |
| 📡 Tracing | Full LangSmith observability for every chain |

---

## 🗂️ Project Structure

```
nutrichef/
├── data/
│   └── knowledge_base.json      # Nutrition substitutions, cuisine profiles, cooking methods
├── src/
│   ├── rag.py                   # ChromaDB setup, embeddings, retrieval
│   ├── agent.py                 # LangChain agent with memory & tool routing
│   └── tools.py                 # USDA API, calorie comparator, ingredient substituter
├── app.py                       # Streamlit frontend
├── requirements.txt
└── .env                         # API keys (not committed)
```

---

## 🛠️ Tech Stack

- **LLM:** Claude (via Anthropic API)
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

The RAG knowledge base covers:
- **Ingredient substitutions** — 50+ swaps with health benefits and ratios
- **Cuisine profiles** — Indian, Italian, Chinese, Thai, Mediterranean cooking patterns
- **Cooking methods** — healthier techniques (air fry vs deep fry, steam vs sauté)
- **Dietary filters** — vegan, diabetic-friendly, low-carb, high-protein, gluten-free

---

## 🔭 Roadmap

- [ ] Image input — photograph your fridge or a dish, auto-detect ingredients
- [ ] Weekly meal planner — plan 7 days from one fridge scan
- [ ] Grocery gap filler — "you're 2 ingredients away from this recipe"
- [ ] WhatsApp bot integration

---

## 👩‍💻 Author

**Hima Mehta**  
AI/LLM Engineer  
[LinkedIn](#) · [GitHub](#)

---

## 📄 License

MIT License — use freely, credit appreciated.
