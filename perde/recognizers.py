"""Detectors for Azerbaijani personal data.

Each detector returns Span objects. Pattern detectors cover structured
identifiers (FIN, VÖEN, IBAN, phone numbers, documents, cards). The name
detector combines a first-name list with Azerbaijani and Russian surname
morphology, so it runs offline with no ML model.
"""
from __future__ import annotations

import re
from dataclasses import dataclass

from .names import FIRST_NAMES, NAME_STOPWORDS, SURNAMES, az_lower, fold

AZ_UPPER = "A-ZƏÖÜÇŞĞİ"
AZ_LOWER = "a-zəöüçşğıi"
CYR_UPPER = "А-ЯЁ"
CYR_LOWER = "а-яё"


@dataclass(frozen=True)
class Span:
    start: int
    end: int
    entity: str
    text: str
    score: float
    detector: str


# --- validators -------------------------------------------------------------

def luhn_ok(digits: str) -> bool:
    total, alt = 0, False
    for ch in reversed(digits):
        d = int(ch)
        if alt:
            d *= 2
            if d > 9:
                d -= 9
        total += d
        alt = not alt
    return total % 10 == 0


def iban_ok(iban: str) -> bool:
    s = iban.replace(" ", "").upper()
    if len(s) != 28 or not s.startswith("AZ"):
        return False
    rearranged = s[4:] + s[:4]
    num = "".join(str(int(c, 36)) for c in rearranged)
    return int(num) % 97 == 1


def _context(text: str, start: int, end: int, words: tuple[str, ...], window: int = 40) -> bool:
    around = text[max(0, start - window):min(len(text), end + window)].lower()
    return any(w in around for w in words)


# --- pattern detectors ------------------------------------------------------

_PHONE = re.compile(
    r"(?<![\d+])(?:\+?\s?994|8|0)[\s\-.]?\(?(?:10|50|51|55|60|70|77|99|12|18|2\d|36)\)?"
    r"[\s\-.]?\d{3}[\s\-.]?\d{2}[\s\-.]?\d{2}(?!\d)"
)
_EMAIL = re.compile(r"\b[\w.+-]+@[\w-]+(?:\.[\w-]+)+\b")
_IBAN = re.compile(r"\bAZ\d{2}\s?[A-Z]{4}(?:\s?[A-Z0-9]{4}){5}\b")
_CARD = re.compile(r"(?<!\d)(?:\d[ \-]?){12,18}\d(?!\d)")
_VOEN = re.compile(r"(?<!\d)\d{10}(?!\d)")
_FIN = re.compile(r"\b(?=[0-9A-Z]*\d)(?=[0-9A-Z]*[A-Z])[0-9A-Z]{7}\b")
_ID_CARD = re.compile(r"\b(?:AZE\s?\d{7,8}|AA\s?\d{7})\b")
_PASSPORT = re.compile(r"\bC\d{8}\b")
_DRIVER_LICENSE = re.compile(r"\b[A-Z]{2}\s?\d{6}\b")
_PLATE = re.compile(r"\b\d{2}\s?-?\s?[A-Z]{2}\s?-?\s?\d{3}\b")
_MONTHS = (
    "yanvar|fevral|mart|aprel|may|iyun|iyul|avqust|sentyabr|oktyabr|noyabr|dekabr|"
    "января|февраля|марта|апреля|мая|июня|июля|августа|сентября|октября|ноября|декабря"
)
_DATE = re.compile(
    r"\b(?:0?[1-9]|[12]\d|3[01])[./-](?:0?[1-9]|1[0-2])[./-](?:19|20)\d{2}\b"  # 21.06.1985
    r"|\b(?:19|20)\d{2}-(?:0[1-9]|1[0-2])-(?:0[1-9]|[12]\d|3[01])\b"  # 1985-06-21
    r"|\b(?:0?[1-9]|1[0-2])/(?:1[3-9]|2\d|3[01])/(?:19|20)\d{2}\b"  # 06/21/1985
    rf"|\b(?:0?[1-9]|[12]\d|3[01])\s(?:{_MONTHS})\s(?:19|20)\d{{2}}\b",
    re.IGNORECASE,
)
_STREET_WORD = r"(?:küçəsi|küç\.|prospekti|pr\.|şossesi|döngəsi|məhəlləsi|bulvarı|dalanı|keçidi)"
_NAME_WORD = rf"(?:[{AZ_UPPER}]\.\s?)?[{AZ_UPPER}][{AZ_UPPER}{AZ_LOWER}]+"
_NUM = r"\d{1,4}[A-Za-z]?"
_ADDRESS = re.compile(
    rf"(?:\b{_NUM},?\s)?{_NAME_WORD}(?:\s{_NAME_WORD}){{0,2}}\s{_STREET_WORD}"
    rf"(?:,?\s*(?:ev|bina|mənzil|m\.)?\s*{_NUM}(?![\d.]))?"
    rf"(?:\s*,?\s*(?:mənzil|m\.)\s*\d{{1,4}})?"
    r"|(?:ул\.|улица|проспект|пр-т)\s?[А-ЯЁ][а-яё]+(?:\s[А-ЯЁ][а-яё]+)?(?:,?\s*(?:д\.)?\s*\d{1,4})?"
)

VOEN_CONTEXT = ("vöen", "voen", "воен", "vergi", "tax id", "инн")
CARD_CONTEXT = ("kart", "card", "карт", "visa", "mastercard")
FIN_CONTEXT = ("fin", "фин", "şəxsiyyət", "vəsiqə", "pin", "fərdi identifikasiya")


def detect_patterns(text: str) -> list[Span]:
    spans: list[Span] = []

    def add(m: re.Match, entity: str, score: float, detector: str) -> None:
        spans.append(Span(m.start(), m.end(), entity, m.group(), score, detector))

    for m in _EMAIL.finditer(text):
        add(m, "EMAIL", 0.99, "email")
    for m in _IBAN.finditer(text):
        add(m, "IBAN", 1.0 if iban_ok(m.group()) else 0.7, "iban")
    for m in _PHONE.finditer(text):
        add(m, "PHONE", 0.95, "az_phone")
    for m in _ID_CARD.finditer(text):
        add(m, "ID_CARD", 0.95, "az_id_card")
    for m in _PASSPORT.finditer(text):
        add(m, "PASSPORT", 0.9, "az_passport")
    for m in _DRIVER_LICENSE.finditer(text):
        add(m, "DRIVER_LICENSE", 0.8, "az_driver_license")
    for m in _CARD.finditer(text):
        digits = re.sub(r"\D", "", m.group())
        if 13 <= len(digits) <= 19:
            if luhn_ok(digits):
                add(m, "CARD", 0.95, "card_luhn")
            elif _context(text, m.start(), m.end(), CARD_CONTEXT):
                # Missing a real card costs more than masking a mistyped one.
                add(m, "CARD", 0.7, "card_context")
    for m in _VOEN.finditer(text):
        has_ctx = _context(text, m.start(), m.end(), VOEN_CONTEXT)
        if has_ctx or m.group()[-1] in "12":
            add(m, "VOEN", 0.95 if has_ctx else 0.6, "voen")
    for m in _FIN.finditer(text):
        has_ctx = _context(text, m.start(), m.end(), FIN_CONTEXT)
        add(m, "FIN", 0.95 if has_ctx else 0.65, "fin")
    for m in _PLATE.finditer(text):
        add(m, "CAR_PLATE", 0.85, "az_plate")
    for m in _DATE.finditer(text):
        add(m, "DATE", 0.8, "date")
    for m in _ADDRESS.finditer(text):
        add(m, "ADDRESS", 0.85, "az_address")
    return spans


# --- name detector ----------------------------------------------------------

_SURNAME_AZ = re.compile(
    r"^[a-zəöüçşğı]{2,}(?:ov|ova|yev|yeva|ev|eva|li|lı|lu|lü|zadə|zade|oğlu|oglu|bəyli|beyli|xanlı)$"
)
_SURNAME_RU = re.compile(r"^[а-яё]{2,}(?:ов|ова|ев|ева|ин|ина|заде|ли)$")
_PATRONYMIC = re.compile(r"^(?:oğlu|oglu|qızı|qizi|оглы|кызы)$", re.IGNORECASE)
_TOKEN = re.compile(rf"[{AZ_UPPER}{CYR_UPPER}{AZ_LOWER}{CYR_LOWER}]+")

# Azerbaijani case endings ("Rənanın", "İlyasa", "Nəfisəni") and common Russian ones.
_SUFFIXES = sorted(
    """nın nin nun nün ın in un ün ya yə yı yi yu yü ni nı nu nü na nə dan dən tan tən nda ndə
    da də ta tə la lə ilə yla ylə a ə ı i u ü ы а у ом ой е ым""".split(),
    key=len, reverse=True,
)
_LEFT_CONTEXT = {
    "salam", "hörmətli", "əziz", "cənab", "dear", "hi", "hello", "mr", "mrs", "ms",
    "уважаемый", "уважаемая", "привет", "здравствуйте", "господин", "госпожа",
}
_RIGHT_CONTEXT = {"xanım", "bəy", "müəllim", "həkim", "müəllimə"}


def _kind(word: str) -> str | None:
    """'given', 'surname' or None for an exact lower-cased word."""
    if word in NAME_STOPWORDS:
        return None
    if word in FIRST_NAMES or fold(word) in FIRST_NAMES:
        return "given"
    if word in SURNAMES or fold(word) in SURNAMES or _SURNAME_AZ.match(word) or _SURNAME_RU.match(word):
        return "surname"
    return None


def _classify(tok: str) -> tuple[str | None, int]:
    """Return (kind, stem length). Strips one case ending if the bare word is unknown."""
    low = az_lower(tok)
    k = _kind(low)
    if k:
        return k, len(tok)
    for suf in _SUFFIXES:
        if low.endswith(suf) and len(low) - len(suf) >= 3:
            k = _kind(low[: -len(suf)])
            if k:
                return k, len(tok) - len(suf)
    return None, 0


def detect_names(text: str) -> list[Span]:
    """Find person names: name lexicon, surname morphology, patronymics, titles and greetings."""
    tokens = [(m.start(), m.end(), m.group()) for m in _TOKEN.finditer(text)]
    info = [_classify(t) for _, _, t in tokens]
    spans: list[Span] = []
    i = 0
    while i < len(tokens):
        start, end, tok = tokens[i]
        kind, stem = info[i]
        capital = tok[:1].isupper()
        prev = az_lower(tokens[i - 1][2]) if i else ""
        nxt = az_lower(tokens[i + 1][2]) if i + 1 < len(tokens) else ""
        nxt_kind = info[i + 1][0] if i + 1 < len(tokens) else None
        by_context = capital and tok[1:].islower() and (prev in _LEFT_CONTEXT or nxt in _RIGHT_CONTEXT)
        # lower-case only when a known given name is followed by a surname: "cavid hüseynov"
        lower_pair = not capital and kind == "given" and nxt_kind == "surname"
        if not ((capital and kind) or by_context or lower_pair):
            i += 1
            continue
        j, e = i, start + (stem or len(tok))
        while j + 1 < len(tokens):
            n_start, n_end, n_tok = tokens[j + 1]
            if text[tokens[j][1]:n_start].strip() not in ("", "."):
                break
            n_kind, n_stem = info[j + 1]
            if _PATRONYMIC.match(n_tok):
                j, e = j + 1, n_end
            elif n_kind and (n_tok[:1].isupper() or lower_pair):
                j, e = j + 1, n_start + n_stem
            else:
                break
        parts = j - i + 1
        score = 0.9 if parts > 1 else (0.75 if kind == "given" or by_context else 0.65)
        spans.append(Span(start, e, "PERSON", text[start:e], score, "az_name"))
        i = j + 1
    return spans


ALL_ENTITIES = (
    "PERSON", "FIN", "ID_CARD", "PASSPORT", "VOEN", "PHONE", "EMAIL",
    "IBAN", "CARD", "DRIVER_LICENSE", "ADDRESS", "DATE", "CAR_PLATE",
)
