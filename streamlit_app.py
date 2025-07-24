import streamlit as st, tempfile, os
from PIL import Image
from utils.cv_pipeline import run_hand_analysis

# ───────────── Color-badge helper ─────────────
def action_badge(action: str) -> str:
    colors = {"raise": "#e74c3c",  # red
              "call" : "#3498db",  # blue
              "fold" : "#7f8c8d"}  # gray
    return (f"<span style='background:{colors[action]};"
            f"color:white;padding:6px 12px;border-radius:6px;"
            f"font-weight:600;font-size:1.2rem;'>{action.upper()}</span>")

# ───────────── Basic CSS ─────────────
st.markdown("""
<style>
body { background-color:#f7f7f7; }
.small { font-size:0.85rem; color:#555; }
</style>
""", unsafe_allow_html=True)

# ───────────── Header ─────────────
if os.path.exists("assets/header.jpg"):          
    st.image("assets/header.jpg", use_container_width=True)

st.title("🂡 Poker Board Analyzer")
st.markdown(
    "<span class='small'>Upload a board photo, enter your hole cards, "
    "and get instant advice.</span>",
    unsafe_allow_html=True
)
st.divider()

# ───────────── Sidebar inputs ─────────────
with st.sidebar:
    st.header("Inputs")
    uploaded = st.file_uploader("Board image (.jpg / .png)")
    hole_txt = st.text_input("Hole cards",
                             placeholder="ten of clubs, ace of diamonds")
    players  = st.slider("Players in hand", 2, 10, 6)
    call_amt = st.number_input("Amount to call", min_value=0.0, value=5.0)
    pot_size = st.number_input("Pot size before call", min_value=0.0, value=20.0)
    go = st.button("Analyze")

# ───────────── Main logic ─────────────
if go and uploaded and hole_txt:
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".jpg")
    tmp.write(uploaded.read()); tmp.close()

    with st.spinner("Analyzing hand..."):
        try:
            res = run_hand_analysis(
                image_path  = tmp.name,
                hole_input  = hole_txt,
                num_players = players,
                call_amt    = call_amt,
                pot_before  = pot_size
            )
        except ValueError as e:
            st.error(str(e))
            os.remove(tmp.name)
            st.stop()

    # --- layout: big image left, results right
    left, right = st.columns([2, 1])

    with left:
        st.image(Image.open(tmp.name), caption="Uploaded board",
                 use_container_width=True)

    with right:
        st.subheader("Community Cards")
        st.write(", ".join(res["community_human"]))

        st.subheader("Recommended Action")
        st.markdown(action_badge(res["action"]), unsafe_allow_html=True)

        # --- Treys score visualization ---
        MAX_TREYS_SCORE = 7462
        score = res["hand_score"]
        strength = (MAX_TREYS_SCORE - score) / MAX_TREYS_SCORE * 100

        # Dynamic color logic
        if strength > 70:
            bar_color = "#27ae60"  # Green
        elif strength > 55:
            bar_color = "#2ecc71"  # Light green
        elif strength > 30:
            bar_color = "#f1c40f"  # Yellow
        else:
            bar_color = "#e74c3c"  # Red

        st.markdown(f"""
        <div style="
            background-color:#ddd;
            border-radius:8px;
            overflow:hidden;
            margin-bottom:10px;
        ">
          <div style="
              width:{strength:.1f}%;
              background-color:{bar_color};
              padding:8px 0;
              text-align:center;
              color:white;
              font-weight:bold;
          ">
            Hand Strength: {strength:.1f}%
          </div>
        </div>
        """, unsafe_allow_html=True)

    # --- nicer explanation ---
    expl = res["explain"]
    draw_str = (
        "Flush/Straight draw" if expl["straight_info"]["any_draw"] or expl["flush_draw"]
        else "None"
    )
    texture = expl["board_texture"]
    texture_str = (
        ("Paired, " if texture.paired else "Unpaired, ") +
        ("Monotone" if texture.monotone else "Rainbow")
    )

    with st.expander("Why this action?"):
        st.markdown(f"""
* **Stage:** {expl['stage'].title()}
* **Custom Treys score:** {score} out of {MAX_TREYS_SCORE} *(≈{strength:.0f}%)*  
* **Pot odds:** {res['pot_odds']:.0%}
* **Draw detected:** {draw_str}
* **Board texture:** {texture_str}
""", unsafe_allow_html=True)

    os.remove(tmp.name)

elif go:
    st.warning("Please upload a board image **and** enter your hole cards.")
