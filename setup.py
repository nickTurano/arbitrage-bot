"""
Setup script for Polymarket-Kalshi Arbitrage Bot
"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="polymarket-kalshi-arbitrage-bot",
    version="1.0.0",
    author="Polymarket-Kalshi Arbitrage Bot Contributors",
    description="Professional arbitrage trading bot for Polymarket and Kalshi prediction markets",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/polymarket-kalshi-arbitrage-bot",
    packages=find_packages(exclude=["tests", "tests.*"]),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Financial and Insurance Industry",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Office/Business :: Financial :: Investment",
    ],
    python_requires=">=3.10",
    install_requires=requirements,
    extras_require={
        "dev": [
            "pytest>=7.4.0",
            "pytest-asyncio>=0.21.0",
            "black>=23.10.0",
            "mypy>=1.7.0",
            "flake8>=6.0.0",
            "pytest-cov>=4.1.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "arbitrage-bot=arbitrage_bot.cli:main",
        ],
    },
)

