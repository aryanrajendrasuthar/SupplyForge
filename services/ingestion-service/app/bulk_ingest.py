import csv
import io
import json


def parse_bulk_ingest(filename: str, raw: bytes) -> list[dict]:
    """Returns a list of record payloads. CSV rows become flat dicts; a JSON
    file must contain a top-level array of payload objects."""
    if filename.lower().endswith(".json"):
        data = json.loads(raw.decode("utf-8"))
        if not isinstance(data, list):
            raise ValueError("JSON bulk ingest must be a list of record payloads")
        return data

    reader = csv.DictReader(io.StringIO(raw.decode("utf-8")))
    return [dict(row) for row in reader]
