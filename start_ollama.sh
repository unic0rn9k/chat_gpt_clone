#!/bin/sh
ollama serve &
OLLAMA_PID=$!

until ollama list; do
  sleep 0.4
done

ollama pull 'qwen3:0.6b'

wait "$OLLAMA_PID"
