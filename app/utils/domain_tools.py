'''# app/utils/domain_tools.py
import logging
import socket
from datetime import datetime, timezone
from functools import lru_cache
from typing import Optional, Dict, Any, List

import whois  # pip install python-whois

from app.utils.config import settings

logger = logging.getLogger(__name__)

# small cache wrapper to avoid repeated whois calls in quick succession
@lru_cache(maxsize=256)
def get_whois(domain: str) -> Optional[Dict[str, Any]]:
    """
    Return parsed whois dict or None on error.
    Uses python-whois wrapper. whois lookups can be slow / rate-limited.
    """
    try:
        w = whois.whois(domain)
        # whois.whois returns an object that behaves like dict
        # convert to normal dict for JSON-serializable keys
        return dict(w)
    except Exception as e:
        logger.warning(f"whois lookup failed for {domain}: {e}")
        return None

def domain_creation_date(whois_data: Dict[str, Any]) -> Optional[datetime]:
    """
    Parse creation_date from whois data (handles list or single datetime).
    Returns timezone-aware datetime or None.
    """
    if not whois_data:
        return None
    cd = whois_data.get("creation_date") or whois_data.get("created")
    if not cd:
        return None
    # sometimes we get a list
    if isinstance(cd, list):
        # pick the earliest (oldest)
        cd = min([d for d in cd if d is not None])
    if isinstance(cd, datetime):
        # ensure timezone-aware
        if cd.tzinfo is None:
            cd = cd.replace(tzinfo=timezone.utc)
        return cd
    # sometimes it's a string; try parse
    try:
        # whois lib usually returns datetime; if string, try fallback parse
        return datetime.fromisoformat(str(cd))
    except Exception:
        return None

def domain_age_days(domain: str) -> Optional[int]:
    """
    Return number of days since domain creation, or None if unknown.
    """
    who = get_whois(domain)
    cd = domain_creation_date(who)
    if cd is None:
        return None
    now = datetime.now(timezone.utc)
    delta = now - cd
    return max(0, delta.days)

def resolve_dns(domain: str) -> List[str]:
    """
    Return list of resolved IPv4/IPv6 addresses (may be empty).
    """
    ips = []
    try:
        # getaddrinfo returns tuples; extract address
        info = socket.getaddrinfo(domain, None)
        for entry in info:
            addr = entry[4][0]
            if addr not in ips:
                ips.append(addr)
    except Exception as e:
        logger.warning(f"DNS resolve failed for {domain}: {e}")
    return ips

def extract_domain_from_url(url: str) -> Optional[str]:
    """
    Normalize and extract domain from URL string.
    Returns lower-cased domain (no port).
    """
    try:
        from urllib.parse import urlparse
        p = urlparse(url if url.startswith(("http://", "https://")) else "http://" + url)
        host = p.hostname
        if host:
            return host.lower()
    except Exception as e:
        logger.warning(f"extract_domain error for {url}: {e}")
    return None
if __name__ == "__main__":
    test_url = "https://pib.gov.in/factcheck.aspx"
    domain = extract_domain_from_url(test_url)
    print({
        "domain": domain,
        "age_days": domain_age_days(domain),
        "ips": resolve_dns(domain),
    })
'''
# app/utils/domain_tools.py
import logging
import socket
from datetime import datetime, timezone
from functools import lru_cache
from typing import Optional, Dict, Any, List

import requests
import whois  # pip install python-whois

from app.utils.config import settings

logger = logging.getLogger(__name__)

# -------------------------------
# Trusted domains (hardcoded whitelist)
# -------------------------------
TRUSTED_DOMAINS = [
    "pib.gov.in",
    "ndma.gov.in",
    "who.int",
    "un.org",
    "mohfw.gov.in",
    "cdc.gov",
    "bbc.com",
    "reuters.com",
]

# -------------------------------
# WHOIS helpers
# -------------------------------

@lru_cache(maxsize=256)
def get_whois(domain: str) -> Optional[Dict[str, Any]]:
    """
    Return parsed whois dict or None on error.
    Uses python-whois wrapper. whois lookups can be slow / rate-limited.
    """
    try:
        w = whois.whois(domain)
        return dict(w)  # make JSON serializable
    except Exception as e:
        logger.warning(f"whois lookup failed for {domain}: {e}")
        return None


def domain_creation_date(whois_data: Dict[str, Any]) -> Optional[datetime]:
    """
    Parse creation_date from whois data (handles list or single datetime).
    Returns timezone-aware datetime or None.
    """
    if not whois_data:
        return None
    cd = whois_data.get("creation_date") or whois_data.get("created")
    if not cd:
        return None
    if isinstance(cd, list):
        cd = min([d for d in cd if d is not None])
    if isinstance(cd, datetime):
        if cd.tzinfo is None:
            cd = cd.replace(tzinfo=timezone.utc)
        return cd
    try:
        return datetime.fromisoformat(str(cd))
    except Exception:
        return None


def domain_age_days(domain: str) -> Optional[int]:
    """
    Return number of days since domain creation, or None if unknown.
    """
    who = get_whois(domain)
    cd = domain_creation_date(who)
    if cd is None:
        return None
    now = datetime.now(timezone.utc)
    delta = now - cd
    return max(0, delta.days)


# -------------------------------
# DNS helpers
# -------------------------------

def resolve_dns(domain: str) -> List[str]:
    """
    Return list of resolved IPv4/IPv6 addresses (may be empty).
    """
    ips = []
    try:
        info = socket.getaddrinfo(domain, None)
        for entry in info:
            addr = entry[4][0]
            if addr not in ips:
                ips.append(addr)
    except Exception as e:
        logger.warning(f"DNS resolve failed for {domain}: {e}")
    return ips


# -------------------------------
# Domain extraction
# -------------------------------

def extract_domain_from_url(url: str) -> Optional[str]:
    """
    Normalize and extract domain from URL string.
    Returns lower-cased domain (no port).
    """
    try:
        from urllib.parse import urlparse
        p = urlparse(url if url.startswith(("http://", "https://")) else "http://" + url)
        host = p.hostname
        if host:
            return host.lower()
    except Exception as e:
        logger.warning(f"extract_domain error for {url}: {e}")
    return None


# -------------------------------
# Trusted whitelist check
# -------------------------------

def is_trusted(domain: str) -> bool:
    """
    Check if domain ends with one of the trusted domains.
    """
    return any(domain.endswith(td) for td in TRUSTED_DOMAINS)


# -------------------------------
# urlscan.io integration
# -------------------------------

def check_with_urlscan(url: str) -> Dict[str, Any]:
    """
    Call urlscan.io API to get scan results.
    Requires settings.URLSCAN_API_KEY to be set.
    """
    api_key = getattr(settings, "URLSCAN_API_KEY", None)
    if not api_key:
        return {"urlscan": "skipped (no API key configured)"}

    try:
        resp = requests.post(
            "https://urlscan.io/api/v1/scan/",
            headers={"API-Key": api_key, "Content-Type": "application/json"},
            json={"url": url, "visibility": "private"},
            timeout=15,
        )
        if resp.status_code == 200:
            data = resp.json()
            return {
                "urlscan": "submitted",
                "urlscan_result": data.get("api"),
            }
        else:
            return {
                "urlscan": f"failed ({resp.status_code})",
                "error": resp.text,
            }
    except Exception as e:
        logger.warning(f"urlscan.io check failed for {url}: {e}")
        return {"urlscan": f"error {e}"}


# -------------------------------
# Master verification wrapper
# -------------------------------

def verify_domain(url: str) -> Dict[str, Any]:
    """
    Main link verification wrapper:
    - Extract domain
    - Trusted domain check
    - Domain age (days)
    - DNS resolution
    - urlscan.io integration (optional)
    """
    domain = extract_domain_from_url(url)
    if not domain:
        return {"url": url, "status": "Invalid URL"}

    age_days = domain_age_days(domain)
    ips = resolve_dns(domain)
    trusted = is_trusted(domain)

    result = {
        "url": url,
        "domain": domain,
        "status": "Trusted" if trusted else "Unverified",
        "trusted": trusted,
        "domain_age_days": age_days,
        "ips": ips,
    }

    # urlscan.io (optional)
    scan_res = check_with_urlscan(url)
    result.update(scan_res)

    return result


# -------------------------------
# Local test
# -------------------------------
if __name__ == "__main__":
    test_url = "https://pib.gov.in/factcheck.aspx"
    print(verify_domain(test_url))
