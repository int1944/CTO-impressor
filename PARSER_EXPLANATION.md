# Complete Parser System Explanation

## Table of Contents
1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Component Details](#component-details)
4. [Complete Flow Example](#complete-flow-example)
5. [Key Concepts](#key-concepts)

---

## Overview

The parser is a **rule-based autocomplete system** for travel queries (flights, hotels, trains). It:
- Detects user intent (flight/hotel/train)
- Extracts entities (cities, dates, times, etc.)
- Infers what information is missing (next slot)
- Generates suggestions to guide the user

**Key Design Principle**: The parser works **incrementally** - it provides suggestions as the user types, not just at the end.

---

## Architecture

```
User Query
    ↓
┌─────────────────────────────────────┐
│      RuleEngine (Orchestrator)      │
│  - Coordinates all rule matching    │
│  - Returns RuleMatch object         │
└─────────────────────────────────────┘
    ↓
    ├──→ IntentRules (What does user want?)
    │    - Detects: flight/hotel/train
    │    - Uses regex patterns
    │
    ├──→ EntityRules (What did user provide?)
    │    - Extracts: cities, dates, times, etc.
    │    - Uses patterns + CityService
    │
    └──→ SlotRules (What's missing?)
         - Infers: next_slot (from/to/date/etc.)
         - Uses slot order + keyword detection
    ↓
┌─────────────────────────────────────┐
│   SuggestionGenerator                │
│  - Creates suggestions based on      │
│    next_slot                        │
│  - Returns list of Suggestion objs  │
└─────────────────────────────────────┘
    ↓
Suggestions (with placeholder + entities)
```

---

## Component Details

### 1. RuleEngine (`src/parser/rule_engine.py`)

**Purpose**: Main orchestrator that coordinates all rule matching.

**Key Methods**:
- `match(query, context)` - Main entry point
- `_match_partial_intent(query)` - Handles incomplete queries like "I want to book a"
- `_match_city_or_from_first(query)` - Handles queries starting with cities

**Flow**:
1. Check cache (if enabled)
2. Try `IntentRules.match()` - detect intent
3. If intent found:
   - Extract entities via `EntityRules.extract()`
   - Infer next slot via `SlotRules.infer()`
   - Return `RuleMatch` object
4. If no intent:
   - Try `_match_partial_intent()` - suggest intents
   - Try `_match_city_or_from_first()` - handle city-first queries
5. Return `None` if nothing matches

**RuleMatch Object**:
```python
RuleMatch(
    intent='flight',           # or 'hotel', 'train', or None
    confidence=0.95,          # 0.0 to 1.0
    entities={                # Extracted entities
        'cities': ['Mumbai', 'Delhi'],
        'dates': ['today'],
        ...
    },
    next_slot='date',         # What to suggest next
    match_text='book a flight' # Matched pattern text
)
```

---

### 2. IntentRules (`src/parser/rules/intent_rules.py`)

**Purpose**: Detects what the user wants (flight/hotel/train).

**How it works**:
- Uses regex patterns with confidence scores
- Each intent has multiple patterns (more specific = higher confidence)
- Returns the best match above threshold (0.75)

**Example Patterns**:
```python
'flight': [
    (r'\b(book|want|need)\s+(a\s+)?(flight|fly|airplane)', 0.95),  # High confidence
    (r'\b(flight|fly|flying)\s+(from|to|on)', 0.90),
    (r'\b(flight|fly|flying)\b', 0.78),  # Lower confidence (standalone word)
]
```

**Example**:
- Query: `"book a flight"`
- Matches: Pattern 1 (confidence 0.95)
- Returns: `{'intent': 'flight', 'confidence': 0.95, 'match_text': 'book a flight'}`

**Special Cases**:
- Station codes (NDLS, BCT) → train intent
- City codes (BOM, DEL) → flight intent
- Partial queries ("I want to") → returns None (handled by RuleEngine)

---

### 3. EntityRules (`src/parser/rules/entity_rules.py`)

**Purpose**: Extracts entities from the query (cities, dates, times, passengers, etc.).

**How it works**:
- Uses regex patterns for each entity type
- Uses `CityService` for city matching (handles aliases, partial matches)
- Returns dictionary of extracted entities

**Entity Types**:
- **Cities**: Uses CityService (supports multi-word, aliases)
- **Dates**: Patterns for "today", "tomorrow", "DD/MM/YYYY", etc.
- **Times**: "morning", "afternoon", "9:30 AM", etc.
- **Passengers**: "2 passengers", "for 3 people"
- **Nights**: "3 nights", "for 2 nights"
- **Category**: "5-star", "luxury", "budget"
- **Return dates**: "return on", "coming back"
- And more...

**Example**:
```python
query = "flight from Mumbai to Delhi on today"
entities = {
    'cities': ['Mumbai', 'Delhi'],
    'dates': ['today'],
    'actions': [{'text': 'flight', 'type': 'book', 'raw': 'flight'}]
}
```

**City Extraction Logic**:
1. Uses `CityService.search_cities()` for fuzzy matching
2. Handles multi-word cities ("New York", "Sao Paulo")
3. Supports aliases (BOM → Mumbai, DEL → Delhi)
4. Extracts cities even without intent (for city-first queries)

---

### 4. SlotRules (`src/parser/rules/slot_rules.py`)

**Purpose**: Determines what information is missing (next slot to fill).

**Key Concepts**:

#### Slot Order
Each intent has a logical order of slots:
```python
'flight': ['intent', 'from', 'to', 'date', 'time', 'class', 'airline']
'hotel': ['intent', 'city', 'checkin', 'checkout', 'nights', 'guests', ...]
'train': ['intent', 'from', 'to', 'date', 'class', 'quota']
```

#### Optional Slots
Some slots are optional and suggested conditionally:
```python
'flight': ['return', 'passengers']  # Only if relevant
```

#### Keyword Detection
Keywords indicate a slot is being filled:
```python
'from': ['from', 'departure', 'leaving']
'to': ['to', 'destination', 'arrival']
'date': ['on', 'date', 'when', 'day']
```

**Inference Logic** (`infer()` method):

1. **Explicit Keyword Detection**: If user typed a keyword last, honor it
   - Example: "flight from Mumbai to" → next_slot = 'to' (user just typed "to")

2. **Priority for Flights/Trains**: "from" and "to" before "date"
   - Example: "flight from Mumbai" → next_slot = 'to' (not 'date')

3. **Slot Order**: Find first unfilled slot in order
   - Example: "flight from Mumbai to Delhi" → next_slot = 'date' (from and to filled)

4. **Optional Slots**: Check if optional slots should be suggested
   - Example: "flight from Mumbai to Delhi on today" → next_slot = 'return' (if round-trip context)

**Example**:
```python
query = "flight from Mumbai"
intent = "flight"
entities = {'cities': ['Mumbai']}
filled_slots = {'intent', 'from'}  # Intent detected, from city provided

# Slot order: ['intent', 'from', 'to', 'date', ...]
# First unfilled: 'to'
next_slot = 'to'
```

---

### 5. SuggestionGenerator (`src/parser/suggestion_generator.py`)

**Purpose**: Generates actual suggestions based on `next_slot`.

**How it works**:

1. **Placeholder** (ghost text): Shows what to type next
   - Example: `next_slot='from'` → placeholder: "from"
   - Example: `next_slot='date'` → placeholder: "on which date"

2. **Entity Suggestions**: Based on `next_slot` type
   - `next_slot='from'` or `'to'` → city suggestions
   - `next_slot='date'` → date suggestions ("today", "tomorrow", etc.)
   - `next_slot='class'` → class suggestions ("economy", "business")
   - And so on...

**Suggestion Object**:
```python
Suggestion(
    text='Mumbai',              # What to display
    entity_type='to',           # Slot name
    confidence=0.95,            # Match confidence
    selectable=True,            # Can user click it?
    is_placeholder=False       # Is this ghost text?
)
```

**Special Features**:

1. **City Prefix Detection**: If user types "New yo", suggests "New York"
   - Extracts partial city name from query
   - Filters city suggestions by prefix

2. **Exclusion Logic**: For "to" slot, excludes "from" city
   - Example: "flight from Mumbai to" → won't suggest Mumbai again

3. **Placeholder Mapping**: Different placeholders for different slots
   - `'from'` → "from"
   - `'date'` → "on which date"
   - `'checkin'` → "check-in date"

---

## Complete Flow Example

Let's trace through: **"book a flight from Mumbai"**

### Step 1: RuleEngine.match()
```python
query = "book a flight from Mumbai"
```

### Step 2: IntentRules.match()
```python
# Checks patterns
Pattern: r'\b(book|want|need)\s+(a\s+)?(flight|fly|airplane)'
Match: "book a flight" ✓
Confidence: 0.95

Returns: {
    'intent': 'flight',
    'confidence': 0.95,
    'match_text': 'book a flight'
}
```

### Step 3: EntityRules.extract()
```python
intent = 'flight'
query = "book a flight from Mumbai"

# Extract cities
CityService.search_cities("Mumbai") → ['Mumbai'] ✓

# Extract dates
No date patterns match

# Extract other entities
Actions: [{'text': 'flight', 'type': 'book', 'raw': 'flight'}]

Returns: {
    'cities': ['Mumbai'],
    'actions': [{'text': 'flight', 'type': 'book', 'raw': 'flight'}]
}
```

### Step 4: SlotRules.infer()
```python
intent = 'flight'
entities = {'cities': ['Mumbai'], ...}
query = "book a flight from Mumbai"

# Identify filled slots
filled_slots = {'intent', 'from'}  # Intent detected, "from Mumbai" detected

# Slot order: ['intent', 'from', 'to', 'date', ...]
# Check explicit keywords: query ends with "Mumbai", not a keyword
# Priority: 'from' filled, check 'to'
# 'to' not in filled_slots → return 'to'

Returns: 'to'
```

### Step 5: RuleMatch Created
```python
RuleMatch(
    intent='flight',
    confidence=0.95,
    entities={'cities': ['Mumbai'], 'actions': [...]},
    next_slot='to',
    match_text='book a flight'
)
```

### Step 6: SuggestionGenerator.generate()
```python
rule_match = RuleMatch(...)
next_slot = 'to'
entities = {'cities': ['Mumbai']}

# 1. Add placeholder
placeholder = "to where"  # From PLACEHOLDER_MAP['to']

# 2. Generate entity suggestions
# next_slot is 'to', so get city suggestions
# Exclude 'from' city (Mumbai)
city_suggestions = CityService.get_all_cities(exclude='Mumbai')
# Returns: ['Delhi', 'Bangalore', 'Chennai', ...]

# 3. Create Suggestion objects
suggestions = [
    Suggestion(text="to where", entity_type='to', is_placeholder=True),  # Ghost text
    Suggestion(text="Delhi", entity_type='to', selectable=True),
    Suggestion(text="Bangalore", entity_type='to', selectable=True),
    ...
]
```

### Step 7: Final Output
```python
# API returns:
{
    'suggestions': [
        {'text': 'to where', 'entity_type': 'to', 'is_placeholder': True},
        {'text': 'Delhi', 'entity_type': 'to', 'selectable': True},
        {'text': 'Bangalore', 'entity_type': 'to', 'selectable': True},
        ...
    ],
    'intent': 'flight',
    'next_slot': 'to',
    'source': 'rule_based',
    'latency_ms': 12.5
}
```

---

## Key Concepts

### 1. Incremental Parsing
The parser works **as the user types**, not just at the end:
- "book" → suggests intents
- "book a flight" → suggests "from"
- "book a flight from Mumbai" → suggests "to"
- "book a flight from Mumbai to Delhi" → suggests "date"

### 2. Confidence Scores
- Higher confidence = more certain match
- Threshold: 0.75 (below this, no match)
- Used to rank suggestions

### 3. Slot Inference Priority
1. **Explicit keywords** (user just typed "to" → suggest cities)
2. **Required slots in order** (from → to → date)
3. **Optional slots** (return date, passengers)

### 4. City-First Queries
Handles queries starting with cities:
- "Mumbai" → suggests "to"
- "from Mumbai" → suggests "to"
- "Mumbai to Delhi" → suggests "intent"

### 5. Partial Intent Matching
Handles incomplete queries:
- "I want to book a" → suggests intents (flight/hotel/train)
- "weekday on" → suggests date slot

### 6. Entity Extraction Without Intent
Can extract cities even without intent:
- "Mumbai to Delhi" → extracts both cities, suggests intent

### 7. Multi-word City Support
- Handles "New York", "Sao Paulo"
- Prefix detection: "New yo" → suggests "New York"
- Removes multi-word prefix on Tab completion

### 8. Caching
- Results cached for 5 minutes (300 seconds)
- Speeds up repeated queries
- Can be disabled for testing

---

## Common Patterns

### Pattern 1: Full Intent Query
```
"book a flight from Mumbai to Delhi on today"
→ Intent: flight
→ Entities: cities=[Mumbai, Delhi], dates=[today]
→ Next slot: time/class/airline (optional)
```

### Pattern 2: City-First Query
```
"Mumbai"
→ Intent: None
→ Entities: cities=[Mumbai]
→ Next slot: to
```

### Pattern 3: Partial Query
```
"I want to book a"
→ Intent: None
→ Entities: {}
→ Next slot: intent
→ Suggestions: ["flight", "hotel", "train"]
```

### Pattern 4: Keyword-Only Query
```
"from Mumbai to"
→ Intent: None
→ Entities: cities=[Mumbai]
→ Next slot: to (explicit keyword)
→ Suggestions: destination cities
```

### Pattern 5: Date Slot Query
```
"weekday on"
→ Intent: None
→ Entities: {}
→ Next slot: date
→ Suggestions: ["today", "tomorrow", "this weekend", ...]
```

---

## Error Handling

1. **No Match**: Returns `None` → triggers LLM fallback
2. **Empty Query**: Returns `None` immediately
3. **Invalid Entities**: EntityRules handles gracefully (returns empty dict)
4. **Cache Miss**: Falls back to rule matching
5. **LLM Fallback**: When no rules match, uses LLM service

---

## Performance Considerations

1. **Caching**: Results cached for 5 minutes
2. **CityService**: Uses efficient prefix matching
3. **Pattern Matching**: Regex compiled once
4. **Lazy Loading**: Entities loaded on first use
5. **Early Returns**: Stops at first high-confidence match

---

## Extension Points

To add new functionality:

1. **New Intent**: Add patterns to `IntentRules.INTENT_PATTERNS`
2. **New Entity Type**: Add patterns to `EntityRules` and extraction method
3. **New Slot**: Add to `SlotRules.SLOT_ORDER` and `SLOT_KEYWORDS`
4. **New Suggestions**: Add method to `SuggestionGenerator` (e.g., `_get_X_suggestions()`)

---

This parser is designed to be **flexible**, **extensible**, and **fast** for real-time autocomplete scenarios.
