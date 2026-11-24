import argparse


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="mergeready",
        description="Create an evidence-backed pull request flow report.",
    )
    parser.add_argument(
        "--repo",
        help="GitHub repository in OWNER/NAME format.",
    )
    args = parser.parse_args()

    if not args.repo:
        parser.print_help()
        return

    print(f"MergeReady prototype: repository selected: {args.repo}")
    print("GitHub data access and flow analysis will be added next.")


if __name__ == "__main__":
    main()
