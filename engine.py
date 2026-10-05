import os
import re
import json
from collections import Counter
from typing import List, Dict

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

STOPWORDS = {
    "the","and","for","with","that","this","from","into","about","have","has",
    "are","was","were","will","can","could","should","would","you","your","they",
    "their","there","what","when","where","which","while","how","why","a","an",
    "to","of","in","on","is","it","as","be","by","or","we","our","i","my"
}

def extract_topics(text: str, limit: int = 8) -> List[str]:
    words = re.findall(r"[A-Za-z][A-Za-z0-9-]{2,}", text.lower())
    counts = Counter(w for w in words if w not in STOPWORDS)
    return [w for w, _ in counts.most_common(limit)]

def search_items(items: List[Dict], query: str, limit: int = 5):
    if not items:
        return []
    corpus = [f"{x['title']} {x['content']} {x.get('topics','')}" for x in items]
    vectorizer = TfidfVectorizer(stop_words="english", ngram_range=(1, 2))
    matrix = vectorizer.fit_transform(corpus + [query])
    scores = cosine_similarity(matrix[-1], matrix[:-1]).flatten()
    ranked = sorted(zip(items, scores), key=lambda x: x[1], reverse=True)
    return [{**item, "score": round(float(score), 4)}
            for item, score in ranked[:limit] if score > 0]

def local_generate(query: str, sources: List[Dict]) -> Dict:
    topics = []
    for item in sources:
        topics.extend(item.get("topics", "").split(","))
    topics = [x.strip() for x in topics if x.strip()]
    unique = list(dict.fromkeys(topics))[:8]
    primary = unique[:3] if unique else ["your saved knowledge"]
    idea_name = " ".join(x.title() for x in primary[:2]) + " Opportunity"

    return {
        "title": idea_name,
        "summary": f"Combine insights about {', '.join(primary)} to solve a specific user problem related to: {query}.",
        "problem": "A repeated or underserved problem appears across the selected knowledge.",
        "solution": "Build a focused product that connects the strongest recurring problem with the most useful capability found in the saved knowledge.",
        "why_now": "The opportunity is supported by patterns already present in your saved information.",
        "next_step": "Interview 5 potential users and test whether the problem is painful enough to pay for.",
        "connections": primary,
        "sources": [{"id": x["id"], "title": x["title"], "reason": "Relevant to the question based on text similarity."} for x in sources],
        "mode": "local"
    }

def openai_generate(query: str, sources: List[Dict]) -> Dict:
    key = os.getenv("OPENAI_API_KEY")
    if not key:
        return local_generate(query, sources)

    from openai import OpenAI
    client = OpenAI(api_key=key)
    context = "\n\n".join(
        f"[Knowledge {x['id']}] {x['title']}\n{x['content']}\nTopics: {x.get('topics','')}"
        for x in sources
    )
    prompt = f"""
You are the reasoning engine for a personal knowledge system.
User question: {query}

Use the supplied knowledge as evidence. You may make novel inferences, but label them as inferences.
Return JSON with:
title, summary, problem, solution, why_now, next_step,
connections (array), sources (array of objects with id, title, reason).

Saved knowledge:
{context}
"""
    response = client.chat.completions.create(
        model=os.getenv("OPENAI_MODEL", "gpt-4.1-mini"),
        temperature=0.7,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": "Generate useful, grounded ideas from a user's saved knowledge."},
            {"role": "user", "content": prompt},
        ],
    )
    result = json.loads(response.choices[0].message.content)
    result["mode"] = "openai"
    return result
