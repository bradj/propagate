#!/usr/bin/env python3
from propagate.db import PropagateDB


def format_status(db: PropagateDB) -> str:
    runs = db.get_recent_runs(limit=10)

    if not runs:
        return "No runs recorded yet."

    lines = []

    last = runs[0]
    last_time = last["started_at"][:16].replace("T", " ") + " UTC"
    eos_new = last.get("eos_new") or 0
    status_str = last["status"]
    if eos_new > 0:
        status_str += f" ({eos_new} new EOs)"
    if last.get("deployed"):
        status_str += ", deployed"
    lines.append(f"Last run:     {last_time} — {status_str}")

    if last.get("error"):
        lines.append(f"Error:        {last['error']}")

    if last.get("eos_found") is not None:
        eos_found = last["eos_found"]
        total_processed_row = db._connect().execute(
            "SELECT COUNT(DISTINCT eo_number) FROM eos WHERE president = ?",
            (last["president"],)
        ).fetchone()
        total_processed = total_processed_row[0] if total_processed_row else 0
        lines.append(
            f"EOs:          {eos_found} found,"
            f" {total_processed} ever processed"
        )

    if last.get("batch_id"):
        poll = last.get("poll_seconds") or 0
        minutes = poll // 60
        seconds = poll % 60
        lines.append(
            f"Last batch:   {last['batch_id']}"
            f" (completed in {minutes}m {seconds}s)"
        )

    lines.append("")
    lines.append("Recent runs:")
    for run in runs:
        date = run["started_at"][:10]
        status = run["status"]
        eos = run.get("eos_new")
        eo_str = f"{eos} new EOs" if eos and eos > 0 else "no new EOs"
        deployed = "deployed" if run.get("deployed") else ""
        error = run.get("error") or ""
        if status == "failed":
            eo_str = error[:40] if error else "—"
        line = f"  {date}  {status:<16} {eo_str:<20} {deployed}"
        lines.append(line.rstrip())

    return "\n".join(lines)


def main():
    db = PropagateDB()
    print(format_status(db))


if __name__ == "__main__":
    main()
