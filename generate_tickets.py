"""Generate a synthetic help-desk ticket dataset for portfolio analysis.

The data is fully synthetic (random seed 42, fictional agent names) and exists
only to demonstrate analysis technique — it does not represent any real
company's tickets.

Columns:
    ticket_id            e.g. HD-0001
    created_date         when the ticket was opened
    resolved_date        when it was closed (blank if still open)
    category             ticket category
    priority             Low / Medium / High / Critical
    agent                assigned agent (fictional)
    satisfaction         user rating 1-5 (blank if unrated or still open)
    first_response_minutes  minutes until the first human response
"""

import csv
import random
from datetime import datetime, timedelta
from pathlib import Path

random.seed(42)

CATEGORIES = [
    "Password Reset",
    "VPN / Network",
    "Hardware",
    "Software Install",
    "Email / Outlook",
    "Printer",
    "Access Request",
    "Phishing / Malware",
]
PRIORITIES = ["Low", "Medium", "High", "Critical"]
PRIORITY_WEIGHTS = [0.35, 0.35, 0.22, 0.08]  # most tickets are low/medium
AGENTS = ["A. Sharma", "J. Chen", "M. Okafor", "S. Patel", "L. Tremblay", "D. Kim"]

# Typical resolution window (hours) by priority: (min, max)
RESOLUTION_WINDOW = {
    "Critical": (1, 6),
    "High": (4, 24),
    "Medium": (8, 48),
    "Low": (24, 96),
}
# Typical first-response window (minutes) by priority: (min, max)
FIRST_RESPONSE_WINDOW = {
    "Critical": (2, 15),
    "High": (10, 45),
    "Medium": (20, 120),
    "Low": (45, 240),
}

START = datetime(2026, 6, 1)
N_TICKETS = 500


def main() -> None:
    rows = []
    for i in range(1, N_TICKETS + 1):
        ticket_id = f"HD-{i:04d}"
        created = START + timedelta(
            days=random.randint(0, 83),
            hours=random.randint(0, 23),
            minutes=random.randint(0, 59),
        )
        category = random.choice(CATEGORIES)
        priority = random.choices(PRIORITIES, weights=PRIORITY_WEIGHTS)[0]
        agent = random.choice(AGENTS)

        lo, hi = FIRST_RESPONSE_WINDOW[priority]
        first_response_minutes = round(random.uniform(lo, hi), 1)

        if random.random() < 0.06:  # ~6% of tickets still open
            resolved_date, satisfaction = "", ""
        else:
            rlo, rhi = RESOLUTION_WINDOW[priority]
            # Hardware swaps and access approvals legitimately take longer.
            factor = 1.4 if category in ("Hardware", "Access Request") else 1.0
            hours = random.uniform(rlo, rhi) * factor
            resolved_date = (created + timedelta(hours=hours)).strftime("%Y-%m-%d %H:%M")
            # Satisfaction loosely follows speed: faster resolution -> happier user.
            base = 5 if hours < 12 else (4 if hours < 36 else 3)
            satisfaction = max(1, min(5, base + random.choice([-1, 0, 0, 0, 1])))
            if random.random() < 0.12:  # some users never rate
                satisfaction = ""

        rows.append(
            [
                ticket_id,
                created.strftime("%Y-%m-%d %H:%M"),
                resolved_date,
                category,
                priority,
                agent,
                satisfaction,
                first_response_minutes,
            ]
        )

    out = Path(__file__).parent / "tickets.csv"
    with open(out, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(
            [
                "ticket_id",
                "created_date",
                "resolved_date",
                "category",
                "priority",
                "agent",
                "satisfaction",
                "first_response_minutes",
            ]
        )
        writer.writerows(rows)
    print(f"Wrote {len(rows)} synthetic tickets to {out}")


if __name__ == "__main__":
    main()
