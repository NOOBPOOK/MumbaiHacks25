from supabase import create_client
import os
from dotenv import load_dotenv
from collections import defaultdict

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY) #type: ignore

TABLE_NAME = "Messages_Primary"
GROUP_BY_COLUMN = "final_hash"   # change to your column name

# -----------------------------
# 1. Read all records
# -----------------------------
response = supabase.table(TABLE_NAME).select("*").execute()
records = response.data

if not records:
    print("No records found.")
    exit()

# -----------------------------
# 2. Group by a column
# -----------------------------
groups = defaultdict(list)

for row in records:
    key = row[GROUP_BY_COLUMN]
    groups[key].append(row)

# Now `groups` is a dict like:
# {
#    "pending": [ {record1}, {record2}, ... ],
#    "completed": [ ... ],
# }

# -----------------------------
# 3. Print or use grouped records
# -----------------------------


from datetime import datetime
from collections import defaultdict

def parse_timestamp(ts):
    """
    Converts timestamp strings to Python datetime.
    Supports ISO formats from Supabase.
    """
    return datetime.fromisoformat(ts.replace("Z", "+00:00"))

def compute_virality(group_records):
    total_msgs = len(group_records)

    # Hard penalty for single-record groups
    if total_msgs == 1:
        return 1.0   # very low score

    timestamps = [parse_timestamp(r["msg_sent_at"]) for r in group_records]
    timestamps.sort()

    first = timestamps[0]
    last = timestamps[-1]

    # minutes difference (avoid div-by-zero)
    time_window_minutes = max((last - first).total_seconds() / 60, 1)

    # burstiness (messages per minute)
    burstiness = total_msgs / time_window_minutes

    # volume factor to penalize low-count groups
    volume_factor = min(total_msgs / 5, 1)

    # final score
    score = burstiness * 10 * volume_factor
    return round(min(score, 100), 2)

def compute_virality_for_groups(groups):
    """
    Input: groups = { key: [records...] }
    Output: list of tuples → (key, score, records)
    """
    results = []

    for key, records in groups.items():
        score = compute_virality(records)
        results.append((key, score, records))

    # Sort by virality descending
    results.sort(key=lambda x: x[1], reverse=True)
    return results

# -------------------------------------------------------
# EXAMPLE USAGE (plug after your grouping code)
# -------------------------------------------------------

virality_results = compute_virality_for_groups(groups)

print("\n===== GROUPS SORTED BY VIRALITY =====\n")
for key, score, records in virality_results:
    print(f"Group: {key} | Virality Score: {score}")

    # Sort this group's records by msg_sent_at (earliest to latest)
    sorted_records = sorted(records, key=lambda r: r["msg_sent_at"])

    # Pick the first message as the representative "most viral" indicator
    representative_record = sorted_records[0]

    print("Representative Viral Record:")
    print(representative_record)          # <-- prints only ONE record
    print(f"Record count: {len(records)}")
    print("----------------------------------")




