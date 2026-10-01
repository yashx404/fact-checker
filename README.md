Fact checker

Paste a claim or headline and see what professional fact-checkers and news outlets say about it.

## How it works
1. Searches the Google Fact Check Tools API for claims already reviewed by fact-checkers.
2. Searches Google News RSS for recent coverage and scores how closely each headline matches.
3. Combines both into a plain-language summary.

## Limitations
- It shows evidence. It does not decide what is true.
- Matching is based on shared keywords, so it can miss paraphrases and can't catch altered details.
- "No fact-check found" does not mean a claim is true or false.

## Run locally
    pip install -r requirements.txt
    streamlit run app.py

Add your Google API key in `.streamlit/secrets.toml`:

    FACTCHECK_API_KEY = "your-key"

## Tech
Python, Streamlit, Google Fact Check Tools API, Google News RSS.