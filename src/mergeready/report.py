from datetime import datetime, timezone
from statistics import median


def parse_timestamp(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def hours_between(start: str, end: str) -> float:
    return (parse_timestamp(end) - parse_timestamp(start)).total_seconds() / 3600


def build_report(owner: str, repo: str, pull_requests: list[dict], reviews_by_pr: dict[int, list[dict]]) -> str:
    rows = []
    first_review_delays = []
    waiting_for_review = 0

    for pr in pull_requests:
        number = pr["number"]
        reviews = reviews_by_pr.get(number, [])
        submitted_reviews = [
            review for review in reviews if review.get("submitted_at")
        ]
        submitted_reviews.sort(key=lambda review: review["submitted_at"])

        first_review_hours = None
        if submitted_reviews:
            first_review_hours = hours_between(
                pr["created_at"],
                submitted_reviews[0]["submitted_at"],
            )
            first_review_delays.append(first_review_hours)
        elif pr["state"] == "open":
            waiting_for_review += 1

        author = pr.get("user", {}).get("login", "")
        reviewers = {
            review.get("user", {}).get("login")
            for review in submitted_reviews
            if review.get("user", {}).get("login")
            and review.get("user", {}).get("login") != author
        }

        if first_review_hours is None:
            first_review_text = "No review recorded"
        else:
            first_review_text = f"{first_review_hours:.1f} h"

        rows.append(
            (
                first_review_hours if first_review_hours is not None else -1,
                number,
                pr,
                first_review_text,
                len(reviewers),
            )
        )

    rows.sort(key=lambda row: row[0], reverse=True)

    lines = [
        f"# MergeReady flow report: {owner}/{repo}",
        "",
        f"Analyzed {len(pull_requests)} recent pull requests.",
        "",
        "## Summary",
        "",
        f"- Open pull requests with no submitted review: **{waiting_for_review}**",
    ]

    if first_review_delays:
        lines.append(
            "- Median time from PR opening to first submitted review: "
            f"**{median(first_review_delays):.1f} hours**"
        )
    else:
        lines.append("- No first-review timing data was available.")

    lines.extend(
        [
            "",
            "## Pull request evidence",
            "",
            "| PR | State | First review | Distinct reviewers | Evidence |",
            "|---|---|---:|---:|---|",
        ]
    )

    for _, number, pr, first_review_text, reviewer_count in rows:
        state = "merged" if pr.get("merged_at") else pr["state"]
        title = pr["title"].replace("|", "\\|")
        lines.append(
            f"| #{number} {title} | {state} | {first_review_text} "
            f"| {reviewer_count} | [PR #{number}]({pr['html_url']}) |"
        )

    lines.extend(
        [
            "",
            "## Notes",
            "",
            "- First-review time is measured from PR creation to the earliest "
            "submitted review returned by GitHub.",
            "- Distinct reviewer counts are not a measure of review quality "
            "or approval requirements.",
            "- CI duration, deployment time, and team ownership are not "
            "included in this prototype report.",
            "",
        ]
    )
    return "\n".join(lines)
