"""
tools.py

The three required FitFindr tools. Each tool is a standalone function that
can be called and tested independently before being wired into the agent loop.

Complete and test each tool before moving to agent.py.

Tools:
    search_listings(description, size, max_price)  → list[dict]
    suggest_outfit(new_item, wardrobe)              → str
    create_fit_card(outfit, new_item)               → str
"""

import os
import re

from dotenv import load_dotenv
from groq import Groq

from utils.data_loader import load_listings

load_dotenv()


# ── Groq client ───────────────────────────────────────────────────────────────
def _get_groq_client():
    """Initialize and return a Groq client using GROQ_API_KEY from .env."""
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        raise ValueError(
            "GROQ_API_KEY not set. Add it to a .env file in the project root."
        )
    return Groq(api_key=api_key)

client = _get_groq_client()
# ── Tool 1: search_listings ───────────────────────────────────────────────────

def search_listings(
    description: str,
    size: str | None = None,
    max_price: float | None = None,
) -> list[dict]:
    """
    Search the mock listings dataset for items matching the description,
    optional size, and optional price ceiling.

    Args:
        description: Keywords describing what the user is looking for
                     (e.g., "vintage graphic tee").
        size:        Size string to filter by, or None to skip size filtering.
                     Matching is case-insensitive (e.g., "M" matches "S/M").
        max_price:   Maximum price (inclusive), or None to skip price filtering.

    Returns:
        A list of matching listing dicts, sorted by relevance (best match first).
        Returns an empty list if nothing matches — does NOT raise an exception.

    Each listing dict has the following fields:
        id, title, description, category, style_tags (list), size,
        condition, price (float), colors (list), brand, platform

    TODO:
        1. Load all listings with load_listings().
        2. Filter by max_price and size (if provided).
        3. Score each remaining listing by keyword overlap with `description`.
        4. Drop any listings with a score of 0 (no relevant matches).
        5. Sort by score, highest first, and return the listing dicts.

    Before writing code, fill in the Tool 1 section of planning.md.
    """
    listings = load_listings()
    keywords = set(description.lower().split())
    scored = []

    for listing in listings:
        if max_price is not None and listing["price"] > max_price:
            continue
        if size is not None:
            listing_size = listing["size"].lower()
            query_size = size.lower()
             # Splitting to get rid of false matches i.e s and us 
            size_tokens = re.split(r"[\s/,]+", listing_size)
            if query_size not in size_tokens:
               continue
    
        searchable = " ".join([
            listing.get("title", ""),
            listing.get("description", ""),
            listing.get("category", ""),
            listing.get("brand") or "",
            " ".join(listing.get("style_tags", [])),
            " ".join(listing.get("colors", [])),
        ]).lower()

        # 4. Drop any listings with a score of 0 (no relevant matches).
        score = sum(1 for kw in keywords if kw in searchable)
        if score > 0:
            scored.append((score, listing))
    
    # 5. Sort by score, highest first, and return the listing dicts.
    scored.sort(key=lambda x: x[0], reverse=True)
    return [listing for _, listing in scored]


# ── Tool 2: suggest_outfit ────────────────────────────────────────────────────

def suggest_outfit(new_item: dict, wardrobe: dict, style_preferences: list = []) -> str:
    """
    Given a thrifted item and the user's wardrobe, suggest 1–2 complete outfits.

    Args:
        new_item: A listing dict (the item the user is considering buying).
        wardrobe: A wardrobe dict with an 'items' key containing a list of
                  wardrobe item dicts. May be empty — handle this gracefully.

    Returns:
        A non-empty string with outfit suggestions.
        If the wardrobe is empty, offer general styling advice for the item
        rather than raising an exception or returning an empty string.

    TODO:
        1. Check whether wardrobe['items'] is empty.
        2. If empty: call the LLM with a prompt for general styling ideas
           (what kinds of items pair well, what vibe it suits, etc.).
        3. If not empty: format the wardrobe items into a prompt and ask
           the LLM to suggest specific outfit combinations using the new item
           and named pieces from the wardrobe.
        4. Return the LLM's response as a string.

    Before writing code, fill in the Tool 2 section of planning.md.
    """
    # 1. Check whether wardrobe['items'] is empty.
    items = wardrobe.get("items", [])
    preferences = f"\nUser style preferences: {', '.join(style_preferences)}" if style_preferences else ""

    # 2. If empty: call the LLM with a prompt for general styling ideas    
    if not items:
        prompt = f"""You are a personal stylist. A user is considering buying this thrifted item:
            Item: {new_item.get("title")}
            Category: {new_item.get("category")}
            Style tags: {", ".join(new_item.get("style_tags", []))}
            Colors: {", ".join(new_item.get("colors", []))},
            {preferences}
        Suggest 1-2 outfits using general wardrobe staples that would pair well with this item. Use their style preferences if they have any."""

    # 3. If not empty: format the wardrobe items into a prompt and ask the LLM to suggest specific outfit combinations using the new item and named pieces from the wardrobe.
    else:
        wardrobe_lines = "\n".join(
            f"- {item.get('title')} ({item.get('category')}, {item.get('colors', [])})"
            for item in items
        )
        prompt = f"""You are a helpful personal stylist. A user is considering buying this thrifted item:
            Item: {new_item.get("title")}
            Category: {new_item.get("category")}
            Style tags: {", ".join(new_item.get("style_tags", []))}
            Colors: {", ".join(new_item.get("colors", []))}
        Their current wardrobe includes:
            {wardrobe_lines}
        Suggest 1-2 complete outfits using the new item and specific pieces from their wardrobe."""
   
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        max_tokens=500,
        messages=[{"role": "user", "content": prompt}]
    )

      # 4. Return the LLM's response as a string.
    return response.choices[0].message.content.strip()


# ── Tool 3: create_fit_card ───────────────────────────────────────────────────

def create_fit_card(outfit: str, new_item: dict) -> str:
    """
    Generate a short, shareable outfit caption for the thrifted find.

    Args:
        outfit:   The outfit suggestion string from suggest_outfit().
        new_item: The listing dict for the thrifted item.

    Returns:
        A 2–4 sentence string usable as an Instagram/TikTok caption.
        If outfit is empty or missing, return a descriptive error message
        string — do NOT raise an exception.

    The caption should:
    - Feel casual and authentic (like a real OOTD post, not a product description)
    - Mention the item name, price, and platform naturally (once each)
    - Capture the outfit vibe in specific terms
    - Sound different each time for different inputs (use higher LLM temperature)

    TODO:
        1. Guard against an empty or whitespace-only outfit string.
        2. Build a prompt that gives the LLM the item details and the outfit,
           and asks for a caption matching the style guidelines above.
        3. Call the LLM and return the response.

    
    """
    if not outfit or not outfit.strip():
        return "Unable to generate a fit card — no outfit suggestion was provided. Try asking for styling advice first."

    prompt = f"""You are writing a casual, authentic OOTD caption for a social media post.

    The outfit: {outfit}

    The thrifted item details:
    - Name: {new_item.get("title")}
    - Price: ${new_item.get("price")}
    - Platform: {new_item.get("platform")}
    - Condition: {new_item.get("condition")}

    Write a 2-4 sentence caption that:
    - Sounds like a real person, not a product listing
    - Mentions the item name, price, and platform once each, naturally
    - Feels fresh and specific to this exact outfit"""

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        max_tokens=200,
        temperature=1.0,
        messages=[{"role": "user", "content": prompt}]
    )

    return response.choices[0].message.content

def compare_price(item: dict, listings: list[dict]) -> dict:
    """
    Estimate whether an item's price is fair based on comparable listings.
    
    Args:
        item:     The listing dict for the item being evaluated.
        listings: The full dataset to compare against.
    
    Returns:
        A dict with verdict, price stats, and a human-readable message.
        If fewer than 2 comparables exist, returns success: False.
    """
    item_price    = item.get("price", 0.0)
    item_category = item.get("category", "").lower()
    item_tags     = set(t.lower() for t in item.get("style_tags", []))

    def is_comparable(listing):
        if listing.get("id") == item.get("id"):
            return False
        if listing.get("category", "").lower() != item_category:
            return False
        listing_tags = set(t.lower() for t in listing.get("style_tags", []))
        return len(listing_tags & item_tags) > 0

    comparables = [l for l in listings if is_comparable(l)]

    if len(comparables) < 2:
        return {
            "success": False,
            "message": "Not enough comparable listings to evaluate this price."
        }

    avg_price = sum(l["price"] for l in comparables) / len(comparables)

    if item_price < avg_price * 0.85:
        verdict = "low"
    elif item_price > avg_price * 1.15:
        verdict = "high"
    else:
        verdict = "fair"

    verdict_line = {
        "low":  f"This item is priced below average — good deal compared to {len(comparables)} similar listings averaging ${avg_price:.2f}.",
        "fair": f"This item is priced fairly compared to {len(comparables)} similar listings averaging ${avg_price:.2f}.",
        "high": f"This item is priced above average compared to {len(comparables)} similar listings averaging ${avg_price:.2f}.",
    }

    return {
        "success":              True,
        "verdict":              verdict,
        "item_price":           item_price,
        "avg_comparable_price": round(avg_price, 2),
        "comparable_count":     len(comparables),
        "message":              verdict_line[verdict],
    }