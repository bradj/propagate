from executive_order import ExecutiveOrder
from pathlib import Path
import os

SUMMARIES_DIR = Path(os.environ.get("PROPAGATE_SUMMARIES_DIR"))

def convert_to_json(obj):
    if isinstance(obj, set):
        return list(obj)
    if hasattr(obj, '__dict__'):
        return obj.__dict__
    return str(obj)


def get_claude_json_path(order: ExecutiveOrder) -> Path:
    return Path(f'{SUMMARIES_DIR}/EO-{order.executive_order_number}-claude.json')

def get_summary_path(order: ExecutiveOrder) -> Path:
    return Path(f'{SUMMARIES_DIR}/EO-{order.executive_order_number}.json')
