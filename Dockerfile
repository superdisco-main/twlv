# Python 3.11 이미지를 기반으로 사용
FROM python:3.11-slim

# 작업 디렉토리 설정
WORKDIR /app

# 필요한 시스템 패키지 설치 (ffmpeg 포함)
RUN apt-get update && apt-get install -y \
    ffmpeg \
    git \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# 소스 코드 복사
COPY . /app/

# 필요한 Python 패키지 설치
RUN pip install --no-cache-dir -r ./jockey/requirements.txt

# 환경 변수 설정 (필요한 경우 수정)
ENV PYTHONPATH=/app
ENV HOST_PUBLIC_DIR=/app/public
ENV LLM_PROVIDER=OPENAI

# 공개 디렉토리 생성
RUN mkdir -p /app/public

# langgraph 설정 파일 생성
COPY langgraph.json /app/langgraph.json
COPY compose.yaml /app/compose.yaml

# 컨테이너 실행 시 실행할 명령어
CMD ["python", "-m", "jockey", "terminal"]