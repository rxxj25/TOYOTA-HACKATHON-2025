"""
Setup script for GR Cup Real-Time Analytics Dashboard
"""

from setuptools import setup, find_packages

setup(
    name="gr-cup-analytics",
    version="1.0.0",
    description="Real-Time Analytics Dashboard for GR Cup Race Engineering",
    author="Toyota Hackathon Team",
    packages=find_packages(),
    install_requires=[
        "streamlit>=1.28.0",
        "pandas>=2.0.0",
        "numpy>=1.24.0",
        "plotly>=5.17.0",
    ],
    python_requires=">=3.8",
)

