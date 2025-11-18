# app.py
# AI Museum Curator — Final Project (UI version similar to lecture screenshot)

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

# -----------------------------
# Title
# -----------------------------
st.markdown(
    """
# 🎨 AI Museum Curator  
Explore artworks from The Metropolitan Museum of Art with AI-generated professional explanations.
"""
)

# -----------------------------
# Sidebar
# -----------------------------
st.sidebar.header("Settings")

# Department dropdown (like screenshot)
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
    st.session_state["trigger"] = True

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
# Helper Functions
# -----------------------------
MET_BASE = "https://collectionapi.metmuseum.org/public/collection/v1"


def get_object_ids_from_department(dept_id):
    url = f"{MET_BASE}/search"
    params = {"departmentId": dept_id, "hasImages": "true", "q": ""}
    r = requests.get(url)
    data = r.json()
    return data.get("objectIDs", [])


def get_artwork(object_id):
    url = f"{MET_BASE}/objects/{object_id}"
    r = requests.get(url)
    return r.json()


def generate_curator_text(api_key, model, artwork):
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
        model=model,
        messages=[
            {"role": "system", "content": "You are a professional museum curator."},
            {"role": "user", "content": prompt},
        ],
    )

    return response.choices[0].message.content


# -----------------------------
# Main Display Logic
# -----------------------------
if "trigger" not in st.session_state:
    st.info("← Choose a department and click **Load New Artworks**.")
else:
    dept_id = departments[selected_dept]

    # 1. Get object IDs
    with st.spinner("Fetching artworks..."):
        object_ids = get_object_ids_from_department(dept_id)

    if not object_ids:
        st.error("No artworks found.")
    else:
        # pick a random artwork like screenshot
        object_id = random.choice(object_ids)

        with st.spinner("Loading artwork details..."):
            artwork = get_artwork(object_id)

        # layout: big image left, info right
        col1, col2 = st.columns([1.3, 1])

        # display image
        with col1:
            img = artwork.get("primaryImage") or artwork.get("primaryImageSmall")
            if img:
                st.image(img, use_container_width=True)
            else:
                st.warning("No image available.")

        # artwork info (title, artist, date, etc.)
        with col2:
            st.markdown(f"## {artwork.get('title', 'Untitled')}")
            st.markdown(f"**Artist:** {artwork.get('artistDisplayName', 'Unknown')}")
            st.markdown(f"**Date:** {artwork.get('objectDate', 'Unknown')}")
            st.markdown(f"**Medium:** {artwork.get('medium', 'Unknown')}")
            st.markdown(f"**Dimensions:** {artwork.get('dimensions', 'Unknown')}")

            st.markdown("---")
            st.markdown("## Curator's Interpretation")

            # ask for API key when needed
            openai_key = st.text_input("OpenAI API Key", type="password")
            model = "gpt-4o-mini"

            if st.button("Generate Explanation"):
                if not openai_key:
                    st.error("Please enter your OpenAI API key.")
                else:
                    with st.spinner("AI Curator is writing..."):
                        interpretation = generate_curator_text(
                            openai_key, model, artwork
                        )
                        st.write(interpretation)
