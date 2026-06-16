"""Descarga URLs como Markdown vía Jina y las indexa en ChromaDB."""

import sys

from agents.paths import setup_import_path

setup_import_path()

from agents.config import JINA_API_KEY, URLS_FILE  # noqa: E402
from agents.ingest import ingest_markdown_to_chroma  # noqa: E402
from agents.jina_fetcher import normalize_url, process_urls  # noqa: E402

ALLOW_DUPLICATES = False
USE_URLS_FILE_IF_EXISTS = True

DEFAULT_URLS = [
    "https://cti.wazuh.com/vulnerabilities/cves/CVE-2026-34182",
]


def load_urls() -> list[str]:
    urls: list[str] = []

    if USE_URLS_FILE_IF_EXISTS and URLS_FILE.exists():
        for line in URLS_FILE.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            urls.append(normalize_url(line))
    else:
        urls = [normalize_url(url) for url in DEFAULT_URLS if normalize_url(url)]

    if not ALLOW_DUPLICATES:
        urls = list(dict.fromkeys(urls))

    return urls


def main() -> None:
    cli_urls = [normalize_url(arg) for arg in sys.argv[1:] if normalize_url(arg)]

    if cli_urls:
        urls = cli_urls if ALLOW_DUPLICATES else list(dict.fromkeys(cli_urls))
    else:
        urls = load_urls()

    process_urls(urls, api_token=JINA_API_KEY)
    ingest_markdown_to_chroma()


if __name__ == "__main__":
    main()
