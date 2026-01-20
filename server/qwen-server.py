from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import time
import os
import re
import logging
from typing import Dict, Tuple, Optional, Set
from llama_cpp import Llama
import uvicorn
import redis
from cache import QueryCache


def extract_present_entities(query: str) -> Tuple[Set[str], str]:
    """Extract entities already present in the query and identify LOB."""
    present = set()
    query_lower = query.lower()
    lob = ""

    # Detect LOB
    if "flight" in query_lower:
        lob = "flight"
        # Check for source city
        if re.search(r"from\s+(\w+)", query_lower):
            present.add("source")
        # Check for destination city
        if re.search(r"to\s+(\w+)", query_lower):
            present.add("destination")
        # Check for date - IMPROVED to match formats like "Mon, Jan 19", "tomorrow", "next Friday"
        if re.search(
            r"(on\s+(\d+|january|february|march|april|may|june|july|august|september|october|november|december|sunday|monday|tuesday|wednesday|thursday|friday|saturday|mon|tue|wed|thu|fri|sat|sun|tomorrow|this\s+\w+)|(\d{1,2})\s+(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)|on\s+(mon|tue|wed|thu|fri|sat|sun)[,.]?\s+(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec|january|february|march|april|may|june|july|august|september|october|november|december)[,.]?\s+\d+|\btomorrow\b|next\s+(week|monday|tuesday|wednesday|thursday|friday|saturday|sunday|month))",
            query_lower,
        ):
            present.add("date")
        # Check for passengers - IMPROVED REGEX
        if re.search(
            r"(for\s+\d+\s+(passengers?|people|adults?|travelers?)|with\s+(my|family)|\d+\s+(passengers?|people|adults?|travelers?))",
            query_lower,
        ):
            present.add("passengers")
        # Check for class
        if re.search(r"(economy|business|first\s+class|premium)", query_lower):
            present.add("class")
        # Check for time of day
        if re.search(r"(morning|afternoon|evening|night)", query_lower):
            present.add("time")

    elif "hotel" in query_lower:
        lob = "hotel"
        # Check for location
        if re.search(r"in\s+(\w+)", query_lower):
            present.add("location")
        # Check for check-in date - IMPROVED to match formats like "Mon, Jan 19", "tomorrow", "next week"
        if re.search(
            r"(on\s+(\d+|january|february|march|april|may|june|july|august|september|october|november|december|sunday|monday|tuesday|wednesday|thursday|friday|saturday|mon|tue|wed|thu|fri|sat|sun|tomorrow|this\s+\w+)|(\d{1,2})\s+(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)|on\s+(mon|tue|wed|thu|fri|sat|sun)[,.]?\s+(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec|january|february|march|april|may|june|july|august|september|october|november|december)[,.]?\s+\d+|\btomorrow\b|next\s+(week|monday|tuesday|wednesday|thursday|friday|saturday|sunday|month)|check[-\s]?in\s+on|arriving\s+on|from\s+(\d+|january|february|march|april|may|june|july|august|september|october|november|december))",
            query_lower,
        ):
            present.add("check-in")
        # Check for nights/duration
        if re.search(r"for\s+(\d+)\s+(nights?|days?)", query_lower):
            present.add("nights")
        # Check for guests
        if re.search(r"(for|with)\s+(\d+)\s+(guests?|people)", query_lower):
            present.add("guests")
        # Check for room type
        if re.search(r"(single|double|suite|deluxe)\s+(room)?", query_lower):
            present.add("room")
        # Check for category
        if re.search(r"((\d+)[-\s]?star|budget|luxury)", query_lower):
            present.add("category")

    elif "train" in query_lower:
        lob = "train"
        # Check for source
        if re.search(r"from\s+(\w+)", query_lower):
            present.add("source")
        # Check for destination
        if re.search(r"to\s+(\w+)", query_lower):
            present.add("destination")
        # Check for date - IMPROVED to match formats like "Mon, Jan 19", "tomorrow", "next Friday"
        if re.search(
            r"(on\s+(\d+|january|february|march|april|may|june|july|august|september|october|november|december|sunday|monday|tuesday|wednesday|thursday|friday|saturday|mon|tue|wed|thu|fri|sat|sun|tomorrow|this\s+\w+)|(\d{1,2})\s+(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)|on\s+(mon|tue|wed|thu|fri|sat|sun)[,.]?\s+(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec|january|february|march|april|may|june|july|august|september|october|november|december)[,.]?\s+\d+|\btomorrow\b|next\s+(week|monday|tuesday|wednesday|thursday|friday|saturday|sunday|month))",
            query_lower,
        ):
            present.add("date")
        # Check for class
        if re.search(r"(ac|non[-\s]?ac|sleeper|(\d+)ac|first\s+ac)", query_lower):
            present.add("class")
        # Check for passengers
        if re.search(r"(for\s+(\d+)|(\d+)\s+(passengers|people))", query_lower):
            present.add("passengers")
        # Check for time
        if re.search(r"(morning|afternoon|evening|night)", query_lower):
            present.add("time")

    elif "holiday" in query_lower or "package" in query_lower:
        lob = "holiday"
        # Check for destination
        if re.search(r"to\s+(\w+)", query_lower):
            present.add("destination")
        # Check for start date
        if re.search(
            r"(starting\s+on|from\s+(\d+|january|february|march|april|may|june|july|august|september|october|november|december))",
            query_lower,
        ):
            present.add("start-date")
        # Check for duration
        if re.search(r"for\s+(\d+)\s+(days?|weeks?)", query_lower):
            present.add("duration")
        # Check for travelers
        if re.search(r"for\s+(\d+)\s+(people|travelers)", query_lower):
            present.add("travelers")
        # Check for theme
        if re.search(
            r"(honeymoon|adventure|beach|family|mountains?|romantic|cultural)",
            query_lower,
        ):
            present.add("theme")
        # Check for budget
        if re.search(r"(under\s+\d+|budget|luxury)", query_lower):
            present.add("budget")

    return present, lob


def filter_suggestions(suggestions: str, present_entities: Set[str], lob: str) -> str:
    """Filter out suggestions that match present entities."""
    if not suggestions or not lob:
        return suggestions

    # Split suggestions
    suggestion_list = [s.strip() for s in suggestions.split("|") if s.strip()]
    filtered = []

    # Define entity mappings for each LOB
    entity_mapping = {
        "flight": {
            "source": ["from [source]", "from where"],
            "destination": ["to [destination]", "to where"],
            "date": ["on [date]", "date"],
            "passengers": [
                "for [passengers]",
                "[passengers]",
                "passengers",
                "how many",
            ],
            "class": ["in [cabin class]", "in [class]", "cabin"],
            "time": ["in [time]", "time of day"],
        },
        "hotel": {
            "location": ["in [location]", "location", "city"],
            "check-in": ["on [check-in date]", "check-in"],
            "nights": ["for [nights]", "[nights]", "nights"],
            "guests": ["with [guests]", "[guests]", "guests"],
            "category": ["[category]", "star", "budget", "luxury"],
        },
        "train": {
            "source": ["from [source]", "from where"],
            "destination": ["to [destination]", "to where"],
            "date": ["on [date]", "date"],
            "class": ["in [class]", "class", "ac", "sleeper"],
            "passengers": ["for [passengers]", "[passengers]", "passengers"],
            "time": ["in [time]", "time"],
        },
        "holiday": {
            "destination": ["to [destination]", "destination"],
            "start-date": ["starting on [date]", "starting"],
            "duration": ["for [days]", "[days]", "days", "duration"],
            "travelers": ["for [travelers]", "travelers"],
            "theme": ["[theme]", "theme", "honeymoon", "adventure"],
            "budget": ["[budget]", "budget", "under"],
        },
    }

    mapping = entity_mapping.get(lob, {})

    for suggestion in suggestion_list:
        suggestion_lower = suggestion.lower()
        should_include = True

        # Check if this suggestion matches a present entity
        for entity_type in present_entities:
            if entity_type in mapping:
                patterns = mapping[entity_type]
                for pattern in patterns:
                    if pattern.lower() in suggestion_lower:
                        should_include = False
                        break
            if not should_include:
                break

        if should_include and suggestion:
            filtered.append(suggestion)

    # Return filtered suggestions or empty if none left
    return "|".join(filtered) if filtered else ""


# FastAPI app
app = FastAPI(title="Qwen LLM Server", version="1.0.0")

# CORS middleware to allow cross-origin requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify allowed origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global model instance
llm_instance = None

# Global cache instance
query_cache: Optional[QueryCache] = None

# Cache statistics
cache_stats = {
    "hits": 0,
    "misses": 0,
    "total_latency_saved_ms": 0.0,
}

MODEL_PATH = os.getenv("MODEL_PATH", "qwen2.5-coder-3b-instruct-fp16.gguf")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Request/Response models
class LLMRequest(BaseModel):
    question: str


class LLMResponse(BaseModel):
    response: str
    latency_ms: float


def load_model(use_metal: bool = True, n_ctx: int = 1300):
    """Load the model using llama.cpp."""
    print(f"Loading model: {MODEL_PATH}")

    if not os.path.exists(MODEL_PATH):
        print(f"ERROR: Model file not found: {MODEL_PATH}")
        print("\nTo download a pre-converted model:")
        print(
            "  huggingface-cli download ggml-org/Qwen2.5-Coder-1.5B-Q8_0-GGUF --local-dir ./models"
        )
        print(
            "  Then set MODEL_PATH environment variable or update MODEL_PATH in this script"
        )
        raise FileNotFoundError(f"Model file not found: {MODEL_PATH}")

    print("This may take a while on first run...")

    start_time = time.time()

    # Check if Metal is available (Apple Silicon)
    if use_metal:
        try:
            import platform

            if platform.system() == "Darwin" and platform.machine() == "arm64":
                n_gpu_layers = -1  # Use all GPU layers (Metal)
                print("  Using Metal (Apple Silicon GPU) acceleration")
            else:
                n_gpu_layers = 0  # CPU only
                print("  Using CPU (Metal not available on this system)")
        except:
            n_gpu_layers = 0
            print("  Using CPU")
    else:
        n_gpu_layers = 0
        print("  Using CPU (Metal disabled)")

    # Initialize llama.cpp model
    llm = Llama(
        model_path=MODEL_PATH,
        n_ctx=1300,  # Context window size
        n_threads=None,  # Auto-detect CPU threads
        n_gpu_layers=n_gpu_layers,  # GPU layers (-1 = all, 0 = CPU only)
        verbose=False,
        # Memory optimizations
        use_mmap=True,  # Memory mapping for faster loading
        use_mlock=False,  # Don't lock memory (allows swapping if needed)
        n_batch=512,  # Batch size for prompt processing
        # Additional performance settings
        n_parts=1,  # Number of parts to split model into
        seed=-1,  # Random seed (-1 = random)
    )

    load_time = time.time() - start_time
    print(f"Model loaded in {load_time:.2f} seconds")

    return llm


def run_inference(
    llm, question: str, max_tokens: int = 15, use_chat_template: bool = True
) -> Tuple[str, float, Dict]:
    """Run optimized inference with llama.cpp."""

    prompt = f"""<|im_start|>system
You are a Travel Autocomplete Assistant. Analyze incomplete travel queries and suggest the SINGLE NEXT most important missing entity.
 
CRITICAL RULE: First identify what entities are ALREADY in the query. Then suggest ONLY THE NEXT MOST IMPORTANT missing entity in the logical order. Never suggest entities already present.
 
DOMAIN: Flights, Hotels, Trains, Holidays
 
MODE: Single entity suggestion (suggest only ONE entity at a time)
 
ENTITY ORDER BY LOB:
 
FLIGHTS: from [source] → to [destination] → on [date] → return [date] → for [passengers] → in [class] → in [time]

HOTELS: in [location] → on [check-in date] → for [nights] → with [guests] → [category]

TRAINS: from [source] → to [destination] → on [date] → in [class] → for [passengers] → in [time]

HOLIDAYS: to [destination] → starting on [date] → for [days] → for [travelers] → [theme] → [budget]
 
HOW TO DETECT PRESENT ENTITIES:
 
FLIGHTS:

- source: "from [source]" or "[source]" before "to"

- destination: "to [destination]" or "[destination]" after "from X to"

- date: "on [date]", "on [day]", "this [day]", "tomorrow"

- passengers: "[number] passengers", "for [number]", "family", "for my [number]"

- class: "economy", "business", "first class"

- time: "morning", "afternoon", "evening", "night"
 
make sure no other entities are present other than above for flights.
 
HOTELS:

- location: "in [city]"

- check-in: "on [date]", "check-in on", "arriving on"

- nights: "for [number] nights", "for [number] days"

- guests: "for [number] guests", "with [number] people"

- category: "[number]-star", "budget", "luxury", "suite"
 
make sure no other entities are present other than above for hotels.
 
TRAINS:

- source: "from [source]"

- destination: "to [destination]" 

- date: "on [date]", "on [day]"

- class: "AC", "Non-AC", "Sleeper", "[number]AC"

- passengers: "for [number] passengers"

- time: "morning", "afternoon", "evening", "night"
 
make sure no other entities are present other than above for trains.
 
HOLIDAYS:

- destination: "to [destination]"

- start date: "starting on", "from [date]"

- duration: "for [number] days", "for a week"

- travelers: "for [number] people", "for [number] travelers"

- theme: "honeymoon", "adventure", "beach", "family"

- budget: "under [amount]", "budget", "luxury"
 
make sure no other entities are present other than above for holidays.
 
PROCESS:

1. Identify LOB (flight/hotel/train/holiday)

2. List entities ALREADY PRESENT in query

3. Identify the NEXT MOST IMPORTANT missing entity in the logical order

4. Suggest ONLY that single entity

5. Verify: the suggested entity is not already present
 
OUTPUT FORMAT: Single entity only. Example: "to [destination]" or "on [date]" or "for [passengers]"
 
EXAMPLES:
 
Query: "book a flight"

Present: none

Missing: destination, source, date

Next: destination (first in order)

Output: "to [destination]"

Query: "flight from city1"

Present: source (city1)

Missing: destination, date, passengers

Next: destination (next in order after source)

Output: "to [destination]"

NOT: "from [source]" (already present)
 
Query: "flight from city1 to city2"

Present: source (city1), destination (city2)

Missing: date, passengers, class

Next: date (next in order)

Output: "on [date]"

NOT: "from [source]" or "to [destination]" (both present)

Query: "hotel in city1"

Present: location (city1)

Missing: check-in date, nights, guests

Next: check-in date (next in order after location)

Output: "on [check-in date]"

NOT: "in [location]" (already present)
 
Query: "hotel in city1 for 3 nights"

Present: location (city1), nights (3 nights)

Missing: check-in date, guests, category

Next: check-in date (next most important)

Output: "on [check-in date]"

NOT: "in [location]" or "for [nights]" (both present)
 
Query: "flight to city1"

Present: destination (city1)

Missing: source, date, passengers

Next: source (should come before destination in order)

Output: "from [source]"

NOT: "to [destination]" (already present)
 
Query: "i want to"

Present: none

Missing: LOB, destination, source, date

Next: LOB type (must identify first)

Output: "book a [flight/hotel/train/holiday]"

Query: "3 people"

Present: passengers

Missing: LOB, destination, date
 
RULES:

- Suggest ONLY ONE entity (the next most important)

- Never repeat present entities

- Follow logical order and suggest the next missing one

- Output single entity only

- Use natural language placeholders like "to [destination]"

- Be concise and direct
 <|im_end|>
    <|im_start|>user
    {question}
    <|im_end|>
    <|im_start|>assistant
    """

    # Run inference and measure time
    start_time = time.time()

    output = llm(
        prompt,
        max_tokens=20,
        temperature=0.0,
        top_p=1.0,
        top_k=1,
        repeat_penalty=1.0,
        stop=["<|im_end|>"],
        echo=False,
    )

    inference_time = time.time() - start_time

    # Extract response
    response = output["choices"][0]["text"].strip()

    # Debug: print full output if response is empty or just stop token
    if not response or len(response) < 2:
        print(f"DEBUG - Full output: {output}")
        print(f"DEBUG - Prompt length: {len(prompt)}")
        print(f"DEBUG - Response length: {len(response)}")
        # Try without chat template if it failed
        if use_chat_template and len(response) < 2:
            print("DEBUG - Retrying with simpler prompt format...")
            return run_inference(llm, question, max_tokens, use_chat_template=False)

    # Post-process: Extract present entities and filter suggestions
    present_entities, lob = extract_present_entities(question)

    # DEBUG: Print what was detected
    print(f"DEBUG - Query: '{question}'")
    print(f"DEBUG - LOB: {lob}")
    print(f"DEBUG - Present entities: {present_entities}")
    print(f"DEBUG - Raw model response: '{response}'")

    # Ensure only single suggestion (take first if multiple)
    if "|" in response:
        response = response.split("|")[0].strip()
        print(f"DEBUG - After single suggestion enforcement: '{response}'")

    # Map verbose LLM responses to clean UI-friendly labels
    response_mapping = {
        # Flights
        "from [source]": "from",
        "to [destination]": "to",
        "destination": "to",
        "on [date]": "date",
        "return [date]": "return",
        "passengers": "passengers",
        "for [passengers]": "passengers",
        "in [class]": "class",
        "in [cabin class]": "class",
        "in [time]": "time",
        # Hotels
        "in [location]": "city",
        "location": "city",
        "on [check-in date]": "checkin",
        "for [nights]": "nights",
        "nights": "nights",
        "guests": "guests",
        "with [guests]": "guests",
        "[category]": "category",
        "check-out [date]": "checkout",
        # Trains (same as flights for most fields)
        # Already covered in flights section
        # Holidays
        "starting on [date]": "date",
        "for [days]": "nights",
        "for [travelers]": "guests",
        "[theme]": "theme",
        "[budget]": "budget",
        # Fallback options
        "meal [preference]": "meal",
        "berth [preference]": "berth",
        # LOB suggestions (keep as-is)
        "book a [flight/hotel/train/holiday]": "intent",
    }

    # Apply mapping to response
    mapped_response = response_mapping.get(response, "None")
    if mapped_response != response:
        print(f"DEBUG - Mapped '{response}' to '{mapped_response}'")
        response = mapped_response

    return response, inference_time


def warmup(llm):
    """Warmup run to initialize kernels and cache."""
    print("Warming up model...")
    try:
        run_inference(llm, "test")
        # Run a second time to ensure everything is cached
        run_inference(llm, "test")
        print("Warmup complete")
    except Exception as e:
        print(f"Warmup warning: {e}")


@app.on_event("startup")
async def startup_event():
    """Load model and initialize cache on server startup."""
    global llm_instance, query_cache

    # Initialize Redis cache
    try:
        cache_enabled = os.getenv("CACHE_ENABLED", "true").lower() == "true"
        if cache_enabled:
            redis_client = redis.Redis(
                host=os.getenv("REDIS_HOST", "localhost"),
                port=int(os.getenv("REDIS_PORT", 6379)),
                db=int(os.getenv("REDIS_DB", 0)),
                password=os.getenv("REDIS_PASSWORD", None),
                decode_responses=True,  # Auto-decode bytes to strings
                socket_connect_timeout=5,  # 5 second timeout
                socket_timeout=5,
            )

            # Test connection
            redis_client.ping()
            logger.info("Redis connection established")

            # Initialize cache
            query_cache = QueryCache(
                redis_client=redis_client,
                ttl_seconds=int(os.getenv("CACHE_TTL_SECONDS", 3600)),
                enabled=True,
            )
            logger.info("Query cache initialized")
        else:
            logger.info("Cache is disabled (CACHE_ENABLED=false)")
            query_cache = None

    except redis.ConnectionError as e:
        logger.warning(f"Failed to connect to Redis: {e}")
        logger.warning("Continuing without cache (fallback mode)")
        query_cache = None
    except Exception as e:
        logger.warning(f"Error initializing cache: {e}")
        logger.warning("Continuing without cache (fallback mode)")
        query_cache = None

    # Load model
    try:
        llm_instance = load_model(use_metal=True, n_ctx=1300)
        warmup(llm_instance)
        logger.info("Server ready!")
    except Exception as e:
        logger.error(f"Failed to load model: {e}")
        raise


@app.get("/")
async def root():
    """Health check endpoint."""
    return {
        "status": "ok",
        "model_loaded": llm_instance is not None,
        "model_path": MODEL_PATH,
    }


@app.post("/llm", response_model=LLMResponse)
async def llm_endpoint(request: LLMRequest):
    """
    LLM inference endpoint with caching.

    Accepts a question and returns the model's response with latency information.
    Checks cache first, runs inference if cache miss, and stores result in cache.
    """
    if llm_instance is None:
        raise HTTPException(status_code=503, detail="Model not loaded")

    if not request.question or not request.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty")

    # Check cache first
    if query_cache is not None:
        cached_result = query_cache.get(request.question)
        if cached_result is not None:
            # Cache hit
            cached_response, cached_latency_ms = cached_result
            cache_stats["hits"] += 1
            logger.debug(f"Cache hit for query: {request.question[:50]}...")
            return LLMResponse(
                response=cached_response,
                latency_ms=cached_latency_ms,
            )

    # Cache miss - run inference
    cache_stats["misses"] += 1
    logger.debug(f"Cache miss for query: {request.question[:50]}...")

    try:
        start_time = time.time()
        response, latency = run_inference(
            llm_instance,
            request.question,
        )
        inference_time_ms = latency * 1000  # Convert to milliseconds

        # Store in cache
        if query_cache is not None:
            query_cache.set(request.question, response, inference_time_ms)

        return LLMResponse(
            response=response,
            latency_ms=inference_time_ms,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Inference error: {str(e)}")


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy", "model_loaded": llm_instance is not None}


@app.get("/cache/stats")
async def cache_stats_endpoint():
    """
    Get cache statistics.

    Returns cache hit/miss statistics and Redis information.
    """
    total_requests = cache_stats["hits"] + cache_stats["misses"]
    hit_rate = (
        (cache_stats["hits"] / total_requests * 100) if total_requests > 0 else 0.0
    )

    stats = {
        "cache_enabled": query_cache is not None and query_cache.enabled,
        "hits": cache_stats["hits"],
        "misses": cache_stats["misses"],
        "total_requests": total_requests,
        "hit_rate_percent": round(hit_rate, 2),
    }

    # Add Redis stats if cache is enabled
    if query_cache is not None:
        redis_stats = query_cache.get_stats()
        stats.update(redis_stats)

    return stats


@app.post("/cache/clear")
async def cache_clear_endpoint():
    """
    Clear all cache entries.

    Returns success status and number of entries cleared.
    """
    if query_cache is None:
        return {
            "success": False,
            "message": "Cache is not enabled or not connected",
        }

    try:
        # Get count before clearing
        stats_before = query_cache.get_stats()
        cache_keys_before = stats_before.get("cache_keys", 0)

        # Clear cache
        success = query_cache.clear()

        if success:
            # Reset statistics
            cache_stats["hits"] = 0
            cache_stats["misses"] = 0
            cache_stats["total_latency_saved_ms"] = 0.0

            return {
                "success": True,
                "message": f"Cleared {cache_keys_before} cache entries",
                "entries_cleared": cache_keys_before,
            }
        else:
            return {
                "success": False,
                "message": "Failed to clear cache",
            }
    except Exception as e:
        logger.error(f"Error clearing cache: {e}")
        return {
            "success": False,
            "message": f"Error clearing cache: {str(e)}",
        }


@app.get("/cache/info")
async def cache_info_endpoint():
    """
    Get detailed Redis cache information.

    Returns Redis server information including memory usage, connected clients, etc.
    """
    if query_cache is None:
        return {
            "cache_enabled": False,
            "message": "Cache is not enabled or not connected",
        }

    try:
        redis_info = query_cache.redis_client.info()
        cache_info = query_cache.get_stats()

        return {
            "cache_enabled": True,
            "redis_connected": query_cache.is_connected(),
            "cache_stats": cache_info,
            "redis_info": {
                "version": redis_info.get("redis_version", "N/A"),
                "uptime_seconds": redis_info.get("uptime_in_seconds", 0),
                "connected_clients": redis_info.get("connected_clients", 0),
                "used_memory_human": redis_info.get("used_memory_human", "N/A"),
                "used_memory_peak_human": redis_info.get(
                    "used_memory_peak_human", "N/A"
                ),
                "maxmemory_human": redis_info.get("maxmemory_human", "N/A"),
                "maxmemory_policy": redis_info.get("maxmemory_policy", "N/A"),
            },
        }
    except Exception as e:
        logger.error(f"Error getting cache info: {e}")
        return {
            "cache_enabled": True,
            "error": str(e),
        }


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
