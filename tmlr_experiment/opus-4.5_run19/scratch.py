import openreview
import pandas as pd
import numpy as np

MS_PER_DAY = 1000 * 60 * 60 * 24

client = openreview.api.OpenReviewClient(baseurl='https://api2.openreview.net')

# Fetch all reviews and decisions in bulk
print("Fetching all TMLR reviews...")
all_reviews = client.get_all_notes(content={'venue': 'TMLR'}, invitation='TMLR/Paper.*/-/Review')
print(f"Found {len(all_reviews)} reviews")