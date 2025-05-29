#!/bin/sh
ollama serve &
OLLAMA_PID=$!

until ollama list; do
  sleep 0.4
done

ollama pull 'gemma3:1b'

wait "$OLLAMA_PID"
