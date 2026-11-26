from datetime import datetime, timezone
from statistics import median


def parse_timestamp(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def duration(hours: float) -> str:
    if hours < 1:
        return f"{round(hours * 60)} min"
    return f"{hours:.1f} h"


def human_reviews(pr, reviews):
    author = (pr.get("user") or {}).get("login")
    result = []
    for review in reviews:
        user = review.get("user") or {}
        if (
            review.get("submitted_at")
            and user.get("type") == "User"
            and user.get("login")
            and user["login"] != author
        ):
            result.append(review)
    return sorted(result, key=lambda review: review["submitted_at"])


def next_action(pr):
    requested = [
        "@" + user["login"] for user in pr.get("requested_reviewers", [])
    ] + [
        team["slug"] for team in pr.get("requested_teams", [])
    ]
    if requested:
        return "Follow up on the existing review request to " + ", ".join(requested) + "."
    return "Choose a reviewer familiar with the changed files and request a review."


def build_report(owner, repo, pull_requests, reviews_by_pr):
    now = datetime.now(timezone.utc)
    delays = []
    queue = []
    rows = []

    for pr in pull_requests:
        number = pr["number"]
        opened = parse_timestamp(pr["created_at"])
        reviews = human_reviews(pr, reviews_by_pr[number])
        reviewers = {review["user"]["login"] for review in reviews}
        link = f"[#{number}]({pr['html_url']})"
        state = "merged" if pr.get("merged_at") else pr["state"]
        first = "None recorded"

        if reviews:
            review = reviews[0]
            hours = (parse_timestamp(review["submitted_at"]) - opened).total_seconds() / 3600
            delays.append(hours)
            first = f"[{duration(hours)}]({pr['html_url']}#pullrequestreview-{review['id']})"
        elif state == "open" and not pr.get("draft"):
            age = (now - opened).total_seconds() / 3600
            queue.append((age, number, link, next_action(pr)))

        if state == "open" and pr.get("draft"):
            state = "draft"
        title = " ".join(pr["title"].split()).replace("|", r"\|")
        rows.append(f"| {link} {title} | {state} | {first} | {len(reviewers)} |")

    lines = [
        f"# MergeReady flow report: {owner}/{repo}", "",
        f"Snapshot at {now:%Y-%m-%d %H:%M UTC} covering the "
        f"{len(pull_requests)} most recently opened PRs returned by GitHub.", "",
        "## Summary", "",
        f"- Open, non-draft PRs without a submitted human review: **{len(queue)}**.",
    ]
    if delays:
        lines.append(
            f"- Median time to first human review: **{duration(median(delays))}** "
            f"across {len(delays)} reviewed PRs in this sample."
        )
    else:
        lines.append("- No submitted human reviews in this sample.")

    lines.extend(["", "## Review queue", ""])
    if queue:
        lines.append("Oldest first, measured from PR opening. Age can include time in draft.")
        lines.append("")
        for age, _, link, action in sorted(queue, reverse=True):
            lines.append(f"- {link} — open for **{duration(age)}**. {action}")
    else:
        lines.append("No open, non-draft PRs are awaiting a first human review in this sample.")

    lines.extend([
        "", "## Pull request evidence", "",
        "| PR | State | First human review | Distinct human reviewers |",
        "|---|---|---:|---:|",
        *rows, "", "## How to read this report", "",
        "A human review is a submitted GitHub review from a User account other than "
        "the PR author. Ordinary conversation comments are excluded. Automation "
        "using a regular User account can still be counted.",
        "The queue covers only the sampled PRs. Review counts describe participation; "
        "they do not establish handoffs, required approvals, or review rounds.", "",
    ])
    return "\n".join(lines)
