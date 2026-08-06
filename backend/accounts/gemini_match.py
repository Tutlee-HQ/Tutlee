"""
Gemini-powered tutor matching.

Replaces pure keyword/substring filtering with genuine semantic reasoning:
Gemini reads the learner's freeform description of what they're stuck on,
compares it against each candidate tutor's subjects/specialities/bio, and
returns a ranked list with a short human-readable reason per match.

Fails gracefully — if GEMINI_API_KEY isn't set, or the API call fails for
any reason (timeout, bad response, rate limit), callers should fall back
to the existing keyword-based ranking rather than breaking the request.
"""
import os
import json
import urllib.request as _ureq
import urllib.error as _uerr

GEMINI_MODEL = 'gemini-2.5-flash'
GEMINI_URL = f'https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent'
MAX_CANDIDATES = 30  # cap prompt size/cost — plenty for a pre-launch tutor pool


def gemini_rank_tutors(subject, weak_areas_text, tutors):
    """
    tutors: list of dicts, each {id, full_name, subjects, specialities, bio}
    Returns: list of {id, reason} in ranked order (best match first),
             or None if Gemini is unavailable/fails — caller should fall
             back to existing behavior in that case.
    """
    api_key = os.environ.get('GEMINI_API_KEY', '').strip()
    if not api_key or not tutors:
        return None

    candidates = tutors[:MAX_CANDIDATES]
    candidate_lines = []
    for t in candidates:
        candidate_lines.append(
            f"- id: {t['id']} | name: {t['full_name']} | "
            f"subjects: {', '.join(t.get('subjects') or [])} | "
            f"specialities: {', '.join(t.get('specialities') or [])} | "
            f"bio: {(t.get('bio') or '').strip()[:200]}"
        )

    prompt = (
        "You are matching a student learner to the best tutor(s) on a peer-to-peer tutoring platform.\n\n"
        f"Learner's subject: {subject}\n"
        f"Learner's description of what they're struggling with: {weak_areas_text or '(not specified)'}\n\n"
        "Candidate tutors:\n" + "\n".join(candidate_lines) + "\n\n"
        "Rank the candidates from best to worst fit for this specific learner. "
        "Base your ranking on how well each tutor's subjects/specialities/bio match "
        "the learner's actual described struggle, not just the general subject. "
        "For each tutor, give a short (max 20 words) reason a learner would find genuinely useful — "
        "explain WHY this tutor fits their specific weak area, not a generic statement. "
        "Return ALL candidate ids, ordered best-fit first."
    )

    body = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "responseMimeType": "application/json",
            "responseSchema": {
                "type": "ARRAY",
                "items": {
                    "type": "OBJECT",
                    "properties": {
                        "id": {"type": "INTEGER"},
                        "reason": {"type": "STRING"},
                    },
                    "required": ["id", "reason"],
                },
            },
        },
    }

    try:
        req = _ureq.Request(
            f'{GEMINI_URL}?key={api_key}',
            data=json.dumps(body).encode('utf-8'),
            headers={'Content-Type': 'application/json'},
            method='POST',
        )
        with _ureq.urlopen(req, timeout=12) as resp:
            data = json.loads(resp.read().decode('utf-8'))
        text = data['candidates'][0]['content']['parts'][0]['text']
        ranked = json.loads(text)
        if not isinstance(ranked, list):
            return None
        return ranked
    except (_uerr.URLError, _uerr.HTTPError, KeyError, IndexError, json.JSONDecodeError, TimeoutError):
        return None
