"""Deterministic text analysis over extracted evidence."""

from __future__ import annotations

import re
from collections import Counter, defaultdict

from src.data.models import AnalysisResult, AnalysisSummary, Contradiction, ExtractedDocument, Finding, Theme

_STOPWORDS = {
    "about",
    "after",
    "also",
    "been",
    "between",
    "could",
    "from",
    "have",
    "into",
    "more",
    "than",
    "that",
    "their",
    "there",
    "these",
    "they",
    "this",
    "were",
    "what",
    "when",
    "which",
    "with",
    "will",
    "would",
}

_TOPICS = ("price", "pricing", "cost", "users", "revenue", "growth", "market", "year")


def _sentences(text: str) -> list[str]:
    return [part.strip() for part in re.split(r"(?<=[.!?])\s+", text) if part.strip()]


def _terms(text: str) -> list[str]:
    words = [w.lower() for w in re.findall(r"[a-zA-Z]{4,}", text)]
    return [w for w in words if w not in _STOPWORDS]


def _source_url(document: ExtractedDocument) -> str | None:
    url = document.metadata.get("final_url")
    return str(url) if url else None


def analyze_text(documents: list[ExtractedDocument]) -> AnalysisResult:
    """Build deterministic findings, themes, and contradiction markers from extracted text."""
    if not documents:
        return AnalysisResult(
            summary=AnalysisSummary(
                summary="No extracted documents available for analysis.",
                limitations=["No textual evidence was available."],
            )
        )

    term_docs: defaultdict[str, set[str]] = defaultdict(set)
    term_counts: Counter[str] = Counter()
    doc_sentences: dict[str, list[str]] = {}

    for doc in documents:
        doc_sentences[doc.id] = _sentences(doc.content)
        doc_terms = _terms(doc.content)
        term_counts.update(doc_terms)
        for term in set(doc_terms):
            term_docs[term].add(doc.id)

    recurring_terms = [
        term
        for term, doc_ids in sorted(term_docs.items(), key=lambda item: (-len(item[1]), -term_counts[item[0]], item[0]))
        if len(doc_ids) >= 2
    ][:6]

    findings: list[Finding] = []
    themes: list[Theme] = []

    for idx, term in enumerate(recurring_terms, start=1):
        supporting_docs = [doc for doc in documents if doc.id in term_docs[term]]
        snippets: list[str] = []
        urls: list[str] = []
        for doc in supporting_docs:
            url = _source_url(doc)
            if url:
                urls.append(url)
            sentence = next((s for s in doc_sentences[doc.id] if term in s.lower()), None)
            if sentence:
                snippets.append(sentence[:240])

        support_count = len(supporting_docs)
        avg_term_hits = sum(term_counts.get(term, 0) for _ in supporting_docs) / max(support_count, 1)
        confidence = min(1.0, 0.35 + 0.2 * support_count + 0.05 * avg_term_hits)

        finding_id = f"finding-{idx:03d}"
        findings.append(
            Finding(
                id=finding_id,
                title=f"Recurring theme: {term}",
                summary=f"The term '{term}' appears across {support_count} extracted documents.",
                theme=term,
                supporting_source_ids=[doc.source_id for doc in supporting_docs],
                supporting_source_urls=sorted(set(urls)),
                supporting_snippets=snippets[:4],
                confidence=round(confidence, 2),
            )
        )
        themes.append(
            Theme(
                id=f"theme-{idx:03d}",
                label=term,
                key_terms=[term],
                finding_ids=[finding_id],
                source_ids=[doc.source_id for doc in supporting_docs],
            )
        )

    if not findings:
        # Sparse fallback with still-grounded evidence
        doc = max(documents, key=lambda item: len(item.content))
        snippets = doc_sentences[doc.id][:2]
        findings.append(
            Finding(
                id="finding-001",
                title="Primary extracted content",
                summary="Only limited overlapping terms were found; this finding highlights the most substantive extracted document.",
                theme="sparse-content",
                supporting_source_ids=[doc.source_id],
                supporting_source_urls=[url for url in [_source_url(doc)] if url],
                supporting_snippets=snippets,
                confidence=0.4,
            )
        )
        themes.append(
            Theme(
                id="theme-001",
                label="sparse-content",
                key_terms=[],
                finding_ids=["finding-001"],
                source_ids=[doc.source_id],
            )
        )

    contradictions = detect_contradictions(documents)
    summary = AnalysisSummary(
        total_documents=len(documents),
        total_findings=len(findings),
        total_themes=len(themes),
        total_contradictions=len(contradictions),
        summary=(
            f"Analyzed {len(documents)} documents and produced {len(findings)} findings across "
            f"{len(themes)} themes."
        ),
        limitations=[
            "Analysis is deterministic and term-frequency based.",
            "Contradiction detection only flags obvious numeric conflicts in short topic list.",
        ],
    )
    return AnalysisResult(findings=findings, themes=themes, contradictions=contradictions, summary=summary)


def detect_contradictions(documents: list[ExtractedDocument]) -> list[Contradiction]:
    """Conservative contradiction pass over numeric statements."""
    topic_claims: defaultdict[str, list[tuple[ExtractedDocument, str, str]]] = defaultdict(list)

    for doc in documents:
        for sentence in _sentences(doc.content):
            lowered = sentence.lower()
            numbers = re.findall(r"\d+(?:\.\d+)?", sentence)
            if not numbers:
                continue
            for topic in _TOPICS:
                if topic in lowered:
                    topic_claims[topic].append((doc, sentence, numbers[0]))
                    break

    contradictions: list[Contradiction] = []
    for idx, (topic, claims) in enumerate(sorted(topic_claims.items()), start=1):
        values = {value for _, _, value in claims}
        sources = {claim[0].source_id for claim in claims}
        if len(values) < 2 or len(sources) < 2:
            continue

        snippets = [claim[1][:240] for claim in claims[:4]]
        urls = sorted({url for doc, _, _ in claims if (url := _source_url(doc))})
        contradictions.append(
            Contradiction(
                id=f"contradiction-{idx:03d}",
                topic=topic,
                summary=f"Sources report different numeric values for '{topic}' ({', '.join(sorted(values))}).",
                source_ids=sorted(sources),
                source_urls=urls,
                snippets=snippets,
                confidence=min(0.9, 0.5 + 0.1 * len(values)),
            )
        )

    return contradictions
