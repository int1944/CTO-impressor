#!/usr/bin/env python3
"""
Optimized Latency Test for Qwen 2.5 Coder 1.5B - Autocomplete Use Case
Includes multiple optimizations for faster inference.
"""

import time
import psutil
import os
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM
import gc
from typing import Dict, Tuple

# Model configuration
MODEL_NAME = "Qwen/Qwen2.5-Coder-1.5B-Instruct"

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

def load_model(use_quantization: bool = False, use_compile: bool = True):
    """Load and optimize the Qwen 2.5 Coder model."""
    print(f"Loading model: {MODEL_NAME}")
    print("This may take a while on first run...")
    
    start_time = time.time()
    
    # Load tokenizer
    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME, trust_remote_code=True)
    
    # Check for MPS availability
    use_mps = torch.backends.mps.is_available()
    device = "mps" if use_mps else "cpu"
    
    print(f"  Device: {device.upper()}")
    print(f"  Quantization: {'int8' if use_quantization else 'float16' if use_mps else 'float32'}")
    print(f"  Compilation: {use_compile}")
    
    # Load model with optimizations
    if use_quantization:
        # Try to load with 8-bit quantization for faster inference
        try:
            from transformers import BitsAndBytesConfig
            quantization_config = BitsAndBytesConfig(load_in_8bit=True)
            model = AutoModelForCausalLM.from_pretrained(
                MODEL_NAME,
                quantization_config=quantization_config,
                device_map="auto" if use_mps else None,
                trust_remote_code=True
            )
        except Exception as e:
            print(f"  Warning: Quantization failed ({e}), falling back to float16")
            model = AutoModelForCausalLM.from_pretrained(
                MODEL_NAME,
                torch_dtype=torch.float16 if use_mps else torch.float32,
                device_map="auto" if use_mps else None,
                trust_remote_code=True
            )
    else:
        model = AutoModelForCausalLM.from_pretrained(
            MODEL_NAME,
            torch_dtype=torch.float16 if use_mps else torch.float32,
            device_map="auto" if use_mps else None,
            trust_remote_code=True
        )
    
    # Move to device if not using device_map
    if not use_quantization or not use_mps:
        model = model.to(device)
    
    # Compile model for faster inference (PyTorch 2.0+)
    if use_compile and hasattr(torch, 'compile'):
        print("  Compiling model (this may take a minute)...")
        try:
            # Use 'reduce-overhead' mode for faster inference
            model = torch.compile(model, mode="reduce-overhead", fullgraph=False)
            print("  Model compiled successfully")
        except Exception as e:
            print(f"  Warning: Compilation failed ({e}), continuing without compilation")
    
    # Set model to eval mode
    model.eval()
    
    load_time = time.time() - start_time
    print(f"Model loaded in {load_time:.2f} seconds")
    
    return model, tokenizer, device

def run_inference(model, tokenizer, question: str, device: str, use_kv_cache: bool = True) -> Tuple[str, float, Dict]:
    """Run optimized inference with various speed improvements."""
    
    # Prepare input - optimized for autocomplete
    messages = [
        {"role": "user", "content": f"youre a travel based autocomplete assistant, only complete the word and return the word: {question}"}
    ]
    
    # Pre-apply chat template
    inputs = tokenizer(
        question,
        return_tensors="pt",
        add_special_tokens=False
    ).to(model.device)

    
    # Measure resources before inference
    mem_before = get_memory_usage()
    cpu_before = get_cpu_usage()
    
    # Run inference with optimizations
    start_time = time.time()
    
    # Use torch.inference_mode() instead of no_grad() for better performance
    with torch.inference_mode():
        generated_ids = model.generate(
            **inputs,
            max_new_tokens=10,  # Short for autocomplete
            temperature=0,  # Greedy decoding
            do_sample=False,  # No sampling overhead
            num_beams=1,  # No beam search overhead
            pad_token_id=tokenizer.eos_token_id,  # Avoid padding overhead
            use_cache=use_kv_cache,  # Enable KV cache for faster generation
            # Additional optimizations
            repetition_penalty=1.0,  # No repetition penalty overhead
            output_scores=False,  # Don't compute scores
            return_dict_in_generate=False,  # Return only ids
        )
    
    inference_time = time.time() - start_time
    
    # Measure resources after inference
    mem_after = get_memory_usage()
    cpu_after = get_cpu_usage()
    
    # Decode response - optimized
    input_length = inputs.input_ids.shape[1]
    generated_ids = generated_ids[0][input_length:] if len(generated_ids.shape) > 1 else generated_ids[input_length:]
    response = tokenizer.decode(generated_ids, skip_special_tokens=True)
    
    # Calculate resource deltas
    resource_usage = {
        "memory_rss_delta_mb": mem_after["rss"] - mem_before["rss"],
        "memory_vms_delta_mb": mem_after["vms"] - mem_before["vms"],
        "memory_rss_peak_mb": mem_after["rss"],
        "cpu_usage_percent": cpu_after,
        "inference_time_seconds": inference_time,
    }
    
    return response, inference_time, resource_usage

def warmup(model, tokenizer, device: str):
    """Warmup run to initialize CUDA/MPS kernels and cache."""
    print("Warming up model...")
    dummy_input = "test"
    try:
        run_inference(model, tokenizer, dummy_input, device, use_kv_cache=True)
        # Run a second time to ensure everything is cached
        run_inference(model, tokenizer, dummy_input, device, use_kv_cache=True)
        print("Warmup complete")
    except Exception as e:
        print(f"Warmup warning: {e}")

def main():
    """Main function with optimization options."""
    print("=" * 80)
    print("Qwen 2.5 Coder 1.5B - OPTIMIZED Latency Test")
    print("=" * 80)
    print()
    
    # Check system info
    print("System Information:")
    print(f"  CPU Count: {psutil.cpu_count()}")
    print(f"  Total RAM: {psutil.virtual_memory().total / 1024 / 1024 / 1024:.2f} GB")
    print(f"  MPS Available: {torch.backends.mps.is_available()}")
    print(f"  PyTorch Version: {torch.__version__}")
    if torch.backends.mps.is_available():
        print(f"  Device: Apple Silicon GPU (MPS)")
    print()
    
    # Get baseline resources
    baseline_mem = get_memory_usage()
    baseline_cpu = get_cpu_usage()
    print(f"Baseline Memory: {baseline_mem['rss']:.2f} MB RSS")
    print()
    
    # Load model with optimizations
    # Set use_quantization=True for even faster inference (requires bitsandbytes)
    # Set use_compile=True for torch.compile optimization
    model, tokenizer, device = load_model(use_quantization=False, use_compile=False)
    
    # Get resources after model loading
    loaded_mem = get_memory_usage()
    model_memory = loaded_mem['rss'] - baseline_mem['rss']
    print(f"Model Memory Footprint: {model_memory:.2f} MB")
    print()
    
    # Warmup the model
    warmup(model, tokenizer, device)
    print()
    
    # Run interactive tests
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
            
            response, latency, resources = run_inference(model, tokenizer, question, device)
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
            
            # Light cleanup
            gc.collect()
            
        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"Error: {e}")
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
