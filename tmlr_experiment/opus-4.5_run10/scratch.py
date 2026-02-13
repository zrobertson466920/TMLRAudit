import openreview
import pandas as pd
import numpy as np
from collections import defaultdict

client = openreview.api.OpenReviewClient(baseurl='https://api2.openreview.net')

# Check what parameters get_all_notes accepts
import inspect
sig = inspect.signature(client.get_all_notes)
print(f"get_all_notes parameters: {list(sig.parameters.keys())}")

# Try with wildcard invitation pattern
print("\nTrying different invitation patterns...")
try:
    # Try with just the venue prefix
    test = client.get_all_notes(invitation='TMLR/-/Review')
    print(f"TMLR/-/Review: {len(test)} notes")
except Exception as e:
    print(f"TMLR/-/Review failed: {e}")

# Check if there's a different method
print(f"\nAvailable client methods: {[m for m in dir(client) if not m.startswith('_') and 'note' in m.lower()]}")