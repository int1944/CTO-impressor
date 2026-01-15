#!/usr/bin/env python3
"""
Optimized Latency Test using llama.cpp for Qwen 2.5 Coder 1.5B
Uses llama-cpp-python for faster inference compared to Hugging Face.
"""

import time
import psutil
import os
from typing import Dict, Tuple

try:
    from llama_cpp import Llama
except ImportError:
    print("ERROR: llama-cpp-python is not installed.")
    print("Install it with: CMAKE_ARGS='-DGGML_METAL=on' pip install llama-cpp-python")
    exit(1)

# Model configuration
# You can download pre-converted GGUF models from Hugging Face:
# - ggml-org/Qwen2.5-Coder-1.5B-Q8_0-GGUF (8-bit, ~1.65GB, recommended)
# - MaziyarPanahi/Qwen2.5-Coder-1.5B-GGUF (multiple quantizations)
MODEL_PATH = os.getenv("MODEL_PATH", "qwen2.5-coder-3b-instruct-fp16.gguf")

def get_memory_usage() -> Dict[str, float]:
    """Get current memory usage in MB."""
    process = psutil.Process(os.getpid())
    mem_info = process.memory_info()
    return {
        "rss": mem_info.rss / 1024 / 1024,
        "vms": mem_info.vms / 1024 / 1024,
    }

def get_cpu_usage() -> float:
    """Get current CPU usage percentage."""
    return psutil.cpu_percent(interval=0.1)

def load_model(use_metal: bool = True, n_ctx: int = 512):
    """Load the model using llama.cpp."""
    print(f"Loading model: {MODEL_PATH}")
    
    if not os.path.exists(MODEL_PATH):
        print(f"ERROR: Model file not found: {MODEL_PATH}")
        print("\nTo download a pre-converted model:")
        print("  huggingface-cli download ggml-org/Qwen2.5-Coder-1.5B-Q8_0-GGUF --local-dir ./models")
        print("  Then set MODEL_PATH environment variable or update MODEL_PATH in this script")
        exit(1)
    
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

def run_inference(llm, question: str, max_tokens: int = 15, use_chat_template: bool = True) -> Tuple[str, float, Dict]:
    """Run optimized inference with llama.cpp."""
    
    prompt = f"""<|im_start|>system
You are a Travel Autocomplete Assistant. Analyze incomplete travel queries and suggest the SINGLE NEXT most important missing entity.
 
CRITICAL RULE: First identify what entities are ALREADY in the query. Then suggest ONLY THE NEXT MOST IMPORTANT missing entity in the logical order. Never suggest entities already present.
 
DOMAIN: Flights, Hotels, Trains, Holidays
 
MODE: Single entity suggestion (suggest only ONE entity at a time)
 
ENTITY ORDER BY LOB:
 
FLIGHTS: from [source] → to [destination] → on [date] → return [date] → for [passengers] → in [class] → in [time]

HOTELS: in [location] → on [check-in date] → for [nights] → with [guests] → in [room type] → [category]

TRAINS: from [source] → to [destination] → on [date] → in [class] → for [passengers] → in [time]

HOLIDAYS: to [destination] → starting on [date] → for [days] → for [travelers] → [theme] → [budget]
 
HOW TO DETECT PRESENT ENTITIES:
 
FLIGHTS:

- source: "from [city]" or "[city]" before "to"

- destination: "to [city]" or "[city]" after "from X to"

- date: "on [date]", "on [day]", "this [day]", "tomorrow"

- passengers: "[number] passengers", "for [number]", "family", "for my [number]"

- class: "economy", "business", "first class"

- time: "morning", "afternoon", "evening", "night"
 
make sure no other entities are present other than above for flights.
 
HOTELS:

- location: "in [city]", "at [location]"

- check-in: "on [date]", "check-in on", "arriving on"

- nights: "for [number] nights", "for [number] days"

- guests: "for [number] guests", "with [number] people"

- room: "single", "double", "suite"

- category: "[number]-star", "budget", "luxury"
 
make sure no other entities are present other than above for hotels.
 
TRAINS:

- source: "from [station]" or "from [city]"

- destination: "to [station]" or "to [city]"

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
 
Query: "flight from delhi"

Present: source (delhi)

Missing: destination, date, passengers

Next: destination (next in order after source)

Output: "to [destination]"

NOT: "from [source]" (already present)
 
Query: "flight from delhi to mumbai"

Present: source (delhi), destination (mumbai)

Missing: date, passengers, class

Next: date (next in order)

Output: "on [date]"

NOT: "from [source]" or "to [destination]" (both present)
 
Query: "hotel in goa"

Present: location (goa)

Missing: check-in date, nights, guests

Next: check-in date (next in order after location)

Output: "on [check-in date]"

NOT: "in [location]" (already present)
 
Query: "hotel in goa for 3 nights"

Present: location (goa), nights (3 nights)

Missing: check-in date, guests, room type

Next: check-in date (next most important)

Output: "on [check-in date]"

NOT: "in [location]" or "for [nights]" (both present)
 
Query: "flight to delhi"

Present: destination (delhi)

Missing: source, date, passengers

Next: source (should come before destination in order)

Output: "from [source]"

NOT: "to [destination]" (already present)
 
Query: "i want to"

Present: none

Missing: LOB, destination, source, date

Next: LOB type (must identify first)

Output: "book a [flight/hotel/train/holiday]"
 
RULES:

- Suggest ONLY ONE entity (the next most important)

- Never repeat present entities

- Follow logical order and suggest the next missing one

- Output single entity only

- Use natural language placeholders like "to [destination]"

- Be concise and direct
 
this
 
 <|im_end|>
    <|im_start|>user
    {question}
    <|im_end|>
    <|im_start|>assistant
    """

    # Measure resources before inference
    mem_before = get_memory_usage()
    cpu_before = get_cpu_usage()
    
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
    
    # Measure resources after inference
    mem_after = get_memory_usage()
    cpu_after = get_cpu_usage()
    
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
    
    # Calculate resource deltas
    resource_usage = {
        "memory_rss_delta_mb": mem_after["rss"] - mem_before["rss"],
        "memory_vms_delta_mb": mem_after["vms"] - mem_before["vms"],
        "memory_rss_peak_mb": mem_after["rss"],
        "cpu_usage_percent": cpu_after,
        "inference_time_seconds": inference_time,
    }
    
    return response, inference_time, resource_usage

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

def main():
    """Main function."""
    print("=" * 80)
    print("Qwen 2.5 Coder 1.5B - llama.cpp Latency Test")
    print("=" * 80)
    print()
    
    # Check system info
    print("System Information:")
    print(f"  CPU Count: {psutil.cpu_count()}")
    print(f"  Total RAM: {psutil.virtual_memory().total / 1024 / 1024 / 1024:.2f} GB")
    
    # Check for Apple Silicon
    try:
        import platform
        if platform.system() == "Darwin" and platform.machine() == "arm64":
            print(f"  Platform: Apple Silicon (Metal available)")
        else:
            print(f"  Platform: {platform.system()} {platform.machine()}")
    except:
        pass
    
    print()
    
    # Get baseline resources
    baseline_mem = get_memory_usage()
    baseline_cpu = get_cpu_usage()
    print(f"Baseline Memory: {baseline_mem['rss']:.2f} MB RSS")
    print()
    
    # Load model
    # Set use_metal=False to force CPU usage
    llm = load_model(use_metal=True, n_ctx=512)
    
    # Get resources after model loading
    loaded_mem = get_memory_usage()
    model_memory = loaded_mem['rss'] - baseline_mem['rss']
    print(f"Model Memory Footprint: {model_memory:.2f} MB")
    print()
    
    # Warmup
    warmup(llm)
    print()
    
    # Interactive testing
    print("=" * 80)
    print("Interactive Testing (Enter 'quit' to exit)")
    print("=" * 80)
    print()
    
    latencies = []
    
    while True:
        try:
            question = input("Enter a question: ").strip()
            if question.lower() in ['quit', 'exit', 'q']:
                break
            if not question:
                continue
            
            response, latency, resources = run_inference(llm, question)
            latencies.append(latency)
            
            print(f"Response: {response}")
            print(f"Latency: {latency*1000:.1f}ms")
            print(f"Memory Delta: {resources['memory_rss_delta_mb']:.2f} MB")
            print(f"CPU Usage: {resources['cpu_usage_percent']:.2f}%")
            print()
            
            if len(latencies) > 0:
                avg_latency = sum(latencies) / len(latencies)
                print(f"Average Latency: {avg_latency*1000:.1f}ms (over {len(latencies)} requests)")
                print()
            
        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"Error: {e}")
            import traceback
            traceback.print_exc()
            continue
    
    # Final statistics
    if latencies:
        print("=" * 80)
        print("Final Statistics")
        print("=" * 80)
        print(f"Total Requests: {len(latencies)}")
        print(f"Average Latency: {sum(latencies)/len(latencies)*1000:.1f}ms")
        print(f"Min Latency: {min(latencies)*1000:.1f}ms")
        print(f"Max Latency: {max(latencies)*1000:.1f}ms")
        print("=" * 80)

if __name__ == "__main__":
    main()
