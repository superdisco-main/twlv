#!/bin/bash

# 환경 변수 설정 확인
if [ -z "$OPENAI_API_KEY" ]; then
  echo "OPENAI_API_KEY is not set. Please set it and restart the container."
  exit 1
fi

if [ -z "$TWELVE_LABS_API_KEY" ]; then
  echo "TWELVE_LABS_API_KEY is not set. Please set it and restart the container."
  exit 1
fi

# Jockey 실행
echo "Starting Jockey in terminal mode..."
exec python -m jockey terminal 