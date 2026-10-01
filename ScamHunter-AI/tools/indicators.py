"""Offline scam-indicator scanner.

Runs instantly, needs no API key and no network. It extracts links, phone
numbers, e-mails and crypto wallets, flags well-known scam language and
suspicious URL features, and produces a 0-100 *heuristic* signal score.

The score is a triage hint, never proof: it is shown to the user as
"Instant scan" and passed to the AI agents as an unverified signal.
"""
from __future__ import annotations

import math
import re
from urllib.parse import urlparse

# ---------------------------------------------------------------- patterns

_EMAIL = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
_SCHEME_URL = re.compile(r"(?i)\b(?:https?://|www\.)[^\s<>\"'`)\]]+")
_BARE_DOMAIN = re.compile(
    r"(?i)(?<![@\w./-])((?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+"
    r"(?:com|net|org|info|xyz|top|click|link|online|site|shop|club|live|work|"
    r"support|help|app|io|co|pk|in|ru|cn|tk|ml|ga|cf|gq|icu|vip|buzz|cc|me|ly|"
    r"cfd|sbs|store|fun|bond|today|space|website|ws|biz|us|uk)"
    r"(?:/[^\s<>\"'`)\]]*)?)(?![\w@-])"
)
_PHONE = re.compile(r"(?<![\w.])(?:\+|00)?\d[\d\s().-]{7,18}\d(?![\w])")
_WALLETS = {
    "Bitcoin": re.compile(r"\b(?:bc1[a-z0-9]{25,60}|[13][a-km-zA-HJ-NP-Z1-9]{25,34})\b"),
    "Ethereum": re.compile(r"\b0x[a-fA-F0-9]{40}\b"),
    "Tron": re.compile(r"\bT[1-9A-HJ-NP-Za-km-z]{33}\b"),
}
_MONEY = re.compile(
    r"(?i)(?:[$£€₹]|rs\.?|pkr|usd|usdt|aed)\s?\d[\d,]*(?:\.\d+)?(?:\s?(?:k|m|million|lakh|lac|crore))?"
)

SHORTENERS = {
    "bit.ly", "tinyurl.com", "t.co", "goo.gl", "is.gd", "cutt.ly", "rb.gy",
    "shorturl.at", "ow.ly", "buff.ly", "tiny.cc", "rebrand.ly", "s.id", "t.ly",
}
RISKY_TLDS = {
    "xyz", "top", "click", "link", "icu", "vip", "buzz", "tk", "ml", "ga", "cf",
    "gq", "support", "help", "work", "live", "club", "online", "site", "cfd",
    "sbs", "bond", "fun", "today", "space", "website", "ws",
}
FREE_MAIL = {"gmail.com", "yahoo.com", "outlook.com", "hotmail.com", "proton.me", "aol.com", "icloud.com"}

# brand keyword -> domains that really belong to the brand
BRANDS = {
    "paypal": {"paypal.com"},
    "amazon": {"amazon.com", "amazon.co.uk", "amazon.in", "amazon.ae"},
    "apple": {"apple.com", "icloud.com"},
    "microsoft": {"microsoft.com", "live.com", "office.com"},
    "google": {"google.com", "gmail.com", "youtube.com"},
    "netflix": {"netflix.com"},
    "binance": {"binance.com"},
    "coinbase": {"coinbase.com"},
    "metamask": {"metamask.io"},
    "whatsapp": {"whatsapp.com", "wa.me"},
    "facebook": {"facebook.com", "fb.com"},
    "instagram": {"instagram.com"},
    "meezan": {"meezanbank.com"},
    "easypaisa": {"easypaisa.com.pk"},
    "jazzcash": {"jazzcash.com.pk"},
    "daraz": {"daraz.pk"},
    "fedex": {"fedex.com"},
    "dhl": {"dhl.com"},
    "nadra": {"nadra.gov.pk"},
    "hbl": {"hbl.com"},
    "ubl": {"ubldigital.com", "ubl.com.pk"},
    "alfalah": {"bankalfalah.com"},
    "sbp": {"sbp.org.pk"},
}

# (id, label, severity weight, regex, advice)
RULES: list[tuple[str, str, int, str, str]] = [
    ("urgency", "Urgency / pressure", 10,
     r"\b(urgent(?:ly)?|immediately|right now|act now|within \d+ ?(?:hours?|hrs?|minutes?|mins?)|"
     r"last chance|final (?:notice|warning)|expires? (?:today|soon)|limited time|don't delay|hurry)\b",
     "Scammers rush you so you cannot think or verify."),
    ("threat", "Threats / account suspension", 14,
     r"\b(account (?:will be |has been )?(?:suspended|blocked|closed|locked|terminated)|"
     r"legal action|arrest(?:ed)?|warrant|police case|court notice|fine of|penalty|"
     r"blocked permanently|sim (?:will be )?blocked)\b",
     "Real organisations do not threaten arrest or closure over a message."),
    ("credentials", "Asks for OTP / PIN / password / ID", 22,
     r"\b(otp|one[- ]time (?:password|code)|verification code|pin code|\bpin\b|password|"
     r"cvv|cvc|card number|cnic|ssn|social security|seed phrase|recovery phrase|private key|"
     r"login details|bank details)\b",
     "Never share OTPs, PINs, passwords or seed phrases with anyone."),
    ("payment_method", "Untraceable payment method", 20,
     r"\b(gift ?cards?|itunes card|google play card|steam card|bitcoin|btc|usdt|crypto(?:currency)?|"
     r"western union|moneygram|wire transfer|bank transfer|easypaisa|jazz ?cash|"
     r"remittance|binance|trust wallet|metamask)\b",
     "Requests for gift cards, crypto or wire transfers are classic scam payment channels."),
    ("upfront_fee", "Upfront / processing fee", 20,
     r"\b((?:processing|registration|release|clearance|customs|delivery|activation|"
     r"insurance|tax|admin|verification) (?:fee|charge|deposit|payment)|"
     r"advance (?:fee|payment)|pay (?:a )?(?:small )?fee|refundable deposit)\b",
     "Legitimate prizes, loans and jobs do not require you to pay first."),
    ("too_good", "Too-good-to-be-true promise", 18,
     r"\b(guaranteed (?:returns?|profit|income|approval)|risk[- ]free|double your money|"
     r"100% (?:profit|safe|guaranteed|genuine)|you(?:'ve| have)? won|congratulations|"
     r"lucky (?:draw|winner)|lottery|jackpot|prize|free (?:iphone|gift|money|cash)|"
     r"passive income|earn (?:\$|rs\.?|pkr)?\s?\d[\d,]* ?(?:per|a|/) ?(?:day|week|hour)|"
     r"daily (?:profit|income)|no experience (?:needed|required))\b",
     "Unrealistic rewards are the hook in most investment, giveaway and job scams."),
    ("secrecy", "Secrecy / isolation", 12,
     r"\b(don't tell|do not tell|keep (?:this|it) (?:secret|confidential|private)|"
     r"do not (?:share|discuss) with|between us|confidential offer)\b",
     "Secrecy stops friends or family from warning you."),
    ("impersonation", "Impersonates a bank / courier / government", 12,
     r"\b(dear (?:customer|user|client|account holder)|your bank|bank (?:security|support|team)|"
     r"customer (?:care|support|service)|fbr|nadra|state bank|sbp|fia|cyber crime|"
     r"tax (?:refund|department)|dhl|fedex|ups|tcs|leopards|post office|amazon|paypal|apple id|"
     r"microsoft support|bisp|ehsaas|benazir income)\b",
     "Check the claim through the organisation's official number or app, not the message."),
    ("off_platform", "Pushes you to WhatsApp / Telegram", 10,
     r"\b(whats ?app|telegram|signal)\b.{0,40}\b(contact|message|chat|join|number|link)\b|"
     r"\b(contact|message|chat|join)\b.{0,40}\b(whats ?app|telegram)\b",
     "Moving to a private chat removes platform protections."),
    ("remote_access", "Asks for remote access", 22,
     r"\b(anydesk|teamviewer|quick ?support|ultraviewer|remote (?:access|control|desktop)|"
     r"install (?:this )?(?:app|apk|software))\b",
     "Never install remote-access tools for someone who contacted you."),
    ("job_lure", "Job-scam wording", 12,
     r"\b(work from home|work-from-home|online job|part[- ]time job|data entry job|"
     r"task (?:based|completion)|like (?:and )?subscribe|product (?:rating|boosting)|"
     r"hiring (?:now|urgently)|recruitment fee|training fee)\b",
     "Real employers never charge to hire you or pay per 'like'."),
    ("romance", "Romance / emergency-money pattern", 12,
     r"\b(i (?:am|'m) (?:a )?(?:soldier|doctor|engineer|widow|oil rig)|my (?:late )?husband|"
     r"stuck (?:abroad|overseas|at (?:the )?airport)|need (?:money|help) (?:urgently|for)|"
     r"send me (?:money|funds)|my dear|dearest|sweetheart)\b",
     "Never send money to someone you have not met in person."),
    ("crypto_invest", "Crypto / trading platform pitch", 14,
     r"\b(trading (?:platform|bot|signals?|group)|forex|pig butchering|mining pool|staking reward|"
     r"airdrop|presale|token (?:launch|sale)|usdt (?:investment|trading))\b",
     "Unregulated platforms often show fake profits until you try to withdraw."),
]
_COMPILED = [(i, l, w, re.compile(rx, re.I), a) for i, l, w, rx, a in RULES]


# ------------------------------------------------------------- URL analysis

def _registered_domain(host: str) -> str:
    parts = [p for p in host.lower().split(".") if p]
    if len(parts) <= 2:
        return ".".join(parts)
    second = {"co", "com", "org", "net", "gov", "edu", "ac"}
    if len(parts[-1]) == 2 and parts[-2] in second:
        return ".".join(parts[-3:])
    return ".".join(parts[-2:])


def _clean_url(raw: str) -> str:
    return raw.rstrip(".,;:!?\"')]}>")


def analyze_url(raw: str) -> dict:
    """Return {url, host, flags, risk} for a single link."""
    url = _clean_url(raw)
    candidate = url if re.match(r"(?i)^https?://", url) else "http://" + url.lstrip("/")
    flags: list[str] = []
    risk = 0

    try:
        parsed = urlparse(candidate)
        host = (parsed.hostname or "").lower()
    except ValueError:
        return {"url": url, "host": "", "flags": ["Malformed link"], "risk": 20}

    if not host:
        return {"url": url, "host": "", "flags": ["Malformed link"], "risk": 20}

    reg = _registered_domain(host)
    tld = host.rsplit(".", 1)[-1]

    if re.fullmatch(r"\d{1,3}(?:\.\d{1,3}){3}", host):
        flags.append("Link uses a raw IP address"); risk += 30
    if reg in SHORTENERS or host in SHORTENERS:
        flags.append("URL shortener hides the real destination"); risk += 20
    if "xn--" in host:
        flags.append("Punycode (look-alike characters) in domain"); risk += 30
    if "@" in candidate.split("//", 1)[-1].split("/", 1)[0]:
        flags.append("'@' trick hides the real host"); risk += 30
    if tld in RISKY_TLDS:
        flags.append(f".{tld} is a domain ending often abused in scams"); risk += 14
    if host.count("-") >= 2:
        flags.append("Many hyphens in the domain"); risk += 10
    if len(host.split(".")) >= 5:
        flags.append("Unusually deep sub-domains"); risk += 10
    if candidate.lower().startswith("http://") and url.lower().startswith("http://"):
        flags.append("Not encrypted (http, not https)"); risk += 8
    if len(url) > 110:
        flags.append("Very long link"); risk += 6

    labels = re.split(r"[.-]", host)
    for brand, official in BRANDS.items():
        if brand in labels or any(brand in lab for lab in labels if len(lab) > len(brand)):
            if reg not in official:
                flags.append(f"Mentions '{brand}' but is not the official {brand} domain"); risk += 28
                break

    return {"url": url, "host": host, "flags": flags, "risk": min(risk, 60)}


# ------------------------------------------------------------------ scanner

def _snippet(text: str, match: re.Match, width: int = 70) -> str:
    start = max(0, match.start() - 15)
    end = min(len(text), match.end() + 15)
    out = " ".join(text[start:end].split())
    return (out[: width + 20] + "…") if len(out) > width + 20 else out


def _extract_urls(text: str) -> list[str]:
    emails = _EMAIL.findall(text)
    scrubbed = _EMAIL.sub(" ", text)
    found, seen = [], set()
    for m in _SCHEME_URL.finditer(scrubbed):
        u = _clean_url(m.group(0))
        if u.lower() not in seen:
            seen.add(u.lower()); found.append(u)
    covered = " ".join(found).lower()
    for m in _BARE_DOMAIN.finditer(scrubbed):
        u = _clean_url(m.group(1))
        if u.lower() not in seen and u.lower() not in covered:
            seen.add(u.lower()); found.append(u)
    del emails
    return found[:12]


def _extract_phones(text: str) -> list[str]:
    out, seen = [], set()
    for m in _PHONE.finditer(text):
        raw = m.group(0).strip()
        digits = re.sub(r"\D", "", raw)
        if 9 <= len(digits) <= 15 and digits not in seen:
            if re.fullmatch(r"(?:19|20)\d{2}[-./ ]\d{1,2}[-./ ]\d{1,2}", raw):  # a date
                continue
            seen.add(digits); out.append(raw)
    return out[:6]


def scan_text(text: str) -> dict:
    """Scan free text. Always returns a dict with the same keys."""
    text = (text or "")[:20000]
    result = {
        "urls": [], "emails": [], "phones": [], "wallets": [], "amounts": [],
        "flags": [], "score": 0, "level": "none", "headline": "",
    }
    if not text.strip():
        return result

    result["emails"] = list(dict.fromkeys(_EMAIL.findall(text)))[:6]
    result["phones"] = _extract_phones(text)
    result["urls"] = [analyze_url(u) for u in _extract_urls(text)]
    result["amounts"] = list(dict.fromkeys(m.group(0).strip() for m in _MONEY.finditer(text)))[:6]
    for chain, rx in _WALLETS.items():
        for m in rx.finditer(text):
            result["wallets"].append({"chain": chain, "address": m.group(0)})
    result["wallets"] = result["wallets"][:4]

    total = 0.0
    for rule_id, label, weight, rx, advice in _COMPILED:
        m = rx.search(text)
        if m:
            result["flags"].append(
                {"id": rule_id, "label": label, "weight": weight,
                 "evidence": _snippet(text, m), "advice": advice}
            )
            total += weight

    # free e-mail used while pretending to be an organisation
    impersonates = any(f["id"] == "impersonation" for f in result["flags"])
    free = [e for e in result["emails"] if e.split("@")[-1].lower() in FREE_MAIL]
    if impersonates and free:
        result["flags"].append(
            {"id": "free_mail", "label": "Official-sounding message from a free e-mail address",
             "weight": 12, "evidence": free[0],
             "advice": "Banks and couriers write from their own domains."}
        )
        total += 12

    if result["wallets"]:
        result["flags"].append(
            {"id": "wallet", "label": "Contains a crypto wallet address", "weight": 16,
             "evidence": result["wallets"][0]["address"],
             "advice": "Crypto payments cannot be reversed. Treat any request to pay a wallet as high risk."}
        )
        total += 16

    risky_urls = [u for u in result["urls"] if u["risk"] > 0]
    if risky_urls:
        total += min(40, sum(u["risk"] for u in risky_urls) * 0.6)

    score = 0 if total <= 0 else round(100 * (1 - 0.5 ** (total / 28)))
    result["score"] = int(max(0, min(100, score)))

    if not (result["flags"] or risky_urls):
        result["level"] = "none"
    elif result["score"] >= 60:
        result["level"] = "high"
    elif result["score"] >= 30:
        result["level"] = "medium"
    else:
        result["level"] = "low"

    n = len(result["flags"]) + len(risky_urls)
    labels = {
        "none": "", "low": "Few warning signals",
        "medium": "Several warning signals", "high": "Strong warning signals",
    }
    result["headline"] = f"{labels[result['level']]} · {n} indicator{'s' if n != 1 else ''}" if n else ""
    return result


def has_findings(scan: dict) -> bool:
    return bool(scan and (scan.get("flags") or scan.get("urls") or scan.get("phones")
                          or scan.get("wallets") or scan.get("emails")))


def format_signals(scan: dict) -> str:
    """Compact text version for the AI prompts (clearly marked as heuristic)."""
    if not has_findings(scan):
        return ""
    lines = [f"Heuristic signal score: {scan['score']}/100 ({scan['level']})."]
    for f in scan["flags"]:
        lines.append(f"- {f['label']}: \"{f['evidence']}\"")
    for u in scan["urls"]:
        extra = "; ".join(u["flags"]) if u["flags"] else "no automatic flags"
        lines.append(f"- Link {u['url']} -> host {u['host']} ({extra})")
    for w in scan["wallets"]:
        lines.append(f"- {w['chain']} wallet address: {w['address']}")
    if scan["phones"]:
        lines.append("- Phone numbers: " + ", ".join(scan["phones"]))
    if scan["emails"]:
        lines.append("- E-mail addresses: " + ", ".join(scan["emails"]))
    return "\n".join(lines)


def build_search_queries(text: str, scan: dict | None = None, limit: int = 3) -> list[str]:
    """Short, targeted web queries (a 2,500-character query finds nothing)."""
    scan = scan or scan_text(text)
    queries: list[str] = []
    for u in scan["urls"]:
        host = u["host"]
        if host and host not in SHORTENERS:
            queries.append(f"{host} scam reviews")
    for w in scan["wallets"][:1]:
        queries.append(f"{w['address']} scam")
    for p in scan["phones"][:1]:
        queries.append(f"{p} scam number")
    queries = list(dict.fromkeys(queries))[:limit]
    if not queries:
        plain = " ".join(re.sub(r"https?://\S+", " ", text or "").split())
        if plain:
            queries.append(plain[:180] + " scam")
    return queries[:limit]
