from setuptools import setup, find_packages

setup(
    name="esg-data-agent",
    version="1.0.0",
    description="ESG Data Collection and Intelligence System",
    packages=find_packages(),
    python_requires=">=3.9",
    install_requires=[
        "beautifulsoup4>=4.12.0",
        "lxml>=4.9.0",
        "pdfplumber>=0.10.0",
        "openpyxl>=3.1.0",
        "python-docx>=1.0.0",
        "requests>=2.31.0",
    ],
    entry_points={
        "console_scripts": [
            "esg-agent=main:main",
        ],
    },
)
