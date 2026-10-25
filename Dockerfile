FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y gcc python3-dev

COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip setuptools wheel
RUN pip install --no-cache-dir aiogram==2.25.1 aiohttp==3.8.6 flask==2.3.3 flask-cors==4.0.0 jinja2==3.1.2 requests==2.31.0 beautifulsoup4==4.12.2 python-dotenv==1.0.0 gunicorn==21.2.0 lxml==4.9.3

COPY . .

CMD ["python", "bot.py"]
