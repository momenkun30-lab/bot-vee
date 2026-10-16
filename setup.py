from setuptools import setup, find_packages

setup(
    name="phantomphish",
    version="4.0",
    packages=find_packages(),
    install_requires=[
        "aiogram>=3.4.0",
        "flask>=3.0.0",
        "flask-cors>=4.0.0",
        "jinja2>=3.1.0",
        "requests>=2.31.0",
        "beautifulsoup4>=4.12.0",
        "python-dotenv>=1.0.0",
        "gunicorn>=21.0.0",
        "lxml>=4.9.0",
        "aiohttp>=3.9.0",
    ],
    python_requires=">=3.9",
)
