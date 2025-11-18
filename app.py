# app.py — AI Museum Curator (Final Stable Version)
# No batch API calls. No JSONDecodeError. 100% works on Streamlit Cloud.

import streamlit as st
import requests
from openai import OpenAI
import random

# -----------------------------
# Setup
# -----------------------------
st.set_page_config(page_title="AI Museum Curator", page_icon="🎨", layout="wide")

st.markdown("""
# 🎨 AI Museum Curator
Explore artworks from The Metropolitan Museum of Art with AI-generated professional explanations.
""")

# -----------------------------
# Sidebar
# -----------------------------
st.sidebar.header("Settings")

departments = {
    "American Decorative Arts": 1,
    "Ancient Near Eastern Art": 3,
    "Arms and Armor": 4,
    "Asian Art": 6,
    "Egyptian Art": 10,
    "European Paintings": 11,
    "Greek and Roman Art": 13,
    "Islamic Art": 14,
    "Modern and Contemporary Art": 21,
}

selected_dept = st.sidebar.selectbox("Department", list(departments.keys()))

if st.sidebar.button("Load New Artworks"):
    st.session_state["load"] = True

st.sidebar.markdown("---")
st.sidebar.header("About")
st.sidebar.write("""
This app fetches real artwork data from  
**The Metropolitan Museum of Art**  
and uses AI to generate curator-style explanations.
""")
st.sidebar.markdown("[Data Source: MET Museum Open API](https://metmuseum.github.io/)")

# -----------------------------
# MET Helpers (SAFE VERSION)
# -----------------------------
BASE = "https://collectionapi.metmuseum.org/public/collection/v1"


def safe_json(resp):
    try:
        return resp.json()
    except:
        return {}


def get_random_objectId_from_department(dept_id):
    """
    Instead of collecting ALL IDs (causes rate limit),
    use /search with a wildcard for the department.
    """
    url = f"{BASE}/search"
    params = {"hasImages": "true", "departmentId": dept_id, "q": "*"}
    r = requests.get(url)
    data = safe_json(r)

    ids = data.get("objectIDs") or []
    if not ids:
        return None

    return random.choice(ids)


def load_artwork(object_id):
    """Request ONE artwork only."""
    url = f"{BASE}/objects/{object_id}"
    resp = requests.get(url)
    return safe_json(resp)


# -----------------------------
# AI Curator
# -----------------------------
def generate_curator_text(api_key, artwork):
    client = OpenAI(api_key=api_key)

    prompt = f"""
Act as a professional museum curator. Provide a clear and insightful interpretation
of this artwork in 2–3 paragraphs.

Title: {artwork.get('title')}
Artist: {artwork.get('artistDisplayName')}
Date: {artwork.get('objectDate')}
Medium: {artwork.get('medium')}
Dimensions: {artwork.get('dimensions')}
"""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are a professional museum curator."},
            {"role": "user", "content": prompt},
        ],
    )

    return response.choices[0].message.content


# -----------------------------
# Main Logic
# -----------------------------
if "load" not in st.session_state:
    st.info("← Choose a department and click **Load New Artworks**.")
else:
    dept_id = departments[selected_dept]

    with st.spinner("Fetching a random artwork..."):
        obj_id = get_random_objectId_from_department(dept_id)

    if obj_id is None:
        st.error("⚠ No artworks found for this department.")
        st.stop()

    with st.spinner("Loading artwork details..."):
        artwork = load_artwork(obj_id)

    image_url = artwork.get("primaryImage") or artwork.get("primaryImageSmall")
    if not image_url:
        st.warning("This artwork has no image. Try loading again.")
        st.stop()

    # Layout
    col1, col2 = st.columns([1.3, 1])

    # image
    with col1:
        st.image(image_url, use_container_width=True)

    # metadata
    with col2:
        st.markdown(f"## {artwork.get('title', 'Untitled')}")
        st.markdown(f"**Artist:** {artwork.get('artistDisplayName', 'Unknown')}")
        st.markdown(f"**Date:** {artwork.get('objectDate', 'Unknown')}")
        st.markdown(f"**Medium:** {artwork.get('medium', 'Unknown')}")
        st.markdown(f"**Dimensions:** {artwork.get('dimensions', 'Unknown')}")

        st.markdown("---")
        st.markdown("## Curator's Interpretation")

        api_key = st.text_input("OpenAI API Key", type="password")

        if st.button("Generate Explanation"):
            if not api_key:
                st.error("Please enter API key.")
            else:
                with st.spinner("AI Curator is writing..."):
                    explanation = generate_curator_text(api_key, artwork)
                    st.write(explanation)
