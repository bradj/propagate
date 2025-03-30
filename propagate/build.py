import json
from pathlib import Path
import os
from datetime import datetime
from pprint import pprint
class DateTimeEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            # format to YYYY-MM-DD
            return obj.strftime("%Y-%m-%d")
        return super().default(obj)

def main():
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
            if '12:01' in eo["effective_date"]:
                splits = eo["effective_date"].split(",")
                eo["effective_date"] = splits[0].strip() + ", " + splits[1].strip()
                eo["effective_date"] = datetime.strptime(eo["effective_date"], "%B %d, %Y")
            else:
                eo["effective_date"] = datetime.strptime(eo["effective_date"], "%B %d, %Y")
        except:
            pass

        no_specified_date_strings = ["No expiration date specified", "Not specified", "No expiration date is stated"]

        # find one of these strings in expiration_date
        if any(s in eo["expiration_date"] for s in no_specified_date_strings):
            eo["expiration_date"] = "No expiration date stated"
        else:
            try:
                eo["expiration_date"] = datetime.strptime(eo["expiration_date"], "%Y-%m-%d")
            except:
                # leave as is
                pass

        eo["publication_date"] = datetime.strptime(eo["publication_date"], "%Y-%m-%d")
        eo["signing_date"] = datetime.strptime(eo["signing_date"], "%Y-%m-%d")
        # timestamp is a float in seconds since epoch
        eo["timestamp"] = datetime.fromtimestamp(float(eo["timestamp"]))

    # order by publication date descending
    eo_data.sort(key=lambda x: x["publication_date"], reverse=True)

    with open("eo/eo.json", "w") as f:
        json.dump(eo_data, f, cls=DateTimeEncoder)


if __name__ == "__main__":
    main()
