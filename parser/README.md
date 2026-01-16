# Hybrid Rule-Based Parser with LLM Fallback

A hybrid suggestion engine that uses rule-based parsing for fast, deterministic suggestions, falling back to LLM only when no rules match. Designed for real-time suggestions as the user types, with extensible architecture for future LLM integration.

## Features

- **Rule-based parsing**: Fast pattern matching for intent detection, entity extraction, and slot inference
- **Real-time suggestions**: Provides word suggestions as user types
- **LLM fallback**: Placeholder for LLM integration when no rules match
- **Multi-intent support**: Handles flights, hotels, and trains
- **Extensible architecture**: Easy to add new rules and patterns

## Architecture

The system consists of:

1. **Rule Engine**: Orchestrates rule matching across intent, entity, and slot rules
2. **Intent Rules**: Detects user intent (flight/hotel/train)
3. **Entity Rules**: Extracts entities (cities, dates, times, etc.)
4. **Slot Rules**: Determines what entity should come next
5. **Suggestion Generator**: Generates suggestions based on matched rules
6. **LLM Fallback**: Placeholder for LLM integration

## Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Run the API server:
```bash
python -m src.api.suggestion_api
```

Or using uvicorn directly:
```bash
uvicorn src.api.suggestion_api:app --reload
```

## Usage

### API Endpoint

**POST /suggest**

Request:
```json
{
  "query": "I want to book a flight",
  "cursor_position": 25,
  "context": {}
}
```

Response:
```json
{
  "suggestions": [
    {
      "text": "from",
      "entity_type": "from",
      "confidence": 0.95
    },
    {
      "text": "to",
      "entity_type": "to",
      "confidence": 0.95
    }
  ],
  "intent": "flight",
  "next_slot": "from",
  "source": "rule_based",
  "latency_ms": 12.5
}
```

### Example Queries

- "I want to book a flight" → suggests: "from", "to", "date"
- "Book hotel in" → suggests: city names
- "Train from Mumbai" → suggests: "to", destination cities
- "Flight from Delhi to" → suggests: destination cities

## Project Structure

```
markov_chain_test/
├── src/
│   ├── parser/
│   │   ├── rule_engine.py          # Main rule matching engine
│   │   ├── entity_extractor.py     # Entity extraction
│   │   ├── slot_inferencer.py      # Slot inference
│   │   ├── suggestion_generator.py # Suggestion generation
│   │   └── rules/
│   │       ├── intent_rules.py     # Intent detection rules
│   │       ├── entity_rules.py     # Entity extraction rules
│   │       ├── slot_rules.py       # Slot inference rules
│   │       └── pattern_matcher.py # Pattern matching utilities
│   ├── llm/
│   │   ├── llm_fallback.py         # LLM fallback service
│   │   └── llm_client.py           # LLM API client (future)
│   ├── data/
│   │   └── entities/
│   │       ├── cities.json         # City/airport data
│   │       ├── airlines.json       # Airline names
│   │       └── hotels.json         # Hotel chains/brands
│   ├── api/
│   │   └── suggestion_api.py       # FastAPI endpoint
│   └── utils/
│       ├── text_processor.py       # Text normalization
│       └── cache.py                # Response caching
├── tests/
├── requirements.txt
└── README.md
```

## Supported Intents

### Flight
- Slots: intent → from → to → date → time → class → airline
- Example: "I want to book a flight from Mumbai to Delhi on tomorrow"

### Hotel
- Slots: intent → city → checkin → checkout → guests → rooms
- Example: "Book hotel in Bangalore for 2 guests"

### Train
- Slots: intent → from → to → date → class → quota
- Example: "Train from Mumbai to Delhi on next Monday"

## Rule Development

Rules are defined in Python code but can be extended to support JSON/YAML configuration. Current rules include:

- **Intent patterns**: Regex patterns for detecting flight/hotel/train intents
- **Entity patterns**: Patterns for extracting cities, dates, times, classes
- **Slot keywords**: Keywords that indicate which slot is being filled

## Future Enhancements

- [ ] LLM integration for complex queries
- [ ] Personalization based on user history
- [ ] Multi-language support
- [ ] Advanced entity recognition (NER)
- [ ] Rule configuration via JSON/YAML
- [ ] Analytics and metrics enrichment

## Testing

### Automated Tests

Run unit tests:
```bash
pytest tests/
```

### Manual Testing

#### Method 1: Real-Time Live Typing (Best for Testing)

See suggestions update **as you type** (character by character, no Enter needed):

```bash
python test_live.py
```

Features:
- Suggestions update in real-time as you type
- Press **Tab** to select the first suggestion
- Press **Backspace** to delete
- Press **Enter** to complete and start a new query
- Works on macOS/Linux terminals

#### Method 2: Interactive Test Script

Test queries by entering them one at a time (press Enter after each):

```bash
# Interactive mode - enter queries one by one
python test_interactive.py

# Or test a specific query
python test_interactive.py "I want to book a flight from Mumbai"
```

**Note**: This now properly recognizes partial queries like "I want to book a" and suggests intents!

#### Method 2: Test via API

1. Start the API server:
```bash
uvicorn src.api.suggestion_api:app --reload
```

2. In another terminal, test queries:
```bash
# Interactive mode
python test_api.py

# Or test a specific query
python test_api.py "Book hotel in Delhi"
```

3. Or use curl:
```bash
curl -X POST "http://localhost:8000/suggest" \
  -H "Content-Type: application/json" \
  -d '{"query": "I want to book a flight", "cursor_position": 25}'
```

4. Or use the API docs:
   - Open http://localhost:8000/docs in your browser
   - Use the interactive Swagger UI to test queries

#### Method 3: Python REPL

```python
from src.parser.rule_engine import RuleEngine
from src.parser.suggestion_generator import SuggestionGenerator

engine = RuleEngine()
generator = SuggestionGenerator()

query = "I want to book a flight"
match = engine.match(query)

if match:
    print(f"Intent: {match.intent}")
    print(f"Next Slot: {match.next_slot}")
    suggestions = generator.generate(match)
    for s in suggestions:
        print(f"  - {s.text}")
```

## Performance

- **Rule-based latency**: <50ms (target)
- **LLM fallback latency**: <500ms (target, when implemented)
- **Caching**: Enabled for rule matches (5-minute TTL)

## License

MIT
