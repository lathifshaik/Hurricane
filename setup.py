from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="hurricane-ai",
    version="0.1.0",
    author="Hurricane AI Team",
    author_email="hurricane@example.com",
    description="An intelligent AI coding assistant powered by Ollama",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/hurricane-ai/hurricane",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Code Generators",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    python_requires=">=3.9",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "hurricane=hurricane.cli:main",
        ],
    },
    include_package_data=True,
    package_data={
        "hurricane": ["templates/*", "config/*"],
    },
)
