# FitFindr — Starter Kit

This starter kit contains everything you need to begin Project 2.

## What's Included

```
ai201-project2-fitfindr-starter/
├── data/
│   ├── listings.json          # 40 mock secondhand listings
│   └── wardrobe_schema.json   # Wardrobe format + example wardrobe
├── utils/
│   └── data_loader.py         # Helper functions for loading the data
├── planning.md                # Your planning template — fill this out first
└── requirements.txt           # Python dependencies
```

## Setup

**macOS / Linux:**
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

**Windows:**
```bash
python -m venv .venv
source .venv/Scripts/activate
pip install -r requirements.txt
```

Set your Groq API key in a `.env` file (get a free key at [console.groq.com](https://console.groq.com)):
```
GROQ_API_KEY=your_key_here
```

## The Mock Listings Dataset

`data/listings.json` contains 40 mock secondhand listings across categories (tops, bottoms, outerwear, shoes, accessories) and styles (vintage, y2k, grunge, cottagecore, streetwear, and more).

Each listing has: `id`, `title`, `description`, `category`, `style_tags`, `size`, `condition`, `price`, `colors`, `brand`, and `platform`.

Load it with:
```python
from utils.data_loader import load_listings
listings = load_listings()
```

## The Wardrobe Schema

`data/wardrobe_schema.json` defines the format your agent uses to represent a user's existing wardrobe. It includes:

- `schema`: field definitions for a wardrobe item
- `example_wardrobe`: a sample wardrobe with 10 items you can use for testing
- `empty_wardrobe`: a starting template for a new user

Load an example wardrobe with:
```python
from utils.data_loader import get_example_wardrobe
wardrobe = get_example_wardrobe()
```

## Tool Inventory

Your README submission must document each tool's name, inputs, and return value. **These must exactly match your actual function signatures in `tools.py`.** Your documented interfaces will be checked against your actual function signatures in `tools.py` — if the parameter count or types contradict what's in the code, you may not receive full credit for that tool.

**search_listings(description, size, max_price)**

Inputs: description: str, size: str , max_price: float 
Returns: list[dict] — A matching listings sorted by keyword relevance score or an empty list if none matches
Purpose: It filters the dataset by price and size, and then scores remaining listings by keyword overlap with the description.

**suggest_outfit(new_item, wardrobe, style_preferences)**

Inputs: new_item: dict, wardrobe: dict, style_preferences: list ()
Returns: str of 1 or 2 outfit suggestions from the LLM based on selected_item from search_listing or general styling advice if the wardrobe is empty

**create_fit_card(outfit, new_item)**
Inputs: outfit: str, new_item: dict
Returns: str of a casual social media caption based on the outfit suggestion goten from suggest_outfit or error message string if outfit is empty
Purpose:C alls the Groq LLM at temperature 1.0 to generate a caption suitable for Instagram or TikTok for the user to easily use

**compare_price(item, listings)**
Inputs: item: dict, listings: list[dict]
Returns: dict with success, verdict (low/fair/high), message, and price stats. success will be false if fewer than 2 comparable listings are found
Purpose: Finds listings in the same category with at least one overlapping style tag, computes their average price, and classifies the item as low (below 15% aver), high (greater than 15% average), or fair

---
## Interaction Walkthrough Demo
<!-- Walk through a complete interaction step by step: natural language query → each tool call (and why) → final fit card.
     Walk through this carefully — it's how graders follow your agent's reasoning without a live demo.
     Use a specific example — do not leave this as a template. -->

The loop checks state at two decision points after parsing the query.

**Decision 1 — Did `search_listings` return results?**
`_parse_query` extracts `description`, `size`, and `max_price` from the query, strips stopwords, then passes them to `search_listings`. The loop immediately checks `if not results`.

**Example — no results path:**
Query: `"designer ballgown size XXS under $5"`

`_parse_query` extracts `description="ballgown"`, `size="XXS"`, `max_price=5.0`. `search_listings` filters all listings — every item either exceeds $5.00 or has no keyword overlap with "ballgown". The list comes back empty. The loop sets:

```
session["error"] = "No listings matched 'ballgown' in size XXS under $5.0. 
Try broadening your description, adjusting the size, or raising your budget."
```

The session returns immediately.

**Example — results found path:**
Query: `"vintage graphic tee under $30"`

`_parse_query` extracts `description="vintage graphic tee"`, `max_price=30.0`. `search_listings` finds multiple matches but "Y2K Baby Tee — Butterfly Print" scores highest and becomes `session["selected_item"]` and The loop continues.

Top Listing: Y2K Baby Tee — Butterfly Print
        Brand:     None
        Category:  tops
        Size:      S/M
        Condition: excellent
        Price:     $18.0
        Platform:  depop
        Colors:    white, pink, purple
        Tags:      y2k, vintage, graphic tee, cottagecore

---
**Between Decision 1 and Decision 2 — `compare_price` runs as an optional step**

`compare_price` looks for other listings in the same category (`tops`) with at least one overlapping style tag (  y2k, vintage, graphic tee, cottagecore). For `Y2K Baby Tee — Butterfly Print` it finds several comparables and calculates their average price and classifies the selected_ite at $18 as `"low"`

Price verdict: LOW — This item is priced below average — good deal compared to 14 similar listings averaging $22.00.

If fewer than 2 comparables exist it should return `{"success": False, "message": "Not enough comparable listings to evaluate this price."}`. The loop will sets `session["price_verdict"] = None` and continue to `suggest_outfit`. Technically since we have a lot in our listings there will always be more than 2 comparables

After a result is selected, its style tags are merged into `session["style_preferences"]` and are appended to the user's preferences. This means `suggest_outfit` receives an updated preferences list that reflects what the user just chose, shaping the LLM prompt within the same session.

---

**Decision 2 — Did `suggest_outfit` return a non empty string?**

`suggest_outfit` receives `Y2K Baby Tee — Butterfly Print` as the `new_item` along with the example wardrobe. Because the wardrobe has 10 items, it builds a specific prompt and pass that to the model rather than asking for general advice. 

under Outfit idea it returns 
"love the Y2K Baby Tee with the butterfly print. Based on your style preferences, here are two outfit suggestions that would pair well with this item:

**Outfit 1: Cottagecore Chic**
Pair the Y2K Baby Tee with a flowy, oversized denim skirt and a pair of white sneakers. Add a floppy sun hat and a layered necklace with a delicate charm to give the outfit a whimsical touch. This look combines your love for cottagecore, vintage, and feminine styles.

**Outfit 2: Grunge Revival**
Create a contrast by pairing the sweet butterfly tee with a pair of distressed denim jeans and a flannel shirt tied around your waist. Add a pair of black combat boots and a choker necklace to give the outfit a grunge-inspired edge. This look blends your fondness for 90s grunge, Y2K, and streetwear styles.

In both outfits, the butterfly tee takes center stage, and the other pieces complement its playful, vintage vibe. Feel free to experiment and add your own accessories to make the look truly yours!"

The loop checks `if not ession["outfit_suggestion"]`. If the LLM returns an empty string, `session["error"]` is set to `"Could not generate an outfit suggestion for this item."` and the loop returns before `create_fit_card` is called. Technically this only fires if the Groq API fails since we fall back to general styling advice when the wardrobe is empty 

if `outfit_suggestion` is confirmed non empty, (it is for this example) `create_fit_card` runs taking the outfit string and the selected_item's details to produce the final caption.

"I'm totally obsessing over my new Y2K Baby Tee with the cutest butterfly print - I scored it on Depop for just $18.0 and it's honestly the perfect addition to my wardrobe. I paired it with a flowy denim skirt and white sneakers for a whimsical vibe, but I'm also low-key thinking of dressing it down with some distressed denim and combat boots for a grunge-inspired look. Either way, this tee is giving me all the nostalgic feels and I'm so here for it."

**User query: vintage graphic tee under $30**

**Step 1 — Tool called: search_listings(description, size, max_price)**
- Tool: search_listings(description, size, max_price)
- Input: description="vintage graphic tee", size="M", max_price=30.0
- Why this tool: it helps the user find items in their wardrobe that matches their query
- Output: list[dict] of the match listing

**Step 1.5 — Tool called:compare_price**
- Tool: compare_price
- Input: The listing and The full dataset to compare against.
- Why this tool: The user can see if the item's price is fair relative to comparable listings in the same category with overlapping style tags.
- Output: dictionary with keys for success, verdict, item_price, avg_comparable_price, and comparable_count.

**Step 2 — Tool called: suggest_outfit**
- Tool: suggest_outfit
- Input: top listing dict, user wardrobe dict, style preferences from stored profile
- Why this tool: This also the user to get oufit suggestions based on style
- Output: suggestion str

**Step 3 — Tool called: create_fit_card**
- Tool: reate_fit_card
- Input: outfit suggestion string, top listing dict
- Why this tool: Converts the outfit suggestion into a shareable caption for the user to post.
- Output: A caption string

**Final output to user:**
Y2K Baby Tee — Butterfly Print
        Brand:     None
        Category:  tops
        Size:      S/M
        Condition: excellent
        Price:     $18.0
        Platform:  depop
        Colors:    white, pink, purple
        Tags:      y2k, vintage, graphic tee, cottagecore
Price verdict: LOW — This item is priced below average — good deal compared to 14 similar listings averaging $22.00.

love the Y2K Baby Tee with the butterfly print. Based on your style preferences, here are two outfit suggestions that would pair well with this item:

**Outfit 1: Cottagecore Chic**
Pair the Y2K Baby Tee with a flowy, oversized denim skirt and a pair of white sneakers. Add a floppy sun hat and a layered necklace with a delicate charm to give the outfit a whimsical touch. This look combines your love for cottagecore, vintage, and feminine styles.

**Outfit 2: Grunge Revival**
Create a contrast by pairing the sweet butterfly tee with a pair of distressed denim jeans and a flannel shirt tied around your waist. Add a pair of black combat boots and a choker necklace to give the outfit a grunge-inspired edge. This look blends your fondness for 90s grunge, Y2K, and streetwear styles.

In both outfits, the butterfly tee takes center stage, and the other pieces complement its playful, vintage vibe. Feel free to experiment and add your own accessories to make the look truly yours!"

I'm totally obsessing over my new Y2K Baby Tee with the cutest butterfly print - I scored it on Depop for just $18.0 and it's honestly the perfect addition to my wardrobe. I paired it with a flowy denim skirt and white sneakers for a whimsical vibe, but I'm also low-key thinking of dressing it down with some distressed denim and combat boots for a grunge-inspired look. Either way, this tee is giving me all the nostalgic feels and I'm so here for it."

----
## Tool Inventory

**`search_listings(description, size, max_price)`**
- **Inputs:** `description (str)` — keywords describing the item after stopwords are stripped; `size (str)` — size token to match against listing size field, or None to skip; `max_price (float)` — max price for a lsiting
- **Returns:** `list[dict]` — each dict is a full listing with fields `id`, `title`, `description`, `category`, `style_tags` (list), `size`, `condition`, `price` (float), `colors` (list), `brand`, `platform`. Sorted highest relevance score first. Returns empty list if no listings pass all filters
- **Purpose:** Filters the mock dataset by price and size, then scores remaining listings by whole word keyword overlap with the description

**`suggest_outfit(new_item, wardrobe, style_preferences)`**
- **Inputs:** `new_item (dict)` — a listing dict for the item being considered; `wardrobe (dict)` — dict with an `items` key containing a list of wardrobe item dicts, may be empty; `style_preferences (list)` — list of style tag strings from the user's stored profile, default `[]`
- **Returns:** `str` — 1 or 2 complete outfit suggestions as a non empty string. If `wardrobe["items"]` is empty, returns general styling advice using common wardrobe staples. Incorporates `style_preferences` into the prompt when provided. Never returns an empty string or raises.
- **Purpose:** Calls the Groq LLM (llama-3.3-70b-versatile) to pair the new item with specific pieces from the user's wardrobe, or with general staples if the wardrobe is empty.

**`create_fit_card(outfit, new_item)`**
- **Inputs:** `outfit (str)` — the outfit suggestion string returned by `suggest_outfit`; `new_item (dict)` — the listing dict for the thrifted item
- **Returns:** `str` — a 2 or 4 sentence social media caption mentioning the item name, price, and platform once each naturally. If `outfit` is empty or whitespace, returns a descriptive error string instead of raising.
- **Purpose:** Calls the Groq LLM at temperature 1.0 to generate a fresh, casual OOTD caption suitable for Instagram or TikTok. Higher temperature ensures the output sounds different each time rather than templated.

**`compare_price(item, listings)`** *(bonus tool)*
- **Inputs:** `item (dict)` — the listing being evaluated; `listings (list[dict])` — the full dataset to compare against
- **Returns:** `dict` with keys `success (bool)`, `verdict (str)` — one of `"low"`, `"fair"`, or `"high"`; `item_price (float)`, `avg_comparable_price (float)`, `comparable_count (int)`, `message (str)` — human-readable verdict. If fewer than 2 comparable listings exist, returns `{"success": False, "message": "..."}`.
- **Purpose:** Finds listings in the same category with at least one overlapping style tag, computes their average price, and classifies the item as low (>15% below average), high (>15% above), or fair.

---

## State Management

All state for a single interaction lives in a session dict initialized by `_new_session` at the start of `run_agent`. Nothing is stored in global variables between tool calls — each tool receives exactly what it needs as explicit arguments read from the session.

| Field | Set when | Passed to |
|---|---|---|
| `session["query"]` | Immediately, from the function argument | Stored for reference; used in error messages |
| `session["parsed"]` | After `_parse_query` runs | Keys `description`, `size`, `max_price` passed as arguments to `search_listings` |
| `session["search_results"]` | After `search_listings` returns | Used to check for empty results and to set `selected_item` |
| `session["selected_item"]` | Set to `results[0]` if results exist | Passed to `compare_price`, `suggest_outfit`, and `create_fit_card` |
| `session["price_verdict"]` | After `compare_price` returns | Surfaced to the caller alongside the fit card |
| `session["style_preferences"]` | Loaded from profile at start; updated with item tags after selection | Passed to `suggest_outfit`; written back to `profiles.json` via `save_profile` |
| `session["outfit_suggestion"]` | After `suggest_outfit` returns | Passed as the `outfit` argument to `create_fit_card` |
| `session["fit_card"]` | After `create_fit_card` returns | Final output to the user |
| `session["error"]` | On any early exit | Caller checks this first; if not None, all other output fields are None |

Between sessions, only `wardrobe` and `style_preferences` are persisted and written to `profiles.json` at the end of a successful run and loaded at the start of the next.

---
**Outfit 1: Cottagecore Chic**
Pair the butterfly tee with a flowy, earth-toned linen skirt (think beige, sienna, or light brown) and a pair of neutral sandals (e.g., brown or beige). Add a minimalist straw hat and a delicate, floral hair clip to complete the look. This outfit embodies the cottagecore and feminine vibes you adore, while the earth tones bring a sense of warmth and coziness.

**Outfit 2: 90s Revival**
Create a fun, laid-back look by pairing the butterfly tee with a pair of high-waisted, light-washed linen shorts. Add a pair of chunky sneakers (e.g., white or beige) and a simple, woven tote bag in a natural color. You can also throw on a denim jacket or a cardigan in a soft, pastel hue to add a touch of 90s grunge to the outfit. This look combines your love of Y2K, vintage, and graphic tees with a relaxed, summer vibe.

Both outfits should fit seamlessly into your existing wardrobe, and you can always mix and match pieces to create new looks. Enjoy your thrifted find!

 **I just scored the cutest Y2K Baby Tee — Butterfly Print on Depop for $18.0 and I'm obsessed. I paired it with my fave flowy linen skirt and neutral sandals for a cottagecore vibe that's perfect for summer. The fact that it's in excellent condition is just the cherry on top - I feel like I raided my dream closet. Now, to decide whether to dress it up or down next...**

Here's the revised version:

---

## Price Comparison Tool

`compare_price` filters the full dataset to find listings in the same `category` with at least one overlapping `style_tag`, computes their average price, and classifies the selected item as `"low"` (more than 15% below average), `"high"` (more than 15% above), or `"fair"` (within 15% either way). If fewer than 2 comparables exist it returns `success: False` and the loop sets `session["price_verdict"] = None` and continues without blocking the interaction.

**Low verdict, query:** `"looking for a vintage graphic tee under $30"`

```
Price verdict: LOW — This item is priced below average — 
good deal compared to 14 similar listings averaging $22.00.
```

**High verdict, query:** `"90s leather bomber jacket"`

```
Price verdict: HIGH — This item is priced above average 
compared to 7 similar listings averaging $39.57.
```

---

## Style Profile Memory

Between sessions, `save_profile` writes `style_preferences` to `profiles.json` keyed by `user_id`. On the next run, `load_profile` restores those preferences and passes them into `suggest_outfit`, which adds them into the LLM prompt ("     Suggest 1-2 outfits using general wardrobe staples that would pair well with this item. Be sure to use and explicitly reference their style preferences if they have any."""
")
**Example**
**Interaction 1, query:** `"flowy midi skirt under $40"`
Top result is  90s Silk Slip Dress ($30, depop). Its tags get written to the profile:

"5c464646-338d-4194-a62b-450b49479fdd": {
  "style_preferences": ["90s", "vintage", "feminine", "floral", "cottagecore"]
}


**Interaction 2, query:** `"black combat boots"` (same app session so same user_id)
`load_profile` restores the preferences from interaction 1 before any tool runs. The top result is Oversized Flannel Shirt and Its tags get appended to the existing profile:

"5c464646-338d-4194-a62b-450b49479fdd": {
  "style_preferences": 
  ["90s", "vintage", "feminine", "floral", "cottagecore", "grunge", "flannel",       "streetwear", "layering"]
}

The fit card for the flannel picks up the `90s` preference from interaction 1 even though the current query had nothing to do with it:

> *"Just scored this Oversized Flannel Shirt from thredUp for $22 and it's giving major 90s vibes. Paired it with black shoes and accessories to make the plaid pop. Total steal."*

----

## Error Handling and Fail Points

<!-- For each tool, describe the specific failure mode and what your agent does in response.
     This maps to the error handling section of the rubric (F5-C1). -->

| Tool | Failure mode | What the agent does |
|---|---|---|
| `search_listings` | Returns empty list — no listings pass price, size, and keyword filters | Sets `session["error"]` with a message naming the specific failed constraint. Returns immediately. `suggest_outfit` and `create_fit_card` are never called.|
| `suggest_outfit` | Returns empty or falsy string | Sets `session["error"]` to `"Could not generate an outfit suggestion for this item."` Returns before `create_fit_card` is called. Wardrobe-empty case is handled inside the tool itself by switching to a general styling prompt — it never returns empty. |
| `create_fit_card` | `outfit` argument is empty or whitespace | Agent surfaces `Unable to generate a fit card — no outfit suggestion was provided. Try asking for styling advice first.` as the output. |
| `compare_price` | Fewer than 2 comparable listings found | Agent stores `None` in `session["price_verdict"]` and continues through the rest of the loop|
| `load_profile` | `profiles.json` exists but contains corrupt JSON | Catches `json.JSONDecodeError` and prints the exception for debugging. |

---
## Spec Reflection

<!-- Answer both questions with at least 2–3 sentences each. -->
**One way planning.md helped during implementation:**

Filling out the planning doc before writing any code forced me to think through the happy path and the failure cases before I hit them in the code. Specifically, it helped me decide where the loop should return early, how to handle empty results from `search_listings`, and why the three tools couldn't just be called sequentially for every request since a styling query has no reason to run a search.

**One divergence from your spec, and why:**
My original spec didn't fully account for what needed to be returned versus what should just live in the session. As I implemented the loop I kept needing to track more intermediate state, so the session object grew beyond what I had planned. I also added the extra credit features mid-way through, which meant reworking both the agent and the tools to support `compare_price`, the style preferences flow, and profile persistence. Those additions changed the shape of the loop more than I expected since they introduced new decision points and new variables that needed to be passed between tools.

## AI Tool Plan

<!-- For each part of the implementation below, describe:
     - Which AI tool you plan to use (Claude, Copilot, ChatGPT, etc.)
     - What you'll give it as input (which sections of this planning.md, your agent diagram)
     - What you expect it to produce
     - How you'll verify the output matches your spec before moving on

     "I'll use AI to help me code" is not a plan.
     "I'll give Claude my Tool 1 spec (inputs, return value, failure mode) and ask it to implement
     search_listings() using load_listings() from the data loader — then test it against 3 queries
     before trusting it" is a plan. -->

**Milestone 3 — Individual tool implementations:**
I used Claude for all the tool generation giving it the spec (inputs, return value, failure mode) from planning and the todo and asked it to implement the tools. I ended up having to revise some of the error statements and object design like the llm response call and return because it used the wrong specs. And also the parser it originally generated was too loose so i was getting matches for completely unrelated things so i added a stopword object as a source of truth for common words to ignore


**Milestone 4 — Planning loop and state management:**
I also use gave Claude the Architecture diagram and session schema to help me figure out how to implement style_prefrences and how to persist the data. It was not writing to the file correctly and then trying to read corrupted data so i added a try catch statement to handle that edge case
---

## Where to Start

1. **Read `planning.md` and fill it out before writing any code.**
2. Verify the data loads correctly by running `python utils/data_loader.py`.
3. Build and test each tool individually before connecting them through your planning loop.

Your implementation files go in this same directory. There's no required file structure for your agent code — organize it however makes sense for your design.
