import json
from pathlib import Path
import os
from datetime import datetime
from pprint import pprint
import sys
from util import (
    fetch_all_executive_orders,
    claude_json_to_summary,
    save_summary,
    get_summary_path,
)


class DateTimeEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            # format to YYYY-MM-DD
            return obj.strftime("%Y-%m-%d")
        return super().default(obj)


def build_from_claude_batch(jsonl_path: Path):
    """
    Build from a Claude batch.

    This will read from the jsonl_path.

    It will then save the summaries to a file.
    """
    eos = fetch_all_executive_orders()

    with open(jsonl_path, "r") as f:
        for line in f:
            l = json.loads(line)
            eo_number = int(l["custom_id"].split("-")[1])
            text = l["result"]["message"]["content"][0]["text"]
            claude_json = json.loads(text)

            # write to a file in the summaries directory
            with open(
                Path(os.getenv("PROPAGATE_SUMMARIES_DIR"))
                / f"EO-{eo_number}-claude.json",
                "w",
            ) as f:
                json.dump(claude_json, f, cls=DateTimeEncoder)

            order = [eo for eo in eos if eo.executive_order_number == eo_number][0]
            summary = claude_json_to_summary(claude_json, order)
            summary_path = get_summary_path(order)

            # Save summary
            saved_path = save_summary(summary, summary_path)
            print(f"Summary saved to {saved_path}")


def build_from_summaries():
    eo_dir = Path(os.getenv("PROPAGATE_SUMMARIES_DIR"))
    eo_files = list(eo_dir.glob("*.json"))
    eo_data = []

    # ignore eo.json
    for file in eo_files:
        if file.name == "eo.json" or "claude" in file.name:
            continue

        with open(file, "r") as f:
            obj = json.load(f)
            obj["timestamp"] = file.stat().st_mtime
            eo_data.append(obj)

    # convert these to date objects
    # effective_date, publication_date, signing_date
    for eo in eo_data:
        try:
            if "12:01" in eo["effective_date"]:
                splits = eo["effective_date"].split(",")
                eo["effective_date"] = splits[0].strip() + ", " + splits[1].strip()
                eo["effective_date"] = datetime.strptime(
                    eo["effective_date"], "%B %d, %Y"
                )
            else:
                eo["effective_date"] = datetime.strptime(
                    eo["effective_date"], "%B %d, %Y"
                )
        except:
            pass

        no_specified_date_strings = [
            "No expiration date specified",
            "Not specified",
            "No expiration date is stated",
        ]

        # find one of these strings in expiration_date
        if any(s in eo["expiration_date"] for s in no_specified_date_strings):
            eo["expiration_date"] = "No expiration date stated"
        else:
            try:
                eo["expiration_date"] = datetime.strptime(
                    eo["expiration_date"], "%Y-%m-%d"
                )
            except:
                # leave as is
                pass

        eo["publication_date"] = datetime.strptime(eo["publication_date"], "%Y-%m-%d")
        eo["signing_date"] = datetime.strptime(eo["signing_date"], "%Y-%m-%d")
        # timestamp is a float in seconds since epoch
        eo["timestamp"] = datetime.fromtimestamp(float(eo["timestamp"]))

    # order by executive order number descending
    eo_data.sort(key=lambda x: x["eo_number"], reverse=True)

    eo_json = {"eos": eo_data, "build_time": datetime.now().isoformat()}

    with open("eo/eo.json", "w") as f:
        json.dump(eo_json, f, cls=DateTimeEncoder)


if __name__ == "__main__":
    if len(sys.argv) == 2:
        p = Path(sys.argv[1])
        if p.exists():
            build_from_claude_batch(p)
        else:
            print(f"File {p} does not exist")

    build_from_summaries()
