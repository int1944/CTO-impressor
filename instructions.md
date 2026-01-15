### Install llama.cpp

```bash
CMAKE_ARGS="-DGGML_METAL=on" pip install llama-cpp-python
```

### Qwen GGUF for llama.cpp link
[CLick to download ](https://huggingface.co/bartowski/Qwen2.5-Coder-1.5B-Instruct-GGUF/blob/main/Qwen2.5-Coder-1.5B-Instruct-f16.gguf)

```bash
curl -L -o Qwen2.5-Coder-1.5B-Instruct-f16.gguf \
  https://huggingface.co/bartowski/Qwen2.5-Coder-1.5B-Instruct-GGUF/resolve/main/Qwen2.5-Coder-1.5B-Instruct-f16.gguf
```