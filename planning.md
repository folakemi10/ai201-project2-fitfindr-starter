# FitFindr — planning.md

> Complete this document before writing any implementation code.
> Your spec and agent diagram are what you'll use to direct AI tools (Claude, Copilot, etc.) to generate your implementation — the more specific they are, the more useful the generated code will be.
> Your planning.md will be reviewed as part of your submission.
> Update it before starting any stretch features.

---

## Tools

List every tool your agent will use. For each tool, fill in all four fields.
You must have at least 3 tools. The three required tools are listed — add any additional tools below them.

### Tool 1: search_listings

**What it does:**
searches the listing dataset and returns all matching items. It returns a not found message to the user when nothing the item is not in the dataset

**Input parameters:**
<!-- List each parameter, its type, and what it represents -->
- `description` (str): A describiption of the itek
- `size` (str): The size of the item
- `max_price` (float): The price ceiling for the item

**What it returns:**
<!-- Describe the return value — what fields does a result contain? -->
{
    "found": True,
    "item": {
        "id": "",
        "title": "",
        "description": "",
        "category": "",
        "style_tags": [],
        "size": "",
        "condition": "",
        "price": 0.0,
        "colors": [],
        "brand": "",
        "platform": ""
    }
}

**What happens if it fails or returns nothing:**
<!-- What should the agent do if no listings match? -->
a dictionary with a message string
{
    "found": False,
    "message": "No listings matched your search. Try broadening the description, adjusting the size, or raising the price ceiling."
}
---

### Tool 2: suggest_outfit

**What it does:**
suggests one or more complete outfit combinations using the given item and the user's current wardrobe, . should handle an empty or minimal wardrobe.

**Input parameters:**
<!-- List each parameter, its type, and what it represents -->
- `new_item` (dict): the full listing dict for the new item being being added to the wardrobe
- `wardrobe` (dict): the full listing dict for clothes in the user's current wardrobe 

**What it returns:**
 {
    "success": True,
    "outfit": "Pair the washed black band tee with your baggy jeans and chunky sneakers for a 90s street look."
}

**What happens if it fails or returns nothing:**
<!-- What should the agent do if the wardrobe is empty or no outfit can be suggested? -->
it should always return something. if the wardrobe is empty but a new item was provided it should suggest a
an pair for the item based on the item's style_tags, category, and colors. if the new item is missimg or no it should Return a message asking the user to pick an item first.
{
    "success": False,
    "message": "No item selected. Run a search first"
}
---

### Tool 3: create_fit_card

**What it does:**
Generates a styled, shareable fit card summarising the outfit — item details, suggested pairings, and a style label (e.g. "Street Casual").

**Input parameters:**
<!-- List each parameter, its type, and what it represents -->
- `outfit` (str): the outfit suggestion 
- `new_item` (dict): the full listing dict for the new item being featured

**What it returns:**
{
    "success": True,
    "card": {
        "title": "Your Fit: Street Casual",
        "featured_item": { new_item},
        "outfit_summary": "..."
    }
}

**What happens if it fails or returns nothing:**
If outfit is an empty string or new_item is missing required fields, the display message that says not enough information to build a fit card
---

### Additional Tools (if any)

<!-- Copy the block above for any tools beyond the required three -->
---

### Tool 4: compare_price

**What it does:**
Takes the selected item and searches the dataset for comparable listings by category and style tags, then returns whether the price is fair, high, or low relative to similar items.

**Input parameters:**
- `item` (dict): the full listing dict for the item being evaluated
- `listings` (list): the full dataset to compare against

**What it returns:**
{
    "success": ,
    "verdict": ,         
    "item_price": ,
    "avg_comparable_price": ,
    "message": "This item is priced fairly compared to 8 similar listings averaging $26.50."
}

**What happens if it fails or returns nothing:**
If outfit is an empty string or new_item is missing required fields, the display message that says not enough information to build a fit card
---

## Planning Loop

**How does your agent decide which tool to call next?**
If the user describes an item to find: the agent calls search_listings
If search_listings returned results AND the user wants styling help: the agent calls suggest_outfit
If suggest_outfit returned an outfit AND the user wants to share it: then call create_fit_card
At any point, if the user asks "style this for me" with an item already in session state: then skip search_listings and go straight to suggest_outfit
If the user just wants search results with no styling → stop after search_listings, never call the other two
---

## State Management

**How does information from one tool get passed to the next?**
<!-- Describe how your agent stores and accesses state within a session. What data is tracked? How is it passed between tool calls? -->
session = {
    "wardrobe": [],       
    "new_item": None,  
    "outfit": None
}
suggest_outfit reads new_item and wardrobe
create_fit_card reads new_item and outfit
---

## Error Handling

For each tool, describe the specific failure mode you're handling and what the agent does in response.

| Tool | Failure mode | Agent response |
|------|-------------|----------------|
| search_listings | No results match the query |Return found: False agent suggests dropping the size filter, raising max_price, or simplifying the description |
| suggest_outfit | Wardrobe is empty |Still returns success: True; agent generates generic pairings from the item's style_tags, category, and colors and notes the wardrobe is empty |
| create_fit_card | Outfit input is missing or incomplete | Return success: False; agent displays the raw outfit string as plain text and prompts the user to ask for styling suggestions first|
| compare_price | Fewer than 2 comparable listings| Return success: False; agent notes there isn't enough data to judge the price and continues without a verdict |

---

## Architecture

<!-- Draw a diagram of your agent showing how the components connect:
     User input → Planning Loop → Tools (search_listings, suggest_outfit, create_fit_card)
                                                                          ↕
                                                                   State / Session
     Show what triggers each tool, how state flows between them, and where error paths branch off.
     Use ASCII art or a Mermaid diagram (https://mermaid.js.org/syntax/flowchart.html).
     Do NOT embed an image — graders need to read your diagram directly in the file;
     an embedded image or screenshot cannot be evaluated.
     You'll share this diagram with an AI tool when asking it to implement
     the planning loop and each individual tool. -->

User input
    │
    ▼
Planning Loop — checks intent + session state to decide next tool
    │
    ├── "find me X" ──▶ search_listings(description, size, max_price)
    │       │ found: False ──▶ reply to loosen constraints, stop
    │       │ found: True  ──▶ session["new_item"] = item
    │                 │
    │           user wants styling?
    │              yes ──▶ suggest_outfit(new_item, wardrobe)
    │                          │ success: False ──▶ ask user to search first, stop
    │                          │ success: True  ──▶ session["outfit"] = outfit
    │                    user wants fit card?
    │                       yes ──▶ create_fit_card(outfit, new_item)
    │                                   │ success: False ──▶ show plain outfit text
    │                                   │ success: True  ──▶ show card, stop
    │                       no  ──▶ show outfit text, stop
    │              no  ──▶ show item, stop
    │
    └── "style it" (new_item in session) ──▶ suggest_outfit, skip search
    
                    ▲
        session = { new_item, outfit, wardrobe }
---

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

## A Complete Interaction (Step by Step)

Write out what a full user interaction looks like from start to finish — tool call by tool call. Use a specific example query.

**Example user query:** "I'm looking for a vintage graphic tee under $30. I mostly wear baggy jeans and chunky sneakers. What's out there and how would I style it?"

**Step 1:**
<!-- What does the agent do first? Which tool is called? With what input? -->
it should calls search_listings(description="vintage graphic tee", size=None, max_price=30.0). and set session["new_item"] to the band tee.

**Step 2:**
<!-- What happens next? What was returned from step 1? What tool is called now? -->
 step one returned the new_item and it should call suggest_outfit(new_item=session["new_item"], wardrobe=session["wardrobe"]). 

**Step 3:**
<!-- Continue until the full interaction is complete -->
 step two returned the suugested_outfit and it should call create_fit and generate caption
**Final output to user:**
<!-- What does the user actually see at the end? -->
the captions