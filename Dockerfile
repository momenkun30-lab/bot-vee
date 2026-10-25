FROM python:3.11-slim-bookworm

WORKDIR /app

# تثبيت المتطلبات الأساسية
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    python3-dev \
    libxml2-dev \
    libxslt1-dev \
    && rm -rf /var/lib/apt/lists/*

# ترقية pip
RUN pip install --no-cache-dir --upgrade pip setuptools wheel

# تثبيت الحزم
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# نسخ الملفات
COPY . .

# تشغيل
CMD ["python", "bot.py"]
