import json
from collections import Counter
from pathlib import Path

LOG_DIRECTORY_PATH = Path("logs/")
REPORTS_DIR = Path("reports")


def percentile(values, p):
    if not values:
        return None
    k = int((len(values) - 1) * p / 100)
    return values[k]


def main():
    latencies = []
    status_counts = Counter()

    for file_path in LOG_DIRECTORY_PATH.iterdir():
        if file_path.is_file() and file_path.suffix == ".jsonl":
            with file_path.open() as f:
                for line in f:
                    try:
                        event = json.loads(line)
                    except json.JSONDecodeError:
                        continue
                    if "latency_ms" in event:
                        latencies.append(event["latency_ms"])
                    if "status_code" in event:
                        status_counts[event["status_code"]] += 1

    sorted_latencies = sorted(latencies) if latencies else []

    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    summary_lines = [
        f"Total requests: {len(latencies)}",
        f"Status counts: {dict(status_counts)}",
        f"p50 latency: {percentile(sorted_latencies, 50)}",
        f"p95 latency: {percentile(sorted_latencies, 95)}",
        f"p99 latency: {percentile(sorted_latencies, 99)}",
    ]
    summary = "\n".join(summary_lines) + "\n"

    with REPORTS_DIR.joinpath("latency_summary.txt").open("w") as file:
        file.write(summary)


if __name__ == "__main__":
    main()
