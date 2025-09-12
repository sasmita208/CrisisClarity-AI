import tldextract
import socket
from datetime import datetime, timezone
from dateutil import parser as date_parser
import whois


# ---------- Trusted Whitelist ----------
TRUSTED_DOMAINS = {
    "pib.gov.in",
    "ndma.gov.in",
    "who.int",
    "un.org",
    "mohfw.gov.in",
    "cdc.gov",
    "bbc.com",
    "reuters.com",
}

# ---------- Suspicious Keywords ----------
SUSPICIOUS_KEYWORDS = ["login", "verify", "update", "secure", "bank", "account"]


def get_domain_age(domain: str) -> int | None:
    try:
        print(f"Running WHOIS lookup for domain: {domain}")
        w = whois.whois(domain)
        creation_date = w.creation_date
        print(f"WHOIS creation_date raw: {creation_date}")

        if isinstance(creation_date, list):
            # Normalize all dates to UTC naive for comparison
            normalized_dates = []
            for dt in creation_date:
                if dt.tzinfo is not None:
                    dt = dt.astimezone(timezone.utc).replace(tzinfo=None)
                normalized_dates.append(dt)
            creation_date = min(normalized_dates)
        elif isinstance(creation_date, datetime):
            if creation_date.tzinfo is not None:
                creation_date = creation_date.astimezone(timezone.utc).replace(tzinfo=None)

        if isinstance(creation_date, datetime):
            age_days = (datetime.utcnow() - creation_date).days
            print(f"Domain age in days: {age_days}")
            return age_days

    except Exception as e:
        print(f"WHOIS lookup failed for {domain}: {e}")

    return None


def analyze_url(url: str) -> dict:
    """
    Analyze the given URL and return verdict, reasons, status, and domain age.
    """
    extracted = tldextract.extract(url)
    domain = ".".join(part for part in [extracted.domain, extracted.suffix] if part)

    result = {
        "url": url,
        "domain": domain,
        "status": "Unknown",
        "domain_age_days": None,
        "reasons": [],
        "trusted": False,
    }

    # -- Trusted domain check --
    if domain in TRUSTED_DOMAINS:
        result["status"] = "Trusted"
        result["trusted"] = True
    else:
        # -- Suspicious keyword check --
        for word in SUSPICIOUS_KEYWORDS:
            if word in url.lower():
                result["reasons"].append(f"Suspicious keyword found: {word}")

        # -- Protocol check --
        if url.lower().startswith("http://"):
            result["reasons"].append("Insecure protocol (http)")

        if result["reasons"]:
            result["status"] = "Flagged"
        else:
            result["status"] = "Safe"

    # -- WHOIS domain age check --
    result["domain_age_days"] = get_domain_age(domain)

    return result
