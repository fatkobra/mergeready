import json
import os
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


def get_json(path: str):
    base_url = os.environ.get(
        "MERGEREADY_GITHUB_API_BASE",
        "https://api.github.com",
    ).rstrip("/")
    url = f"{base_url}/{path.lstrip('/')}"
    request = Request(
        url,
        headers={
            "Accept": "application/vnd.github+json",
            "User-Agent": "MergeReady-Hacksgiving-Prototype",
            "X-GitHub-Api-Version": "2022-11-28",
        },
    )

    if base_url == "https://api.github.com":
        token = os.environ.get("MERGEREADY_GITHUB_TOKEN")
        if token:
            request.add_header("Authorization", f"Bearer {token}")

    try:
        with urlopen(request, timeout=30) as response:
            return json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(
            f"GitHub returned HTTP {exc.code} for {url}: {detail}"
        ) from exc
    except URLError as exc:
        raise RuntimeError(f"Could not reach GitHub at {url}: {exc}") from exc


def fetch_pull_requests(owner: str, repo: str, limit: int):
    path = (
        f"repos/{owner}/{repo}/pulls"
        f"?state=all&sort=created&direction=desc&per_page={limit}"
    )
    return get_json(path)


def fetch_reviews(owner: str, repo: str, number: int):
    reviews = []
    page = 1
    while True:
        batch = get_json(
            f"repos/{owner}/{repo}/pulls/{number}/reviews?per_page=100&page={page}"
        )
        reviews.extend(batch)
        if len(batch) < 100:
            return reviews
        page += 1
