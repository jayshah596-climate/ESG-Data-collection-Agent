"""Module 1: Data Collection - Web scraping, PDF extraction, text cleaning."""

import re
import requests
from bs4 import BeautifulSoup

from config import ESG_KEYWORDS


def scrape_website(url: str) -> str:
    """Fetch and extract text content from a URL."""
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (ESG Data Collection Agent)"
        }
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "lxml")

        # Remove non-content elements
        for tag in soup(["script", "style", "nav", "footer", "header", "aside", "form"]):
            tag.decompose()

        text = soup.get_text(separator="\n", strip=True)
        return text

    except requests.RequestException as e:
        print(f"[WARNING] Failed to scrape {url}: {e}")
        return ""


def extract_pdf_text(pdf_path: str) -> str:
    """Extract text from a PDF file using pdfplumber."""
    try:
        import pdfplumber

        text_parts = []
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text_parts.append(page_text)

        return "\n".join(text_parts)

    except Exception as e:
        print(f"[WARNING] Failed to extract PDF text from {pdf_path}: {e}")
        return ""


def clean_text(raw_text: str) -> str:
    """Clean raw text: remove noise, excessive whitespace, deduplicate."""
    if not raw_text:
        return ""

    # Remove excessive whitespace
    text = re.sub(r"\n{3,}", "\n\n", raw_text)
    text = re.sub(r"[ \t]{2,}", " ", text)

    # Remove common web artifacts
    text = re.sub(r"cookie[s]?\s*(?:policy|settings|preferences)", "", text, flags=re.IGNORECASE)
    text = re.sub(r"accept\s*(?:all\s*)?cookies?", "", text, flags=re.IGNORECASE)

    # Deduplicate lines
    seen = set()
    unique_lines = []
    for line in text.split("\n"):
        stripped = line.strip()
        if stripped and stripped not in seen:
            seen.add(stripped)
            unique_lines.append(stripped)

    return "\n".join(unique_lines)


def filter_esg_content(text: str) -> str:
    """Filter text to keep only ESG-relevant paragraphs."""
    if not text:
        return ""

    paragraphs = text.split("\n")
    esg_paragraphs = []

    for para in paragraphs:
        para_lower = para.lower()
        if any(kw in para_lower for kw in ESG_KEYWORDS):
            esg_paragraphs.append(para)

    # If very little ESG content found, return all text (might be a sustainability report)
    if len(esg_paragraphs) < 5 and len(paragraphs) > 10:
        return text

    return "\n".join(esg_paragraphs)


def collect(company_name: str, url: str = None, pdf_path: str = None) -> dict:
    """Orchestrate data collection from all sources.

    Returns dict with keys: company_name, web_text, pdf_text, combined_text
    """
    web_text = ""
    pdf_text = ""

    if url:
        print(f"[INFO] Scraping website: {url}")
        raw_web = scrape_website(url)
        cleaned_web = clean_text(raw_web)
        web_text = filter_esg_content(cleaned_web)
        print(f"[INFO] Extracted {len(web_text)} characters from website")

    if pdf_path:
        print(f"[INFO] Extracting PDF: {pdf_path}")
        raw_pdf = extract_pdf_text(pdf_path)
        pdf_text = clean_text(raw_pdf)
        print(f"[INFO] Extracted {len(pdf_text)} characters from PDF")

    combined = "\n\n".join(filter(None, [web_text, pdf_text]))

    return {
        "company_name": company_name,
        "web_text": web_text,
        "pdf_text": pdf_text,
        "combined_text": combined,
    }
