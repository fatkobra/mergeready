import argparse
from pathlib import Path

from mergeready.github_api import fetch_pull_requests, fetch_reviews
from mergeready.report import build_report


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="mergeready",
        description="Create an evidence-backed pull request flow report.",
    )
    parser.add_argument(
        "--repo",
        required=True,
        help="GitHub repository in OWNER/NAME format.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=10,
        help="Number of recent pull requests to inspect (1-25; default: 10).",
    )
    parser.add_argument(
        "--output",
        default="reports/latest.md",
        help="Report path (default: reports/latest.md).",
    )
    args = parser.parse_args()

    parts = args.repo.split("/", maxsplit=1)
    if len(parts) != 2 or not all(parts):
        parser.error("--repo must use OWNER/NAME format")

    if not 1 <= args.limit <= 25:
        parser.error("--limit must be between 1 and 25")

    owner, repo = parts

    try:
        pull_requests = fetch_pull_requests(owner, repo, args.limit)
        reviews_by_pr = {
            pr["number"]: fetch_reviews(owner, repo, pr["number"])
            for pr in pull_requests
        }
        report = build_report(owner, repo, pull_requests, reviews_by_pr)
    except RuntimeError as exc:
        parser.exit(1, f"MergeReady: {exc}\n")

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(report, encoding="utf-8")
    print(f"Report written to {output_path}")
    print(f"Pull requests analyzed: {len(pull_requests)}")


if __name__ == "__main__":
    main()
