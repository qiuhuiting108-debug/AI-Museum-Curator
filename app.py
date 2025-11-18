# app.py
# AI Museum Curator — Final Project (Stable Version with Error Handling)
# Fully matches the lecture UI layout.

import streamlit as st
import requests
from openai import OpenAI
import random

# -----------------------------
# Page Setup
# -----------------------------
st.set_page_config(
    page_title="AI Museum Curator",
    page_icon="🎨",
    layout="wide"
)

# Title
st.markdown(
    """
# 🎨 AI Museum Curator  
Explore artworks from The Metropolitan Museum of Art with AI-generated professional explanations.
"""
)

# -----------------------------
# Sidebar UI
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
    st.session_state["load_art"] = True

# About text
st.sidebar.markdown("---")
st.sidebar.header("About")
st.sidebar.write(
    """
This app fetches real artwork data from  
**The Metropolitan Museum of Art**  
and uses AI to generate **curator-style explanations**.
"""
)
st.sidebar.markdown(
    "[Data Source: MET Museum Open API](https://metmuseum.github.io/)"
)

# -----------------------------
# MET API Helpers
# -----------------------------
MET_BASE = "https://collectionapi.metmuseum.org/public/collection/v1"


def safe_json(response):
    """Safely parse JSON. Return {} if invalid."""
    try:
        return response.json()
    except:
        return {}


def get_object_ids_from_department(dept_id):
    """Fetch object IDs from a department, with full error handling."""
    url = f"{MET_BASE}/search"
    params = {"departmentId": dept_id, "hasImages": "true", "q": ""}

    r = requests.get(url)
    data = safe_json(r)

    object_ids = data.get("objectIDs") or []
    if not object_ids:
        return []
    return object_ids


def get_artwork(object_id):
    """Fetch artwork metadata, safe from API failures."""
    url = f"{MET_BASE}/objects/{object_id}"
    r = requests.get(url)
    return safe_json(r)


# -----------------------------
# AI Curator Function
# -----------------------------
def generate_curator_text(api_key, artwork):
    client = OpenAI(api_key=api_key)

    prompt = f"""
Act as a professional museum curator. Provide a thoughtful and engaging interpretation 
of this artwork in 2–3 paragraphs.

Title: {artwork.get('title')}
Artist: {artwork.get('artistDisplayName')}
Date: {artwork.get('objectDate')}
Medium: {artwork.get('medium')}
Dimensions: {artwork.get('dimensions')}
Culture: {artwork.get('culture')}
Department: {artwork.get('department')}
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
# Main App Logic
# -----------------------------
if "load_art" not in st.session_state:
    st.info("← Choose a department and click **Load New Artworks** to begin.")
else:
    dept_id = departments[selected_dept]

    # 1. Fetch Object IDs
    with st.spinner("Fetching artworks from the MET Museum..."):
        object_ids = get_object_ids_from_department(dept_id)

    if not object_ids:
        st.error("⚠️ This department has no available artworks. Try another one.")
    else:
        # pick random valid artwork
        object_id = random.choice(object_ids)

        with st.spinner("Loading artwork details..."):
            artwork = get_artwork(object_id)

        # Validate artwork image
        img = artwork.get("primaryImage") or artwork.get("primaryImageSmall")
        if not img:
            st.warning("This artwork has no image. Try loading again.")
            st.stop()

        # -----------------------------
        # UI Layout — Image (Left) / Info + AI (Right)
        # -----------------------------
        col1, col2 = st.columns([1.3, 1])

        # Image
        with col1:
            st.image(img, use_container_width=True)

        # Artwork Info
        with col2:
            st.markdown(f"## {artwork.get('title', 'Untitled')}")
            st.markdown(f"**Artist:** {artwork.get('artistDisplayName', 'Unknown')}")
            st.markdown(f"**Date:** {artwork.get('objectDate', 'Unknown')}")
            st.markdown(f"**Medium:** {artwork.get('medium', 'Unknown')}")
            st.markdown(f"**Dimensions:** {artwork.get('dimensions', 'Unknown')}")

            st.markdown("---")
            st.markdown("## Curator's Interpretation")

            openai_key = st.text_input("OpenAI API Key", type="password")

            if st.button("Generate Explanation"):
                if not openai_key:
                    st.error("Please enter your OpenAI API key.")
                else:
                    with st.spinner("AI Curator is writing..."):
                        try:
                            result = generate_curator_text(openai_key, artwork)
                            st.write(result)
                        except Exception as e:
                            st.error("AI generation failed. Please check your API key or try again later.")
