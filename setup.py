from setuptools import setup, find_packages

setup(
    name='tokmon',
    version='0.1',
    packages=find_packages(),
    install_requires=[
        'mitmproxy',
        'tiktoken',
    ],
    package_data={
        "tokmon": ["pricing.json"],
    },
    entry_points={
        'console_scripts': [
            "tokmon = tokmon.cli:cli",
        ],
    },
)
