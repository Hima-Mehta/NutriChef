import streamlit as st
from streamlit_tags import st_tags
from src.agent import run as agent_run
import plotly.graph_objects as go

# Map display names to condition keys used in knowledge base
CONDITION_MAP = {
    "General Wellbeing":    "general_wellbeing",
    "Diabetes":             "diabetes",
    "PCOS":                 "pcos",
    "Hypertension":         "hypertension",
    "High Cholesterol":     "high_cholesterol",
    "Thyroid":              "thyroid",
    "Obesity":              "obesity"
}

CUISINE_MAP = {
    "North Indian":     "north_indian",
    "South Indian":     "south_indian",
    "Gujarati":         "gujarati",
    "Maharashtrian":    "maharashtrian",
    "No preference":    None
}

# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="NutriChef",
    page_icon="🥗",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── Custom CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;600&family=DM+Mono:wght@400;500&display=swap');

/* ── Root tokens ── */
:root {
    --green-deep:   #1B3A2D;
    --green-mid:    #2D5E45;
    --green-light:  #4A8C68;
    --cream:        #F7F3EC;
    --cream-dark:   #EDE8DF;
    --saffron:      #E8A020;
    --saffron-light:#F5C560;
    --text-dark:    #1A1A1A;
    --text-mid:     #4A4A4A;
    --text-light:   #8A8A8A;
    --white:        #FFFFFF;
    --radius:       12px;
    --radius-sm:    8px;
}

/* ── Global reset ── */
html, body, [class*="css"] {
    font-family: 'DM Sans', sans-serif;
    background-color: var(--cream);
    color: var(--text-dark);
}

.stApp { background-color: var(--cream); }

/* Hide streamlit chrome */
#MainMenu, footer, header { visibility: hidden; }
.block-container { padding: 0 !important; max-width: 100% !important; }

/* ── Header ── */
.nutrichef-header {
    background: var(--green-deep);
    padding: 20px 48px;
    display: flex;
    align-items: center;
    justify-content: space-between;
}
.nutrichef-logo {
    font-size: 22px;
    font-weight: 600;
    color: var(--cream);
    letter-spacing: -0.3px;
}
.nutrichef-logo span {
    color: var(--saffron);
}
.nutrichef-tagline {
    font-size: 13px;
    color: rgba(247,243,236,0.55);
    font-weight: 400;
    letter-spacing: 0.2px;
}

/* ── Setup panel (mise en place) ── */
.setup-wrapper {
    max-width: 860px;
    margin: 48px auto 0 auto;
    padding: 0 24px;
}
.setup-title {
    font-size: 28px;
    font-weight: 600;
    color: var(--green-deep);
    margin-bottom: 6px;
    letter-spacing: -0.5px;
}
.setup-sub {
    font-size: 14px;
    color: var(--text-mid);
    margin-bottom: 32px;
    line-height: 1.6;
}
.setup-card {
    background: var(--white);
    border-radius: var(--radius);
    padding: 28px 32px;
    margin-bottom: 16px;
    border: 1px solid var(--cream-dark);
}
.setup-card-label {
    font-size: 11px;
    font-weight: 600;
    letter-spacing: 1px;
    text-transform: uppercase;
    color: var(--green-light);
    margin-bottom: 12px;
}

/* ── Mode toggle ── */
.mode-toggle-row {
    display: flex;
    gap: 10px;
    margin-bottom: 32px;
}
.mode-btn {
    flex: 1;
    padding: 14px 20px;
    border-radius: var(--radius-sm);
    border: 2px solid var(--cream-dark);
    background: var(--white);
    cursor: pointer;
    text-align: left;
    transition: all 0.15s ease;
}
.mode-btn.active {
    border-color: var(--green-deep);
    background: var(--green-deep);
    color: var(--cream);
}
.mode-btn-title { font-size: 14px; font-weight: 600; }
.mode-btn-desc  { font-size: 12px; opacity: 0.65; margin-top: 2px; }

/* ── Chat area ── */
.chat-wrapper {
    max-width: 760px;
    margin: 0 auto;
    padding: 0 24px 200px 24px;
}
.chat-bubble-user {
    background: var(--green-deep);
    color: var(--cream);
    padding: 14px 18px;
    border-radius: 18px 18px 4px 18px;
    margin: 12px 0 12px 60px;
    font-size: 14px;
    line-height: 1.6;
}
.chat-bubble-ai {
    background: var(--white);
    color: var(--text-dark);
    padding: 18px 22px;
    border-radius: 18px 18px 18px 4px;
    margin: 12px 60px 12px 0;
    font-size: 14px;
    line-height: 1.7;
    border: 1px solid var(--cream-dark);
}
.chat-bubble-ai .ai-label {
    font-size: 11px;
    font-weight: 600;
    letter-spacing: 0.8px;
    text-transform: uppercase;
    color: var(--green-light);
    margin-bottom: 8px;
}

/* Nutrition pill */
.nutrition-row {
    display: flex;
    gap: 8px;
    flex-wrap: wrap;
    margin-top: 14px;
}
.nutrition-pill {
    background: var(--cream);
    border: 1px solid var(--cream-dark);
    border-radius: 20px;
    padding: 4px 12px;
    font-size: 12px;
    font-family: 'DM Mono', monospace;
    color: var(--green-deep);
    font-weight: 500;
}
.nutrition-pill.highlight {
    background: var(--saffron-light);
    border-color: var(--saffron);
}

/* ── Input bar ── */
.input-bar-outer {
    position: fixed;
    bottom: 0; left: 0; right: 0;
    background: var(--cream);
    border-top: 1px solid var(--cream-dark);
    padding: 20px 24px 40px 24px;
    padding-bottom: max(40px, env(safe-area-inset-bottom, 40px));
    z-index: 100;
    box-shadow: 0 -4px 24px rgba(0,0,0,0.06);
}
.input-bar-inner {
    max-width: 760px;
    margin: 0 auto;
    display: flex;
    gap: 10px;
    align-items: flex-end;
}

/* Streamlit input overrides */
.stTextInput > div > div > input,
.stTextArea > div > div > textarea {
    background: var(--white) !important;
    border: 1.5px solid var(--cream-dark) !important;
    border-radius: var(--radius-sm) !important;
    font-family: 'DM Sans', sans-serif !important;
    font-size: 14px !important;
    color: var(--text-dark) !important;
    padding: 12px 16px !important;
}
.stTextInput > div > div > input:focus,
.stTextArea > div > div > textarea:focus {
    border-color: var(--green-mid) !important;
    box-shadow: 0 0 0 3px rgba(45,94,69,0.12) !important;
}

/* Streamlit button overrides */
.stButton > button {
    background: var(--green-deep) !important;
    color: var(--cream) !important;
    border: none !important;
    border-radius: var(--radius-sm) !important;
    font-family: 'DM Sans', sans-serif !important;
    font-weight: 500 !important;
    font-size: 14px !important;
    padding: 12px 24px !important;
    transition: background 0.15s ease !important;
}
.stButton > button:hover {
    background: var(--green-mid) !important;
}

/* Primary CTA */
.stButton.primary > button {
    background: var(--saffron) !important;
    color: var(--green-deep) !important;
    font-weight: 600 !important;
}
.stButton.primary > button:hover {
    background: var(--saffron-light) !important;
}

/* Select box */
.stSelectbox > div > div {
    border: 1.5px solid var(--cream-dark) !important;
    border-radius: var(--radius-sm) !important;
    background: var(--white) !important;
    font-family: 'DM Sans', sans-serif !important;
    font-size: 14px !important;
}

/* Multiselect */
.stMultiSelect > div > div {
    border: 1.5px solid var(--cream-dark) !important;
    border-radius: var(--radius-sm) !important;
    background: var(--white) !important;
}

/* Divider */
.section-divider {
    border: none;
    border-top: 1px solid var(--cream-dark);
    margin: 24px 0;
}

/* Context badge */
.context-badge {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    background: rgba(27,58,45,0.08);
    border-radius: 20px;
    padding: 4px 12px 4px 8px;
    font-size: 12px;
    color: var(--green-deep);
    font-weight: 500;
    margin: 4px 4px 4px 0;
}

/* Spinner */
.stSpinner > div { border-top-color: var(--green-deep) !important; }

</style>
""", unsafe_allow_html=True)


# ── Session state ─────────────────────────────────────────────────────────────
if "setup_done" not in st.session_state:
    st.session_state.setup_done = False
if "messages" not in st.session_state:
    st.session_state.messages = []
if "mode" not in st.session_state:
    st.session_state.mode = "fridge"
if "ingredients" not in st.session_state:
    st.session_state.ingredients = []
if "cuisine" not in st.session_state:
    st.session_state.cuisine = "Indian"
if "dietary" not in st.session_state:
    st.session_state.dietary = []
if "condition" not in st.session_state:
    st.session_state.condition = "general_wellbeing"
if "condition_display" not in st.session_state:
    st.session_state.condition_display = "General Wellbeing"
if "tokens_saved" not in st.session_state:
    st.session_state.tokens_saved = 0


# ── Recipe card renderer ─────────────────────────────────────────────────────
def _render_recipe_card(data: dict):
    score        = data.get("health_score", 7)
    score_color  = "#2D7A4F" if score >= 8 else "#E8A020" if score >= 5 else "#C0392B"
    score_bg     = "#E8F5EE" if score >= 8 else "#FEF5E4" if score >= 5 else "#FDECEA"
    nutrition    = data.get("nutrition", {})
    cal          = nutrition.get("calories",  0)
    prot         = nutrition.get("protein_g", 0)
    fat          = nutrition.get("fat_g",     0)
    carbs        = nutrition.get("carbs_g",   0)
    total_macro  = prot + fat + carbs or 1

    st.markdown(f"""
    <div style="background:var(--white);border:1px solid var(--cream-dark);border-radius:12px;padding:20px 24px;margin:12px 0;">
        <div style="display:flex;align-items:flex-start;justify-content:space-between;gap:16px;margin-bottom:12px;">
            <div>
                <div style="font-size:17px;font-weight:600;color:var(--green-deep);">{data.get("recipe_name","")}</div>
                <div style="font-size:13px;color:#555;margin-top:4px;line-height:1.5;">{data.get("description","")}</div>
            </div>
            <div style="text-align:center;background:{score_bg};border-radius:10px;padding:8px 14px;min-width:64px;flex-shrink:0;">
                <div style="font-size:22px;font-weight:700;color:{score_color};">{score}/10</div>
                <div style="font-size:10px;font-weight:600;color:{score_color};text-transform:uppercase;letter-spacing:0.5px;">Health score</div>
            </div>
        </div>
        <div style="font-size:11px;color:#888;margin-bottom:14px;">{data.get("health_score_reason","")}</div>
    </div>
    """, unsafe_allow_html=True)

    # Macro chart + pills side by side
    col_chart, col_info = st.columns([1, 1])

    with col_chart:
        if cal > 0:
            import plotly.graph_objects as go
            fig = go.Figure(go.Pie(
                labels   = ["Protein", "Fat", "Carbs"],
                values   = [prot, fat, carbs],
                hole     = 0.55,
                marker   = dict(colors=["#2D7A4F", "#E8A020", "#4A8C68"],
                               line=dict(color="#fff", width=2)),
                textinfo = "percent",
                textfont = dict(size=12),
                hovertemplate = "%{label}: %{value}g<extra></extra>"
            ))
            fig.update_layout(
                showlegend   = True,
                legend       = dict(orientation="h", y=-0.15, font=dict(size=11)),
                margin       = dict(t=10, b=10, l=10, r=10),
                height       = 200,
                annotations  = [dict(text=f"<b>{cal}</b><br>kcal",
                                     x=0.5, y=0.5, font_size=13,
                                     showarrow=False)]
            )
            fig.update_traces(textposition="inside")
            st.plotly_chart(fig, use_container_width=True, config=dict(displayModeBar=False))

    with col_info:
        st.markdown(f"""
        <div style="padding:8px 0;">
            <div style="display:flex;gap:8px;flex-wrap:wrap;margin-bottom:12px;">
                <span style="background:#E8F5EE;color:#2D7A4F;border-radius:20px;padding:4px 12px;font-size:12px;font-family:monospace;font-weight:600;">{prot}g protein</span>
                <span style="background:#FEF5E4;color:#B07D10;border-radius:20px;padding:4px 12px;font-size:12px;font-family:monospace;font-weight:600;">{fat}g fat</span>
                <span style="background:#EAF3DE;color:#3B6D11;border-radius:20px;padding:4px 12px;font-size:12px;font-family:monospace;font-weight:600;">{carbs}g carbs</span>
            </div>
            <div style="font-size:13px;color:#444;line-height:1.6;">{data.get("why_it_works","")}</div>
        </div>
        """, unsafe_allow_html=True)

    # Ingredients + Steps in expanders
    ingredients = data.get("ingredients", [])
    steps       = data.get("steps", [])
    swap_tip    = data.get("swap_tip", "")

    if ingredients:
        with st.expander("📋 Ingredients", expanded=True):
            for ing in ingredients:
                st.markdown(f"- {ing}")

    if steps:
        with st.expander("👩‍🍳 Steps", expanded=False):
            for step in steps:
                st.markdown(f"{step}")

    if swap_tip:
        st.markdown(f"""
        <div style="background:#FEF5E4;border-left:3px solid #E8A020;border-radius:0 8px 8px 0;padding:10px 14px;margin-top:8px;font-size:13px;color:#7A5500;">
            💡 <strong>Swap tip:</strong> {swap_tip}
        </div>
        """, unsafe_allow_html=True)


# ── Header (always visible) ───────────────────────────────────────────────────
st.markdown("""
<div class="nutrichef-header">
    <div>
        <div class="nutrichef-logo">🥗 Nutri<span>Chef</span></div>
        <div class="nutrichef-tagline">Cooking from what you have is an art.</div>
    </div>
</div>
""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# SCREEN 1 — SETUP (Mise en place)
# ══════════════════════════════════════════════════════════════════════════════
if not st.session_state.setup_done:

    st.markdown("""
    <div class="setup-wrapper">
        <div class="setup-title">Let's set up your kitchen.</div>
        <div class="setup-sub">
            No more browsing YouTube for healthy alternatives or staring at a half-empty fridge.<br>
            Tell NutriChef what you're working with — it'll handle the rest.
        </div>
    </div>
    """, unsafe_allow_html=True)

    with st.container():
        col_spacer1, col_main, col_spacer2 = st.columns([1, 3, 1])

        with col_main:

            # ── Mode selector ──
            st.markdown('<div class="setup-card-label">What do you want to do?</div>', unsafe_allow_html=True)
            mode_col1, mode_col2 = st.columns(2)
            with mode_col1:
                if st.button("🧺  Cook from my fridge\nUse what I already have", key="mode_fridge"):
                    st.session_state.mode = "fridge"
            with mode_col2:
                if st.button("🔄  Make a dish healthier\nTransform a specific recipe", key="mode_transform"):
                    st.session_state.mode = "transform"

            current_mode = st.session_state.mode
            st.markdown(
                f"**Mode selected:** {'🧺 Cook from fridge' if current_mode == 'fridge' else '🔄 Transform a dish'}",
                help="Switch using the buttons above"
            )

            st.markdown("<hr class='section-divider'>", unsafe_allow_html=True)

            # ── Fridge mode inputs ──
            if current_mode == "fridge":
                st.markdown('<div class="setup-card-label">What\'s in your fridge?</div>', unsafe_allow_html=True)
                ingredients_input = st.text_input(
                    label="ingredients",
                    placeholder="e.g. chicken, spinach, Greek yogurt, garlic, tomatoes",
                    label_visibility="collapsed"
                )
                st.caption("Separate ingredients with commas — add as many as you like.")

            # ── Transform mode inputs ──
            else:
                st.markdown('<div class="setup-card-label">Which dish do you want to transform?</div>', unsafe_allow_html=True)
                dish_input = st.text_input(
                    label="dish",
                    placeholder="e.g. Butter Chicken, Pasta Carbonara, Aloo Paratha",
                    label_visibility="collapsed"
                )

            st.markdown("<hr class='section-divider'>", unsafe_allow_html=True)

            # ── Cuisine & dietary ──
            pref_col1, pref_col2 = st.columns(2)

            with pref_col1:
                st.markdown('<div class="setup-card-label">Cuisine preference</div>', unsafe_allow_html=True)
                cuisine = st.selectbox(
                    label="cuisine",
                    options=["North Indian", "South Indian", "Gujarati", "Maharashtrian", "No preference"],
                    index=0,
                    label_visibility="collapsed"
                )

            with pref_col2:
                st.markdown('<div class="setup-card-label">Health condition</div>', unsafe_allow_html=True)
                condition_display = st.selectbox(
                    label="condition",
                    options=list(CONDITION_MAP.keys()),
                    index=0,
                    label_visibility="collapsed"
                )

            st.markdown("<br>", unsafe_allow_html=True)

            # ── CTA ──
            if st.button("→  Start cooking", key="start_btn"):
                st.session_state.cuisine          = cuisine
                st.session_state.condition        = CONDITION_MAP[condition_display]
                st.session_state.condition_display = condition_display
                st.session_state.setup_done       = True

                # Build the opening user message
                if current_mode == "fridge":
                    ingr = ingredients_input.strip() if ingredients_input else "whatever's available"
                    opening = f"I have: {ingr}. I'm in the mood for {cuisine} food. I am managing {condition_display}. Please suggest a healthy recipe!"
                else:
                    dish = dish_input.strip() if dish_input else "my dish"
                    opening = f"Please make '{dish}' healthier. I prefer {cuisine} flavours. I am managing {condition_display}."

                st.session_state.ingredients = ingredients_input.split(",") if current_mode == "fridge" and ingredients_input else []
                st.session_state.messages.append({"role": "user", "content": opening})
                st.rerun()


# ══════════════════════════════════════════════════════════════════════════════
# SCREEN 2 — CHAT
# ══════════════════════════════════════════════════════════════════════════════
else:

    # ── Top bar: badges + start over button ──────────────────────────────────
    top_left, top_right = st.columns([5, 1])

    with top_left:
        badges_html = f'<div style="padding: 12px 0;">'
        badges_html += f'<span class="context-badge">🏥 {st.session_state.condition_display}</span>'
        badges_html += f'<span class="context-badge">🌍 {st.session_state.cuisine}</span>'
        if st.session_state.ingredients:
            count = len([i for i in st.session_state.ingredients if i.strip()])
            badges_html += f'<span class="context-badge">🧺 {count} ingredients</span>'
        if st.session_state.tokens_saved > 0:
            badges_html += f'<span class="context-badge">⚡ {st.session_state.tokens_saved} tokens cached</span>'
        badges_html += '</div>'
        st.markdown(badges_html, unsafe_allow_html=True)

    with top_right:
        st.markdown("<div style='padding-top:8px'>", unsafe_allow_html=True)
        if st.button("← Start over", key="reset_btn"):
            # Clear all session state and return to setup screen
            for key in ["setup_done", "messages", "mode", "ingredients",
                        "cuisine", "condition", "condition_display", "tokens_saved"]:
                if key in st.session_state:
                    del st.session_state[key]
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

    # ── Chat messages ─────────────────────────────────────────────────────────
    st.markdown('<div class="chat-wrapper">', unsafe_allow_html=True)

    for msg in st.session_state.messages:
        if msg["role"] == "user":
            st.markdown(f'<div class="chat-bubble-user">{msg["content"]}</div>', unsafe_allow_html=True)
        else:
            data = msg.get("structured")
            if data and isinstance(data, dict) and data.get("recipe_name"):
                _render_recipe_card(data)
            else:
                st.markdown(f'''
                <div class="chat-bubble-ai">
                    <div class="ai-label">NutriChef</div>
                    {msg["content"]}
                </div>''', unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)

    # ── Real agent response ───────────────────────────────────────────────────
    if st.session_state.messages and st.session_state.messages[-1]["role"] == "user":
        with st.spinner("NutriChef is thinking..."):
            try:
                # Get all previous messages except the last user message (for history)
                history = st.session_state.messages[:-1]
                last_user_msg = st.session_state.messages[-1]["content"]

                # Call agent — RAG retrieval + Claude API
                result = agent_run(
                    message   = last_user_msg,
                    condition = st.session_state.condition,
                    cuisine   = CUISINE_MAP.get(st.session_state.cuisine),
                    history   = history
                )

                # Track cached tokens for display
                if result["cached"]:
                    st.session_state.tokens_saved += result["tokens_in"]

                st.session_state.messages.append({
                    "role":       "assistant",
                    "content":    result["response"],
                    "structured": result.get("structured", {})
                })

            except Exception as e:
                st.session_state.messages.append({
                    "role":    "assistant",
                    "content": f"Something went wrong: {str(e)}. Please check your API key in secrets."
                })

            st.rerun()

    # ── Fixed input bar ───────────────────────────────────────────────────────
    st.markdown('<div class="input-bar-outer"><div class="input-bar-inner">', unsafe_allow_html=True)

    input_col, btn_col = st.columns([5, 1])
    with input_col:
        user_input = st.text_input(
            label="message",
            placeholder="Ask a follow-up — swap an ingredient, adjust for dietary needs...",
            label_visibility="collapsed",
            key="chat_input"
        )
    with btn_col:
        send = st.button("Send →", key="send_btn")

    if send and user_input.strip():
        st.session_state.messages.append({"role": "user", "content": user_input.strip()})
        st.rerun()

    st.markdown('</div></div>', unsafe_allow_html=True)