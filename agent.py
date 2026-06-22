"""
agent.py

The FitFindr planning loop. Orchestrates the three tools in response to a
natural language user query, passing state between them via a session dict.

Complete tools.py and test each tool in isolation before implementing this file.

Usage (once implemented):
    from agent import run_agent
    from utils.data_loader import get_example_wardrobe

    result = run_agent(
        user_id = session_id,  # some unique identifier for the user/session
        query="vintage graphic tee under $30, size M",
        wardrobe=get_example_wardrobe(),
    )
    print(result["fit_card"])
    print(result["error"])   # None on success
"""

import re
import json
import os
import uuid

from tools import search_listings, suggest_outfit, create_fit_card, compare_price
from utils.data_loader import load_listings

# ── preference profile ─────────────────────────────────────────────────────────────
PROFILES_PATH = "profiles.json"

def load_profile(user_id: str) -> dict:
    if not os.path.exists(PROFILES_PATH):
        return {"wardrobe": {"items": []}, "style_preferences": []}

    try:
        with open(PROFILES_PATH, "r") as f:
            profiles = json.load(f)
    except (json.JSONDecodeError, IOError) as error:
       print(f"Profile load failed: {type(error).__name__}: {error}")
       return {"wardrobe": {"items": []}, "style_preferences": []}

    return profiles.get(user_id, {"wardrobe": {"items": []}, "style_preferences": []})

def save_profile(user_id: str, wardrobe: dict, style_preferences: list) -> None:
    profiles = {}
    if os.path.exists(PROFILES_PATH):
        try:
            with open(PROFILES_PATH, "r") as f:
                profiles = json.load(f)
        except (json.JSONDecodeError, IOError):
            profiles = {}

    profiles[user_id] = {
        "wardrobe": wardrobe,
        "style_preferences": style_preferences,
    }

    with open(PROFILES_PATH, "w") as f:
        json.dump(profiles, f, indent=2)

# ── session state ─────────────────────────────────────────────────────────────

def _new_session(query: str, wardrobe: dict, style_preferences: list) -> dict:
    """
    Initialize and return a fresh session dict for one user interaction.

    The session dict is the single source of truth for everything that happens
    during a run — it stores the original query, parsed parameters, tool results,
    and any error that caused early termination.

    You may add fields to this dict as needed for your implementation.
    """
    return {
        "query": query,              # original user query
        "parsed": {},                # extracted description / size / max_price
        "search_results": [],        # list of matching listing dicts
        "selected_item": None,       # top result, passed into suggest_outfit
        "wardrobe": wardrobe,        # user's wardrobe dict
        "outfit_suggestion": None,   # string returned by suggest_outfit
        "fit_card": None,            # string returned by create_fit_card
        "error": None,               # set if the interaction ended early
        "style_preferences": style_preferences,  # list of user's style preferences
    }

# ── parser ─────────────────────────────────────────────────────────────
STOPWORDS = {
    "i", "a", "an", "the", "and", "or", "for", "in", "on", "at", "to",
    "want", "need", "looking", "find", "get", "some", "me", "my", "is",
    "it", "of", "with", "that", "this", "have", "just", "really", "very",
}

def _parse_query(query: str) -> dict:
    price_match = re.search(
        r"(?:under|max|below|for|less than|up to|around|at most)\s*\$?(\d+(?:\.\d+)?)"
        r"|\$?(\d+(?:\.\d+)?)\s*(?:or less|max|maximum|and under)",
        query,
        re.IGNORECASE,
    )
    if price_match:
        raw = price_match.group(1) or price_match.group(2)
        max_price = float(raw)
    else:
        max_price = None

    size_match = re.search(r"\bsize\s+([a-zA-Z0-9/]+)\b", query, re.IGNORECASE)
    size = size_match.group(1) if size_match else None

    description = query
    if price_match:
        description = description.replace(price_match.group(0), "")
    if size_match:
        description = description.replace(size_match.group(0), "")

    description = re.sub(r"[,\.]+", " ", description).strip()

    # reduce false matches by removing common stopwords from the description
    cleaned_words = [w for w in description.split() if w.lower() not in STOPWORDS]
    description = " ".join(cleaned_words)
    return {"description": description, "size": size, "max_price": max_price}

# ── planning loop ─────────────────────────────────────────────────────────────

def run_agent(query: str,  user_id: str, wardrobe: dict) -> dict:
    """
    Main agent entry point. Runs the FitFindr planning loop for a single
    user interaction and returns the completed session dict.

    Args:
        query:    Natural language user request
                  (e.g., "vintage graphic tee under $30, size M")
        wardrobe: User's wardrobe dict — use get_example_wardrobe() or
                  get_empty_wardrobe() from utils/data_loader.py

    Returns:
        The session dict after the interaction completes. Check session["error"]
        first — if it is not None, the interaction ended early and the other
        output fields (outfit_suggestion, fit_card) will be None.
    """

    profile = load_profile(user_id)

    if wardrobe is not None:
        resolved_wardrobe = wardrobe 
    else:
        resolved_wardrobe = profile["wardrobe"]

    style_preferences  = profile["style_preferences"]

    session = _new_session(query, resolved_wardrobe, style_preferences)

    session["parsed"] = _parse_query(query)
    parsed = session["parsed"]

    results = search_listings(
        description=parsed["description"],
        size=parsed.get("size"),
        max_price=parsed.get("max_price"),
    )

    session["search_results"] = results

    if not results:
        session["error"] = (
            f"No listings matched '{parsed['description']}'"
            + (f" in size {parsed['size']}" if parsed.get("size") else "")
            + (f" under ${parsed['max_price']}" if parsed.get("max_price") else "")
            + ". Try broadening your description, adjusting the size, or raising your budget."
        )
        return session

    session["selected_item"] = results[0]

    # Update style preferences by extracting tags from the selected item
    if "style_tags" in session["selected_item"]:
        for tag in session["selected_item"]["style_tags"]:
            if tag not in session["style_preferences"]:
                session["style_preferences"].append(tag)

    # optional price comparison
    price_result = compare_price(session["selected_item"], load_listings())
    session["price_verdict"] = price_result if price_result["success"] else None

    session["outfit_suggestion"] = suggest_outfit(
        new_item=session["selected_item"],
        wardrobe=session["wardrobe"],
        style_preferences= session["style_preferences"],
    )

    if not session["outfit_suggestion"]:
        session["error"] = "Could not generate an outfit suggestion for this item."
        return session

    session["fit_card"] = create_fit_card(
        outfit=session["outfit_suggestion"],
        new_item=session["selected_item"],
    )

    save_profile(user_id, session["wardrobe"], session["style_preferences"])

    return session


# ── CLI test ──────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    from utils.data_loader import get_example_wardrobe

    print("=== Happy path: graphic tee ===\n")
    session = run_agent(
        user_id=str(uuid.uuid4()),
        query="looking for a vintage graphic tee under $30",
        wardrobe=get_example_wardrobe(),
    )
    if session["error"]:
        print(f"Error: {session['error']}")
    else:
        print(f"Found: {session['selected_item']['title']}")
        print(f"\nOutfit: {session['outfit_suggestion']}")
        print(f"\nFit card: {session['fit_card']}")

    print("\n\n=== No-results path ===\n")
    session2 = run_agent(
        user_id=str(uuid.uuid4()),
        query="designer ballgown size XXS under $5",
        wardrobe=get_example_wardrobe(),
    )
    print(f"Error message: {session2['error']}")
