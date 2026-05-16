"""Print the seeded demo products as JSON.

Useful to sanity-check the demo data and to paste sample output into a
pitch deck. Run: ``python scripts/seed_demo.py``
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "apps" / "backend"))

from app.demo_data import DEMO_PRODUCTS  # noqa: E402

if __name__ == "__main__":
    payload = {k: v.model_dump() for k, v in DEMO_PRODUCTS.items()}
    print(json.dumps(payload, indent=2, ensure_ascii=False))
