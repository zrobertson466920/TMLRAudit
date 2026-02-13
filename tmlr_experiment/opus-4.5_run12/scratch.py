import openreview
import pandas as pd
import numpy as np

client = openreview.api.OpenReviewClient(baseurl='https://api2.openreview.net')

print("Fetching TMLR submissions with replies...")
submissions = client.get_all_notes(
    invitation='TMLR/-/Submission',
    details='directReplies'
)
print(f"Found {len(submissions)} submissions")

# Extract timing data from directReplies
records = []
for note in submissions:
    replies = note.details.get('directReplies', []) if note.details else []
    
    review_times = []
    decision_time = None
    
    for r in replies:
        invitations = r.get('invitations', [])
        inv_str = invitations[0] if invitations else ""
        cdate = r.get('cdate')
        
        if '/-/Review' in inv_str and 'Release' not in inv_str:
            review_times.append(cdate)
        elif '/-/Decision' in inv_str:
            decision_time = cdate
    
    records.append({
        'forum': note.forum,
        't_third_review': sorted(review_times)[2] if len(review_times) >= 3 else None,
        't_decision': decision_time,
        'n_reviews': len(review_times)
    })

df = pd.DataFrame(records)

# Compute gap in days
df['gap_days'] = (df['t_decision'] - df['t_third_review']) / (1000 * 60 * 60 * 24)
df['censored'] = df['t_decision'].isna()

# Filter to uncensored with 3+ reviews
uncensored = df[(~df['censored']) & (df['gap_days'].notna()) & (df['n_reviews'] >= 3)]

n = len(uncensored)
gaps = uncensored['gap_days']

quantiles = gaps.quantile([0.5, 0.75, 0.90, 0.95, 0.99])
pct_28 = (gaps > 28).mean() * 100
pct_35 = (gaps > 35).mean() * 100
pct_42 = (gaps > 42).mean() * 100

print(f"""
=== TMLR Audit Results ===
N (uncensored with 3+ reviews): {n}

Quantiles (days from 3rd review to decision):
  Median: {quantiles[0.5]:.1f}
  75th:   {quantiles[0.75]:.1f}
  90th:   {quantiles[0.90]:.1f}
  95th:   {quantiles[0.95]:.1f}
  99th:   {quantiles[0.99]:.1f}

Compliance with stated timelines:
  Share > 28 days: {pct_28:.1f}% (violates "no later than 4 weeks")
  Share > 35 days: {pct_35:.1f}% (violates 5-week decision deadline)
  Share > 42 days: {pct_42:.1f}%

Additional stats:
  Total submissions: {len(df)}
  Still awaiting decision: {df['censored'].sum()}
  With <3 reviews: {(df['n_reviews'] < 3).sum()}
""")