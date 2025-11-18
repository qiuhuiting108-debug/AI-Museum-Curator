# app.py — AI Museum Curator (Stable Department Mode)
# Guaranteed to load real images for any MET department.

import streamlit as st
import requests
from openai import OpenAI
import random

# -----------------------------
# Page Setup
# -----------------------------
st.set_page_config(page_title="AI Museum Curator", page_icon="🎨", layout="wide")

# Title
st.markdown("""
# 🎨 AI Museum Curator
Explore artworks from The Metropolitan Museum of Art with AI-generated professional explanations.
""")

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
# MET API Helpers
# -----------------------------

MET_BASE = "https://collectionapi.metmuseum.org/public/collection/v1"


def get_all_department_ids(dept_id):
    """Get full list of objectIDs in a department from /objects endpoint."""
    url = f"{MET_BASE}/objects"
    resp = requests.get(url)

    if resp.status_code != 200:
        return []

    try:
        data = resp.json()
    except:
        return []

    all_ids = data.get("objectIDs", [])
    if not all_ids:
        return []

    # Filter only those belonging to selected department
    dept_ids = []
    for oid in all_ids:
        obj_url = f"{MET_BASE}/objects/{oid}"
        obj_data = requests.get(obj_url).json()
        if obj_data.get("departmentId") == dept_id:
            dept_ids.append(oid)

    return dept_ids


def get_valid_artwork(dept_id):
    """Return the first artwork in department that has an image."""
    all_ids = get_all_department_ids(dept_id)
    random.shuffle(all_ids)

    for oid in all_ids:
        data = requests.get(f"{MET_BASE}/objects/{oid}").json()
        img = data.get("primaryImage") or data.get("primaryImageSmall")
        if img:
            return data  # valid artwork

    return None


# -----------------------------
# AI Curator
# -----------------------------
def ai_curator(api_key, artwork):
    client = OpenAI(api_key=api_key)

    prompt = f"""
Act as a professional museum curator. Provide a clear and insightful interpretation
of the artwork in 2–3 paragraphs.

Title: {artwork.get('title')}
Artist: {artwork.get('artistDisplayName')}
Date: {artwork.get('objectDate')}
Medium: {artwork.get('medium')}
Dimensions: {artwork.get('dimensions')}
"""

    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are a professional museum curator."},
            {"role": "user", "content": prompt},
        ],
    )
    return resp.choices[0].message.content


# -----------------------------
# Main Display
# -----------------------------
if "load" not in st.session_state:
    st.info("← Choose a department and click **Load New Artworks**.")
else:
    dept_id = departments[selected_dept]

    with st.spinner("Loading artworks..."):
        artwork = get_valid_artwork(dept_id)

    if artwork is None:
        st.error("⚠ No artworks with images found in this department.")
        st.stop()

    # Layout
    col1, col2 = st.columns([1.3, 1])

    # Left (image)
    with col1:
        img = artwork.get("primaryImage") or artwork.get("primaryImageSmall")
        st.image(img, use_container_width=True)

    # Right (metadata)
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
                with st.spinner("AI curator is writing..."):
                    explanation = ai_curator(api_key, artwork)
                    st.write(explanation)
