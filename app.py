import streamlit as st
import requests
from openai import OpenAI

# -----------------------------
# Basic Page Config
# -----------------------------
st.set_page_config(
    page_title="AI Museum Curator",
    page_icon="🖼️",
    layout="wide"
)

st.title("🖼️ AI Museum Curator")
st.markdown(
    """
This app fetches real artworks from the MET Museum Open API  
and asks an AI model to **act as a professional museum curator**  
to explain the artwork in a detailed, narrative way.
"""
)

# -----------------------------
# Sidebar – Settings
# -----------------------------
st.sidebar.header("🔑 AI Settings")

openai_api_key = st.sidebar.text_input(
    "OpenAI API Key",
    type="password",
    help="Paste your OpenAI API key here."
)

model_name = st.sidebar.selectbox(
    "Model",
    ["gpt-4.1-mini", "gpt-4.1", "gpt-4o-mini", "gpt-4o"],
    index=0
)

custom_style = st.sidebar.selectbox(
    "Curator Style",
    [
        "Formal museum curator",
        "Friendly guide for beginners",
        "Art historian tone",
        "Storytelling, emotional tone"
    ],
    index=0
)

st.sidebar.markdown("---")
st.sidebar.header("🎨 Artwork Search")

search_mode = st.sidebar.radio(
    "Search Mode",
    ["Keyword Search", "Random from Department"],
    index=0
)

keyword = ""
department_id = None

if search_mode == "Keyword Search":
    keyword = st.sidebar.text_input(
        "Keyword (e.g. Monet, flower, Korea, sculpture)",
        value="Monet"
    )
else:
    department_id = st.sidebar.selectbox(
        "MET Department",
        [
            ("European Paintings", 11),
            ("Modern and Contemporary Art", 21),
            ("Asian Art", 6),
            ("The American Wing", 1),
            ("Egyptian Art", 10),
            ("Greek and Roman Art", 3)
        ],
        format_func=lambda x: x[0]
    )

st.sidebar.markdown("---")
generate_button = st.sidebar.button("🔍 Fetch Artwork & Curator Explanation")

# -----------------------------
# MET Museum API helpers
# -----------------------------

MET_API_BASE = "https://collectionapi.metmuseum.org/public/collection/v1"


def search_artworks_by_keyword(q: str, max_results: int = 50):
    """
    Search artworks by keyword.
    Returns a list of objectIDs.
    """
    params = {
        "q": q,
        "hasImages": "true"
    }
    url = f"{MET_API_BASE}/search"
    resp = requests.get(url, params=params, timeout=10)
    if resp.status_code != 200:
        return []
    data = resp.json()
    object_ids = data.get("objectIDs") or []
    return object_ids[:max_results]


def search_artworks_by_department(dept_id: int, max_results: int = 50):
    """
    Search artworks by department.
    Returns a list of objectIDs.
    """
    params = {
        "departmentId": dept_id,
        "hasImages": "true",
        "q": ""   # empty query returns many
    }
    url = f"{MET_API_BASE}/search"
    resp = requests.get(url, params=params, timeout=10)
    if resp.status_code != 200:
        return []
    data = resp.json()
    object_ids = data.get("objectIDs") or []
    return object_ids[:max_results]


def get_artwork_details(object_id: int):
    """
    Fetch artwork metadata by objectID.
    """
    url = f"{MET_API_BASE}/objects/{object_id}"
    resp = requests.get(url, timeout=10)
    if resp.status_code != 200:
        return None
    return resp.json()


# -----------------------------
# OpenAI – AI Curator
# -----------------------------
def build_system_prompt(style_label: str) -> str:
    """
    Build system prompt according to selected curator style.
    """
    base = (
        "You are a professional museum curator. "
        "You explain artworks in a clear, insightful, and engaging way. "
        "You always connect visual details with historical, cultural, "
        "and emotional context, so that even beginners can understand."
    )

    if style_label == "Friendly guide for beginners":
        extra = (
            " Use simple, friendly language. "
            "Imagine you are explaining to a visitor who is new to art museums."
        )
    elif style_label == "Art historian tone":
        extra = (
            " Use a more academic tone, and mention art history terms, "
            "periods, styles, and references when relevant."
        )
    elif style_label == "Storytelling, emotional tone":
        extra = (
            " Focus on storytelling and emotions. "
            "Describe how the artwork might feel, and imagine the story behind it."
        )
    else:
        extra = ""

    return base + extra


def call_ai_curator(
    api_key: str,
    model: str,
    artwork: dict,
    style_label: str
) -> str:
    """
    Call OpenAI API to generate curator-style explanation.
    """
    client = OpenAI(api_key=api_key)

    title = artwork.get("title", "Unknown Title")
    artist = artwork.get("artistDisplayName", "Unknown Artist")
    date = artwork.get("objectDate", "Unknown Date")
    culture = artwork.get("culture", "")
    period = artwork.get("period", "")
    medium = artwork.get("medium", "")
    department = artwork.get("department", "")

    user_content = (
        f"Please explain the following artwork like a professional curator.\n\n"
        f"Title: {title}\n"
        f"Artist: {artist}\n"
        f"Date/Period: {date or period}\n"
        f"Culture: {culture}\n"
        f"Medium: {medium}\n"
        f"Department: {department}\n\n"
        "Describe:\n"
        "- The overall impression and visual composition\n"
        "- The artistic style or movement (if possible)\n"
        "- Historical and cultural context\n"
        "- Possible symbolism or meaning\n"
        "- Why this work might be important or interesting to visitors\n"
        "Write in 2–4 short paragraphs."
    )

    system_prompt = build_system_prompt(style_label)

    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content}
        ]
    )

    return response.choices[0].message.content.strip()


# -----------------------------
# Main App Logic
# -----------------------------
if generate_button:
    if not openai_api_key:
        st.error("⚠️ Please enter your OpenAI API key in the sidebar.")
    else:
        with st.spinner("Fetching artwork from MET Museum API..."):
            if search_mode == "Keyword Search":
                object_ids = search_artworks_by_keyword(keyword)
            else:
                # department_id is a tuple: (name, id)
                dept_name, dept_code = department_id
                object_ids = search_artworks_by_department(dept_code)

        if not object_ids:
            st.error("No artworks found. Try another keyword or department.")
        else:
            # Pick the first artwork (you could random.choice here as well)
            object_id = object_ids[0]
            artwork_data = get_artwork_details(object_id)

            if not artwork_data:
                st.error("Failed to fetch artwork details. Try again.")
            else:
                # Layout: left = image, right = metadata + AI explanation
                col1, col2 = st.columns([2, 3])

                with col1:
                    image_url = artwork_data.get("primaryImage") or artwork_data.get("primaryImageSmall")
                    if image_url:
                        st.image(image_url, caption=artwork_data.get("title", "Artwork"), use_container_width=True)
                    else:
                        st.warning("No image available for this artwork.")

                with col2:
                    st.subheader("🖼 Artwork Information")
                    st.markdown(f"**Title:** {artwork_data.get('title', 'Unknown')}")
                    st.markdown(f"**Artist:** {artwork_data.get('artistDisplayName', 'Unknown')}")
                    st.markdown(f"**Date:** {artwork_data.get('objectDate', 'Unknown')}")
                    st.markdown(f"**Culture:** {artwork_data.get('culture', 'Unknown')}")
                    st.markdown(f"**Medium:** {artwork_data.get('medium', 'Unknown')}")
                    st.markdown(f"**Department:** {artwork_data.get('department', 'Unknown')}")

                    st.markdown("---")
                    st.subheader("🧠 AI Curator Explanation")

                    with st.spinner("Asking AI curator for interpretation..."):
                        try:
                            curator_text = call_ai_curator(
                                api_key=openai_api_key,
                                model=model_name,
                                artwork=artwork_data,
                                style_label=custom_style
                            )
                            st.markdown(curator_text)
                        except Exception as e:
                            st.error(f"Error calling OpenAI API: {e}")

else:
    st.info("👈 Set your API key and search options in the sidebar, then click **“Fetch Artwork & Curator Explanation”**.")
