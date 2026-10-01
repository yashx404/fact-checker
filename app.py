import re
from urllib.parse import quote

import feedparser
import requests
import streamlit as st

st.set_page_config(page_title="Fact Checker by @Yash")
st.title("Fact checker")
st.write("Paste a headline, and we'll see what fact-checkers and news outlets say.")

API_KEY = st.secrets["FACTCHECK_API_KEY"]
API_URL = "https://factchecktools.googleapis.com/v1alpha1/claims:search"

STOPWORDS = {
    "the", "a", "an", "in", "on", "at", "of", "to", "and", "or", "is", "are", "was",
    "were", "has", "have", "had", "for", "with", "by", "from", "that", "this", "it",
    "yesterday", "today", "will", "be", "as", "not", "no", "can", "just",
}


def keywords(text):
    words = re.findall(r"[a-zA-Z0-9]+", text.lower())
    return {w for w in words if w not in STOPWORDS and len(w) > 2}


def relevance(claim_words, headline):
    if not claim_words:
        return 0.0
    headline_words = keywords(headline)
    return len(claim_words & headline_words) / len(claim_words)


def search_fact_checks(query):
    response = requests.get(
        API_URL,
        params={"query": query, "key": API_KEY, "pageSize": 8},
        timeout=10,
    )
    response.raise_for_status()
    return response.json().get("claims", [])


def search_news(query, limit=15):
    url = (
        "https://news.google.com/rss/search?q="
        + quote(query + " when:30d")
        + "&hl=en-IN&gl=IN&ceid=IN:en"
    )
    feed = feedparser.parse(url)
    articles = []
    for entry in feed.entries[:limit]:
        articles.append(
            {
                "title": entry.get("title", ""),
                "link": entry.get("link", ""),
                "source": entry.get("source", {}).get("title", "Unknown"),
                "published": entry.get("published", ""),
            }
        )
    return articles


claim = st.text_area("Claim or headline", height=120)

if st.button("Check") and claim.strip():
    query = claim.strip()[:200]
    claim_words = keywords(query)

    # ---- Fetch both signals ----
    try:
        with st.spinner("Searching fact-check databases..."):
            fact_checks = search_fact_checks(query)
    except Exception as e:
        fact_checks = []
        st.error(f"Fact-check lookup failed: {e}")

    try:
        with st.spinner("Searching recent news..."):
            articles = search_news(query)
    except Exception as e:
        articles = []
        st.error(f"News search failed: {e}")

    # Keep only fact-checks whose claim text overlaps meaningfully with the query
        # Fact-checkers word claims differently, so use a lenient cutoff
    relevant_checks = [
        c for c in fact_checks if relevance(claim_words, c.get("text", "")) >= 0.25
    ]
    other_checks = [c for c in fact_checks if c not in relevant_checks]
    related, loose = [], []
    for a in articles:
        (related if relevance(claim_words, a["title"]) >= 0.6 else loose).append(a)
    outlets = {a["source"] for a in related}

    # ---- Summary ----
    st.subheader("Summary")
    if relevant_checks:
                st.warning(
            f"Fact-checkers have reviewed related claims ({len(relevant_checks)} found). "
            "Compare the 'Claim' line in each result with yours, then read the rating."
        )
    elif len(outlets) >= 2:
        st.info(
            f"{len(outlets)} outlets have recent stories closely matching these words. "
            "Check that they report the claim as fact and don't merely debunk it."
        )
    elif related:
        st.info("Only one outlet has a closely matching recent story. Treat as unconfirmed.")
    else:
        st.error(
            "No fact-check and no closely matching recent news. "
            "This claim is unverified. That does not prove it's false."
        )
    st.caption("This tool shows evidence. It does not decide what is true.")

    # ---- Section 1 ----
    st.subheader("1. What fact-checkers say")
    if relevant_checks:
        for item in relevant_checks:
            review = item["claimReview"][0]
            st.markdown(
                f"**Rating: {review.get('textualRating', 'N/A')}**  \n"
                f"Publisher: {review['publisher'].get('name', 'Unknown')}  \n"
                f"Claim: _{item.get('text', '')}_  \n"
                f"[Read the full fact-check]({review['url']})"
            )
            st.divider()
    else:
        st.info("No closely matching fact-check found.")
    if other_checks:
        with st.expander(f"Other fact-checks returned ({len(other_checks)}), may be unrelated"):
            for item in other_checks:
                review = item["claimReview"][0]
                st.markdown(
                    f"**Rating: {review.get('textualRating', 'N/A')}** · "
                    f"{review['publisher'].get('name', 'Unknown')}  \n"
                    f"Claim: _{item.get('text', '')}_  \n"
                    f"[Read the full fact-check]({review['url']})"
                )

    # ---- Section 2 ----
    st.subheader("2. Recent news (last 30 days) closely matching the claim")
    if related:
        for a in related:
            st.markdown(f"**{a['source']}** · {a['published']}  \n[{a['title']}]({a['link']})")
    else:
        st.info("No recent articles closely match these words.")

    if loose:
        with st.expander(f"Loosely related results ({len(loose)}), probably not about this claim"):
            for a in loose:
                st.markdown(f"**{a['source']}** · {a['published']}  \n[{a['title']}]({a['link']})")
