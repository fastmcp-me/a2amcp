"""
setup.py for A2AMCP Python SDK
"""

from setuptools import setup, find_packages
import os

# Read the README file
this_directory = os.path.abspath(os.path.dirname(__file__))
with open(os.path.join(this_directory, "README.md"), encoding="utf-8") as f:
    long_description = f.read()

setup(
    name="a2amcp-sdk",
    version="0.1.0",
    author="Jason",
    author_email="",  # Add your email if you want
    description="Python SDK for A2AMCP - Agent-to-Agent communication via Model Context Protocol",
    long_description=long_description,
    long_description_content_type="text/markdown",
    license="MIT",  # Add license here
    url="https://github.com/webdevtodayjason/A2AMCP",
    project_urls={
        "Bug Tracker": "https://github.com/webdevtodayjason/A2AMCP/issues",
        "Documentation": "https://github.com/webdevtodayjason/A2AMCP/blob/main/docs/API_REFERENCE.md",
        "Source Code": "https://github.com/webdevtodayjason/A2AMCP",
    },
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    include_package_data=True,
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Software Development :: Build Tools",
        "Topic :: System :: Distributed Computing",
        # Removed the License classifier since we're using the license field
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    python_requires=">=3.8",
    install_requires=[
        # asyncio is built-in, don't include it
        "typing-extensions>=4.0.0;python_version<'3.10'",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-asyncio>=0.21.0",
            "black>=23.0.0",
            "mypy>=1.0.0",
            "flake8>=6.0.0",
            "isort>=5.0.0",
        ],
        "test": [
            "pytest>=7.0.0",
            "pytest-asyncio>=0.21.0",
            "pytest-cov>=4.0.0",
        ],
    },
    keywords="mcp ai agents communication orchestration splitmind",
    # Remove entry_points if you don't have a CLI yet
    # entry_points={
    #     "console_scripts": [
    #         "a2amcp=a2amcp.cli:main",
    #     ],
    # },
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