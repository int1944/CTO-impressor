### Install llama.cpp

```bash
CMAKE_ARGS="-DGGML_METAL=on" pip install llama-cpp-python
```

### Qwen GGUF for llama.cpp link
```bash
curl -L -o qwen2.5-coder-3b-instruct-fp16.gguf \
  https://huggingface.co/Qwen/Qwen2.5-Coder-3B-Instruct-GGUF/resolve/main/qwen2.5-coder-3b-instruct-fp16.gguf
```