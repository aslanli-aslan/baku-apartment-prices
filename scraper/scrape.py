import csv
import json
import logging
import random
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import requests

from apartmentprices.paths import RAW_DATA

GRAPHQL_URL = "https://bina.az/graphql"

BASE_HEADERS = {
    "Accept": "*/*",
    "Accept-Language": "en-US,en;q=0.9,az;q=0.8,tr;q=0.7,ru;q=0.6",
    "Content-Type": "application/json",
    "Priority": "u=1, i",
    "Referer": "https://bina.az/baki/alqi-satqi/menziller",
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "same-origin",
    "X-Platform": "desktop",
}


LIST_WORKERS = 8
ENRICH_WORKERS = 32


PAGE_SIZE = 25


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(__name__)


_thread_local = threading.local()


_session_config = {}
_config_lock = threading.Lock()


def _init_session_config(cookies: dict, user_agent: str) -> None:
    _session_config["cookies"] = cookies
    _session_config["user_agent"] = user_agent


def _get_session() -> requests.Session:
    if not hasattr(_thread_local, "session"):
        session = requests.Session()
        with _config_lock:
            session.cookies.update(_session_config.get("cookies", {}))
            ua = _session_config.get("user_agent", "Mozilla/5.0")
        session.headers.update(BASE_HEADERS)
        session.headers["User-Agent"] = ua
        _thread_local.session = session
    return _thread_local.session


def _fetch(
    url: str,
    params: dict | None = None,
    retries: int = 5,
    is_json: bool = True,
):

    session = _get_session()
    for attempt in range(retries):
        try:
            resp = session.get(url, params=params, timeout=30)
            resp.raise_for_status()
            if is_json:
                return resp.json()
            return resp.text
        except (requests.RequestException, ValueError) as exc:
            wait = (2**attempt) + random.uniform(0, 1)
            log.warning(
                f"Attempt {attempt + 1}/{retries} failed for {url}: {exc} - retrying in {wait}s"
            )
            time.sleep(wait)
    log.error(f"All {retries} attempts failed for {url}")
    return None


def _search_total_count(price_from=None, price_to=None) -> int | None:
    params = {
        "operationName": "SearchTotalCount",
        "variables": json.dumps(
            {
                "filter": {
                    "cityId": "1",
                    "categoryId": "1",
                    "priceFrom": price_from,
                    "priceTo": price_to,
                    "leased": False,
                }
            }
        ),
        "extensions": json.dumps(
            {
                "persistedQuery": {
                    "version": 1,
                    "sha256Hash": "9869b12c312f3c3ca3f7de0ced1f6fcb355781db43f49b4d8b3e278c13490ae6",
                }
            }
        ),
    }
    data = _fetch(GRAPHQL_URL, params)
    if data:
        return data["data"]["itemsConnection"]["totalCount"]
    return None


def _search_items(
    price_from=None, price_to=None, cursor: str = "", sort: str = "PRICE_ASC"
) -> dict | None:
    params = {
        "operationName": "SearchItems",
        "variables": json.dumps(
            {
                "first": PAGE_SIZE,
                "filter": {
                    "cityId": "1",
                    "categoryId": "1",
                    "priceFrom": price_from,
                    "priceTo": price_to,
                    "leased": False,
                },
                "sort": sort,
                "cursor": cursor,
            }
        ),
        "extensions": json.dumps(
            {
                "persistedQuery": {
                    "version": 1,
                    "sha256Hash": "b781511a943a4d710eefdf811a24dd4ae353e55d836952603ce0b37fde97d073",
                }
            }
        ),
    }
    return _fetch(GRAPHQL_URL, params)


def _fetch_additional_information(id: int) -> dict | None:
    params = {
        "operationName": "UserRelatedItem",
        "variables": json.dumps({"id": id}),
        "extensions": json.dumps(
            {
                "persistedQuery": {
                    "version": 1,
                    "sha256Hash": "2b71465916b23b497ba378e6a300c8bb95ed42dfa85f3a6adc6247e3da774444",
                }
            }
        ),
    }
    return _fetch(GRAPHQL_URL, params)


def _find_min_max() -> tuple[int, int]:
    asc = _search_items(sort="PRICE_ASC")
    desc = _search_items(sort="PRICE_DESC")
    min_price = asc["data"]["itemsConnection"]["edges"][0]["node"]["price"]["total"]
    max_price = desc["data"]["itemsConnection"]["edges"][0]["node"]["price"]["total"]
    return min_price, max_price


def _binner(start: int, max_price: int, target: int) -> int:

    cache = {}

    def count(lo, hi):
        key = (lo, hi)
        if key not in cache:
            result = _search_total_count(lo, hi)
            cache[key] = result if result is not None else 0
        return cache[key]

    low, high = start, max_price

    while True:
        mid = (low + high) // 2
        c = count(start, mid)

        if c == target:
            log.info(f"Range: {start} - {mid} | Count: {c}")
            return mid

        if high - low <= 1:
            c_low = count(start, low)
            c_high = count(start, high)
            best = low if abs(c_low - target) <= abs(c_high - target) else high
            log.info(f"Range: {start} - {best} | Count: {count(start, best)}")
            return best

        if c > target:
            high = mid
        else:
            low = mid


def _define_borders() -> list[tuple[int, int]]:
    total_count = _search_total_count()
    if total_count is None:
        raise RuntimeError("Could not fetch total listing count.")

    target = total_count // LIST_WORKERS
    log.info(f"Total listings: {total_count}  |  Target per worker: {target}")

    min_price, max_price = _find_min_max()
    log.info(f"Price range: {min_price} - {max_price}")

    start = min_price
    ranges = []

    for _ in range(LIST_WORKERS - 1):
        stop = _binner(start, max_price, target)
        ranges.append((start, stop))
        start = stop + 1

    ranges.append((start, max_price))
    tail_count = _search_total_count(start, max_price)
    log.info(f"Range: {start} - {max_price} | Count: {tail_count}")

    return ranges


def _normalize_listing(edge: dict) -> dict:

    KEEP = [
        "id",
        "floor",
        "floors",
        "hasMortgage",
        "rooms",
        "hasBillOfSale",
        "hasRepair",
        "updatedAt",
    ]
    node = edge["node"]
    listing = {}
    listing["area"] = node["area"]["value"]
    listing["location"] = node["location"]["name"]
    listing["price"] = node["price"]["total"]
    for field in KEEP:
        listing[field] = node.get(field)
    return listing


def _scrape_range(price_from: int, price_to: int) -> list[dict]:

    listings = []
    cursor = ""
    has_next = True

    while has_next:
        try:
            data = _search_items(
                price_from=price_from, price_to=price_to, cursor=cursor
            )
            if data is None:
                log.warning(
                    f"Null response for range {price_from}-{price_to} at cursor '{cursor}', stopping range."
                )
                break

            conn = data["data"]["itemsConnection"]
            has_next = conn["pageInfo"]["hasNextPage"]
            cursor = conn["pageInfo"]["endCursor"]
            edges = conn["edges"]
            listings.extend(_normalize_listing(e) for e in edges)

        except (KeyError, TypeError) as exc:
            log.error(
                f"Parse error in range {price_from}-{price_to}: {exc} - stopping range."
            )
            break

    log.info(f"Range {price_from}-{price_to} complete: {len(listings)} listings")
    return listings


# enrichment stage - lat/lng from the listing's detail page


def _get_additional_information(listing: dict) -> dict:

    result = dict(listing)

    id = listing["id"]
    response = _fetch_additional_information(id)

    data = response.get("data")
    item = data.get("item")

    result["lat"] = item.get("latitude", None)
    result["lng"] = item.get("longitude", None)

    return result


# io helpers


def _deduplicate(listings: list[dict]) -> list[dict]:
    seen = set()
    result = []
    for lst in listings:
        lid = lst.get("id")
        if lid not in seen:
            seen.add(lid)
            result.append(lst)
    dupes = len(listings) - len(result)
    if dupes:
        log.info(f"Removed {dupes} duplicate listings")
    return result


WRITE_BATCH_SIZE = 1000


def _enrich_and_stream_to_csv(
    listings: list[dict],
    csv_path: Path,
    max_workers: int = ENRICH_WORKERS,
) -> int:

    field_names = list(listings[0].keys()) + ["lat", "lng"]

    csv_path.parent.mkdir(parents=True, exist_ok=True)

    written = 0
    errors = 0
    total = len(listings)
    start = time.perf_counter()
    write_lock = threading.Lock()
    batch = []

    def _flush_batch():
        # caller holds write_lock
        nonlocal written
        if batch:
            writer.writerows(batch)
            f.flush()
            written += len(batch)
            batch.clear()

    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=field_names)
        writer.writeheader()

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {
                executor.submit(_get_additional_information, lst): lst
                for lst in listings
            }
            for future in as_completed(futures):
                try:
                    result = future.result()
                    with write_lock:
                        batch.append(result)
                        if len(batch) >= WRITE_BATCH_SIZE:
                            _flush_batch()
                except Exception as exc:
                    errors += 1
                    log.error(f"Enrichment future raised: {exc}")

                done = written + len(batch) + errors
                if done % 100 == 0 or done == total:
                    elapsed = time.perf_counter() - start
                    rate = done / elapsed if elapsed > 0 else 0
                    log.info(
                        f"Enriched {done - errors}/{total}  ({rate:.1f}/s)  errors={errors}"
                    )

        _flush_batch()

    log.info(f"CSV written: {written} rows -> {csv_path}")
    return written


def main() -> None:
    from seleniumbase import SB

    log.info("Starting scraper - bypassing Cloudflare with SeleniumBase")
    overall_start = time.perf_counter()

    with SB(uc=True, headless=True) as sb:
        # navigate to page and bypass cloudflare challenge
        sb.driver.set_script_timeout(30)
        sb.uc_open_with_reconnect("https://bina.az/baki/alqi-satqi/menziller", 5)
        sb.uc_gui_click_captcha()
        sb.sleep(5)

        # grab cookies and user agent
        selenium_cookies = {c["name"]: c["value"] for c in sb.driver.get_cookies()}
        user_agent = sb.driver.get_user_agent()
        _init_session_config(selenium_cookies, user_agent)
        log.info(f"Selenium session grabbed ({len(selenium_cookies)} cookies).")

        # Stage 0: Define borders
        ranges = _define_borders()

        # Stage 1: scraping general information
        log.info(
            f"Stage 1: scraping {len(ranges)} price-range sections with {LIST_WORKERS} workers."
        )
        stage1_start = time.perf_counter()
        all_listings = []

        with ThreadPoolExecutor(max_workers=LIST_WORKERS) as executor:
            futures = [executor.submit(_scrape_range, lo, hi) for lo, hi in ranges]
            for future in as_completed(futures):
                try:
                    all_listings.extend(future.result())
                except Exception as exc:
                    log.error(f"Range future raised: {exc}")

        all_listings = _deduplicate(all_listings)
        stage1_elapsed = time.perf_counter() - stage1_start
        log.info(
            f"Stage 1 complete: {len(all_listings)} listings in {stage1_elapsed}s ({len(all_listings) / stage1_elapsed}/s)"
        )

        # Stage 2: enrich and write to csv
        log.info(
            f"Stage 2: enriching {len(all_listings)} listings with {ENRICH_WORKERS} workers."
        )
        stage2_start = time.perf_counter()
        written = _enrich_and_stream_to_csv(all_listings, RAW_DATA / "data.csv")
        stage2_elapsed = time.perf_counter() - stage2_start
        log.info(
            f"Stage 2 complete: {written} rows written in {stage2_elapsed}s ({written / stage2_elapsed}/s)"
        )

    overall_elapsed = time.perf_counter() - overall_start
    log.info(
        f"Done. {written} listings in {overall_elapsed}s ({overall_elapsed / written} s/listing)"
    )


if __name__ == "__main__":
    main()
