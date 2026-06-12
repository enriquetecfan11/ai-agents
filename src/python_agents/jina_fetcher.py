import re
from pathlib import Path
from urllib.parse import urlparse

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from src.python_agents.config import DOCUMENTS_DIR, JINA_API_KEY

TIMEOUT = 30


def make_session() -> requests.Session:
    session = requests.Session()
    retry = Retry(
        total=4,
        backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET", "HEAD", "OPTIONS"],
        respect_retry_after_header=True,
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    return session


def slugify(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"[^a-z0-9]+", "-", text)
    text = re.sub(r"-+", "-", text).strip("-")
    return text or "documento"


def make_filename(url: str) -> str:
    parsed = urlparse(url)
    host = parsed.netloc.replace("www.", "")
    path = parsed.path.strip("/")
    raw = f"{host}-{path.replace('/', '-')}" if path else host
    return slugify(raw) + ".md"


def unique_path(path: Path) -> Path:
    if not path.exists():
        return path

    counter = 2
    while True:
        candidate = path.with_name(f"{path.stem}-{counter}{path.suffix}")
        if not candidate.exists():
            return candidate
        counter += 1


def normalize_url(url: str) -> str:
    return url.strip()


def build_jina_url(url: str) -> str:
    return f"https://r.jina.ai/{url}"


def fetch_markdown(
    session: requests.Session,
    url: str,
    api_token: str | None = None,
) -> str:
    jina_url = build_jina_url(url)
    headers = {"User-Agent": "ai-agents/1.0"}
    token = api_token or JINA_API_KEY
    if token:
        headers["Authorization"] = f"Bearer {token}"

    response = session.get(jina_url, headers=headers, timeout=TIMEOUT)
    response.raise_for_status()
    return response.text


def save_markdown(
    url: str,
    content: str,
    output_dir: Path | None = None,
    allow_duplicates: bool = False,
) -> Path:
    target_dir = output_dir or DOCUMENTS_DIR
    target_dir.mkdir(parents=True, exist_ok=True)

    filepath = target_dir / make_filename(url)
    if allow_duplicates:
        filepath = unique_path(filepath)

    final_content = f"""---
source_url: {url}
fetched_via: https://r.jina.ai/
---

{content}
"""
    filepath.write_text(final_content, encoding="utf-8")
    return filepath


def process_urls(
    urls: list[str],
    api_token: str | None = None,
    output_dir: Path | None = None,
    allow_duplicates: bool = False,
) -> None:
    if not urls:
        print("[INFO] No hay URLs para procesar.")
        return

    session = make_session()
    for idx, url in enumerate(urls, start=1):
        try:
            print(f"[{idx}/{len(urls)}] Descargando: {url}")
            markdown = fetch_markdown(session, url, api_token=api_token)
            saved_path = save_markdown(
                url,
                markdown,
                output_dir=output_dir,
                allow_duplicates=allow_duplicates,
            )
            print(f"[OK] Guardado en: {saved_path}")
        except Exception as exc:
            print(f"[ERROR] {url} -> {exc}")
