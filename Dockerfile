FROM python:3.11-slim

WORKDIR /app

# Cài đặt thư viện hệ thống cần thiết cho psycopg2 và kiểm tra sức khỏe
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Tối ưu hóa log Python trong container
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Cài đặt dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy toàn bộ mã nguồn
COPY . .

# Tạo thư mục uploads nếu chưa có
RUN mkdir -p uploads

EXPOSE 8000

# Chạy migrations Alembic lên bản mới nhất trước khi khởi động FastAPI
CMD ["sh", "-c", "alembic upgrade head && uvicorn app.main:app --host ${HOST:-0.0.0.0} --port ${PORT:-8000}"]
