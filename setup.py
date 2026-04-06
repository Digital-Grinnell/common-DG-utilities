from setuptools import setup, find_packages

setup(
    name="common_dg_utilities",
    version="0.1.0",
    description="Shared utilities for Digital Grinnell Flet-based applications",
    author="Digital Grinnell",
    packages=find_packages(),
    install_requires=[
        "flet>=0.20.0",
    ],
    python_requires=">=3.8",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
)
