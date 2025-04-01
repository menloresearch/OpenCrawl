#!/usr/bin/env python
from setuptools import setup, find_namespace_packages

setup(
    name="opencrawl",
    version="0.1.3",
    description="Integrated website crawler and content analysis library",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    author="OpenCrawl Team",
    author_email="info@opencrawl.org",
    url="https://github.com/opencrawl/opencrawl",
    packages=find_namespace_packages(exclude=["opencrawl.examples.frontend.node_modules*"]),
    include_package_data=True,
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
    ],
    python_requires=">=3.8",
    install_requires=[
        "pathik>=0.1.0",
        "bhumi>=0.1.0",
        "satya>=0.1.0",
        "python-dotenv>=0.21.0",
        "psycopg2-binary>=2.9.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "black>=23.0.0",
            "isort>=5.10.0",
            "mypy>=0.991",
        ],
    },
) 