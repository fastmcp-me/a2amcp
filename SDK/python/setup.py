"""
setup.py for A2AMCP Python SDK
"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="a2amcp",
    version="0.1.0",
    author="A2AMCP Contributors",
    author_email="",
    description="Python SDK for A2AMCP - Agent-to-Agent communication via Model Context Protocol",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/webdevtodayjason/A2AMCP",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    python_requires=">=3.8",
    install_requires=[
        "asyncio",
        "typing-extensions>=4.0.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-asyncio>=0.21.0",
            "black>=23.0.0",
            "mypy>=1.0.0",
            "flake8>=6.0.0",
        ],
        "test": [
            "pytest>=7.0.0",
            "pytest-asyncio>=0.21.0",
            "pytest-cov>=4.0.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "a2amcp=a2amcp.cli:main",
        ],
    },
)

# Directory structure for the SDK:
# a2amcp-sdk/
# ├── setup.py
# ├── README.md
# ├── LICENSE
# ├── requirements.txt
# ├── src/
# │   └── a2amcp/
# │       ├── __init__.py
# │       ├── client.py      (core client from first artifact)
# │       ├── prompt.py      (prompt builder from second artifact)
# │       ├── exceptions.py
# │       ├── models.py
# │       └── cli.py
# ├── tests/
# │   ├── __init__.py
# │   ├── test_client.py
# │   ├── test_prompt.py
# │   └── test_integration.py
# └── examples/
#     └── examples.py       (from third artifact)