from __future__ import annotations

import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from typing import Any
from urllib.parse import urljoin

from .torrent import TorrentItem, normalize_torrent_item

TORZNAB_NS = "http://torznab.com/schemas/2015/feed"
NEWZNAB_NS = "http://www.newznab.com/DTD/2010/feeds/attributes/"


@dataclass(frozen=True)
class TorznabConfig:
    base_url: str
    api_key: str = ""
    categories: list[int] = field(default_factory=list)
    timeout: int = 10
    retries: int = 1


def build_torznab_params(
    query,
    api_key: str = "",
    categories: list[int] | None = None,
) -> dict[str, str]:
    params = {"t": "search", "q": query.title}
    if query.media_type == "movie":
        params["t"] = "movie"
        if query.imdb_id:
            params["imdbid"] = query.imdb_id.removeprefix("tt")
        if query.year:
            params["year"] = str(query.year)
    elif query.media_type in {"episode", "season", "show"}:
        params["t"] = "tvsearch"
        if query.season is not None:
            params["season"] = str(query.season)
        if query.episode is not None:
            params["ep"] = str(query.episode)
        if query.imdb_id:
            params["imdbid"] = query.imdb_id.removeprefix("tt")
    if categories:
        params["cat"] = ",".join(str(item) for item in categories)
    if api_key:
        params["apikey"] = api_key
    return params


def parse_torznab(xml_text: str, base_url: str = "") -> list[TorrentItem]:
    root = ET.fromstring(xml_text)
    items = []
    for item in root.findall(".//channel/item"):
        data = _item_to_dict(item, base_url)
        torrent = normalize_torrent_item(data)
        if torrent.title and (
            torrent.magnet or torrent.torrent_url or torrent.info_hash
        ):
            items.append(torrent)
    return items


def _item_to_dict(item: ET.Element, base_url: str) -> dict[str, Any]:
    attrs = _torznab_attrs(item)
    title = _text(item, "title")
    link = _text(item, "link")
    enclosure = item.find("enclosure")
    enclosure_url = enclosure.get("url", "") if enclosure is not None else ""
    size = attrs.get("size") or _text(item, "size")
    seeders = attrs.get("seeders") or attrs.get("grabs")
    leechers = attrs.get("leechers") or attrs.get("peers")
    magnet = attrs.get("magneturl") or attrs.get("magnet")
    download_url = enclosure_url or link
    if download_url and base_url:
        download_url = urljoin(base_url, download_url)
    return {
        "title": title,
        "magnet": magnet or "",
        "torrent_url": "" if magnet else download_url,
        "size": size,
        "seeders": seeders,
        "leechers": leechers,
        "info_hash": attrs.get("infohash") or attrs.get("info_hash") or "",
        "metadata": {
            "guid": _text(item, "guid"),
            "category": _text(item, "category"),
            "publish_date": _text(item, "pubDate"),
        },
    }


def _torznab_attrs(item: ET.Element) -> dict[str, str]:
    attrs = {}
    for attr in item.findall(f"{{{TORZNAB_NS}}}attr") + item.findall(
        f"{{{NEWZNAB_NS}}}attr"
    ):
        name = (attr.get("name") or "").lower()
        value = attr.get("value") or ""
        if name and value:
            attrs[name] = value
    return attrs


def _text(item: ET.Element, tag: str) -> str:
    child = item.find(tag)
    return (child.text or "").strip() if child is not None else ""
