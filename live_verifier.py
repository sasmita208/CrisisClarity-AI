# app/utils/live_verifier.py
import logging
from typing import List, Dict, Tuple
import numpy as np

from sentence_transformers import SentenceTransformer, util
from transformers import pipeline
from datetime import datetime

logger = logging.getLogger(__name__)

# --- models: pick lightweight defaults
EMBED_MODEL = "all-MiniLM-L6-v2"            # small, fast embeddings
NLI_MODEL   = "valhalla/distilbart-mnli-12-1"  # smaller MNLI

# load (done once)
try:
    embed_model = SentenceTransformer(EMBED_MODEL)
except Exception as e:
    logger.warning("Embedding model failed to load: %s", e)
    embed_model = None

try:
    # text-classification pipeline with MNLI model => outputs labels: entailment/contradiction/neutral
    nli = pipeline("text-classification", model=NLI_MODEL, device=-1, return_all_scores=True)
except Exception as e:
    logger.warning("NLI model load failed: %s", e)
    nli = None


def embed_texts(texts: List[str]):
    if not embed_model:
        return None
    return embed_model.encode(texts, convert_to_tensor=True, show_progress_bar=False)


def top_k_by_embedding(claim: str, candidates: List[Dict], k=5) -> List[Tuple[Dict, float]]:
    """
    candidates: list of dicts with 'text' key (title + excerpt)
    returns list of (candidate_dict, cos_sim_score) sorted desc
    """
    if not embed_model:
        # fallback: do trivial matching using substring / fuzzy (not ideal)
        from rapidfuzz import fuzz
        scored = []
        for c in candidates:
            score = max(fuzz.partial_ratio(claim, c.get("text","")), fuzz.token_set_ratio(claim, c.get("text","")))
            scored.append((c, score/100.0))
        scored.sort(key=lambda x: x[1], reverse=True)
        return scored[:k]

    claim_emb = embed_model.encode(claim, convert_to_tensor=True)
    texts = [c.get("text","") for c in candidates]
    emb = embed_model.encode(texts, convert_to_tensor=True, show_progress_bar=False)
    sims = util.cos_sim(claim_emb, emb)[0].cpu().numpy()   # numpy array of sims
    scored = [(candidates[i], float(sims[i])) for i in range(len(candidates))]
    scored.sort(key=lambda x: x[1], reverse=True)
    return scored[:k]


def nli_score(claim: str, evidence_text: str) -> Dict[str, float]:
    """
    Run the NLI/stance model: premise=evidence, hypothesis=claim.
    Returns dict: {'entailment': score, 'contradiction': score, 'neutral': score}
    """
    if nli is None:
        # fallback: quick heuristic: semantic similarity only
        emb = embed_model.encode([claim, evidence_text], convert_to_tensor=True) if embed_model else None
        if emb is not None:
            sim = float(util.cos_sim(emb[0], emb[1]))
            return {"entailment": sim, "contradiction": 1-sim, "neutral": 0.0}
        else:
            return {"entailment": 0.0, "contradiction": 0.0, "neutral": 1.0}
    try:
        # transformer pipeline returns list of dicts; label mapping depends on model internals
        # valhalla/distilbart-mnli-12-1 returns labels: contradiction, neutral, entailment (with scores).
        out = nli(evidence_text, claim)[0]  # returns list of scores dicts
        # out example: [{'label': 'contradiction', 'score': 0.03}, ...]
        scores = {d['label'].lower(): d['score'] for d in out}
        # ensure keys
        return {
            "entailment": scores.get("entailment", 0.0),
            "contradiction": scores.get("contradiction", 0.0),
            "neutral": scores.get("neutral", 0.0)
        }
    except Exception as e:
        logger.error("NLI call failed: %s", e)
        return {"entailment": 0.0, "contradiction": 0.0, "neutral": 1.0}


def aggregate_verdict_from_evidence(claim: str, evidence_items: List[Dict], top_k=5) -> Dict:
    """
    evidence_items: each dict must include: 'title','excerpt','url','source','publisher' optional, 'type' eg 'news'|'factcheck'
    Steps:
      - produce a 'text' field for each evidence (title + excerpt)
      - retrieve top_k by embedding
      - run nli_score for each top item
      - apply rules:
         * if any fact-check with rating 'false' -> verified_fake (high)
         * else aggregate NLI: weighted vote (factcheck weight higher)
    Returns: dict -> {verdict, confidence, evidence_details:list}
    """
    # create candidate pool with text
    candidates = []
    for e in evidence_items:
        title = e.get("title") or ""
        excerpt = e.get("excerpt") or e.get("text") or e.get("description") or ""
        txt = (title + " - " + excerpt).strip()
        candidates.append({
            "text": txt,
            "url": e.get("url"),
            "source": e.get("source") or e.get("publisher") or e.get("site"),
            "raw": e,
            "type": e.get("type", "news")
        })

    # shortcut: if GoogleFactCheck exists and rating indicates false/true, return quickly
    for e in evidence_items:
        if e.get("provider") == "GoogleFactCheck":
            r = (e.get("rating") or "").lower()
            if "false" in r:
                return {"verdict": "verified_fake", "confidence": 0.98, "evidence": [e]}
            if "true" in r:
                return {"verdict": "verified_true", "confidence": 0.98, "evidence": [e]}

    # retrieve top candidates
    top = top_k_by_embedding(claim, candidates, k=top_k)

    # run NLI on each top candidate and score
    results = []
    entail_sum = 0.0
    contra_sum = 0.0
    total_weight = 0.0

    for cand, sim in top:
        txt = cand["text"]
        nli_scores = nli_score(claim, txt)
        # weight: factcheck > news
        weight = 2.0 if cand.get("type") == "factcheck" or (cand.get("source") and "fact" in cand.get("source", "").lower()) else 1.0
        # combine: use both semantic sim and nli; ensure values in [0,1]
        entail = nli_scores.get("entailment", 0.0)
        contradiction = nli_scores.get("contradiction", 0.0)
        # simple scoring: add weight * score
        entail_sum += weight * entail
        contra_sum += weight * contradiction
        total_weight += weight
        results.append({
            "source": cand.get("source"),
            "url": cand.get("url"),
            "similarity": sim,
            "nli": nli_scores,
            "type": cand.get("type"),
            "weight": weight
        })

    if total_weight == 0:
        return {"verdict": "unknown", "confidence": 0.0, "evidence": results}

    avg_entail = entail_sum / total_weight
    avg_contra = contra_sum / total_weight

    # Final decision rules
    # If avg_contra significantly > avg_entail -> fake
    # If avg_entail significantly > avg_contra -> true
    # else unknown

    # tuning thresholds:
    if avg_contra - avg_entail > 0.15 and avg_contra > 0.5:
        verdict = "verified_fake"
        confidence = round(min(0.99, avg_contra), 2)
    elif avg_entail - avg_contra > 0.15 and avg_entail > 0.5:
        verdict = "verified_true"
        confidence = round(min(0.99, avg_entail), 2)
    else:
        verdict = "unknown"
        confidence = round(max(avg_entail, avg_contra), 2)

    return {"verdict": verdict, "confidence": confidence, "evidence": results}
