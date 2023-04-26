from setuptools import setup, find_packages
import os

# Read the contents of the README.md file
with open(os.path.join(os.path.dirname(__file__), "README.md"), encoding="utf-8") as f:
    long_description = f.read()

setup(
    name='tokmon',
    version='0.2.0',
    packages=find_packages(),
    install_requires=[
        'mitmproxy',
        'tiktoken',
    ],
    package_data={
        "tokmon": ["openai-pricing.json"],
    },
    entry_points={
        'console_scripts': [
            "tokmon = tokmon.cli:cli",
        ],
    },
    description = "tokmon is a CLI utility to monitor OpenAI token usage and costs",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yagil/tokmon",
        project_urls={  # Optional
        "Bug Reports": "https://github.com/yagil/tokmon/issues",
        "Source": "https://github.com/yagil/tokmon/",
    },
)