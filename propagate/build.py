import json
from pathlib import Path
import os
from datetime import datetime

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
        if file.name == "eo.json":
            continue

        with open(file, "r") as f:
            eo_data.append(json.load(f))

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
            continue

        eo["publication_date"] = datetime.strptime(eo["publication_date"], "%Y-%m-%d")
        eo["signing_date"] = datetime.strptime(eo["signing_date"], "%Y-%m-%d")
        # timestamp is a float in seconds since epoch
        eo["timestamp"] = datetime.fromtimestamp(float(eo["timestamp"]))

    with open("eo/eo.json", "w") as f:
        json.dump(eo_data, f, cls=DateTimeEncoder)


if __name__ == "__main__":
    main()
