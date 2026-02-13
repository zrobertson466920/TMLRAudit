import openreview
import pandas as pd
import numpy as np

client = openreview.api.OpenReviewClient(baseurl='https://api2.openreview.net')

print("Fetching TMLR submissions...")
submissions = list(client.get_all_notes(invitation='TMLR/-/Submission', details='replies'))
print(f"Found {len(submissions)} submissions")

records = []
for note in submissions:
    replies = note.details.get('replies', []) if note.details else []
    
    # Find review timestamps (invitations list containing 'Review' but not 'Review_Release')
    review_times = [r['cdate'] for r in replies 
                    if any('/-/Review' in inv and 'Release' not in inv for inv in r.get('invitations', []))]
    t_third_review = sorted(review_times)[2] if len(review_times) >= 3 else None
    
    # Find decision timestamp
    decision_times = [r['cdate'] for r in replies 
                      if any('Decision' in inv for inv in r.get('invitations', []))]
    t_decision = min(decision_times) if decision_times else None
    
    records.append({
        'id': note.id,
        'n_reviews': len(review_times),
        't_third_review': t_third_review,
        't_decision': t_decision,
        'censored': t_decision is None
    })

df = pd.DataFrame(records)

# Compute gap: from third review to decision
df['gap_days'] = np.where(
    ~df['censored'] & df['t_third_review'].notna(),
    (df['t_decision'] - df['t_third_review']) / (1000 * 60 * 60 * 24),
    np.nan
)

# Filter to uncensored with valid gaps
analysis_df = df[~df['censored'] & df['gap_days'].notna() & (df['gap_days'] > 0)]
gaps = analysis_df['gap_days']

n = len(gaps)
quantiles = gaps.quantile([0.5, 0.75, 0.90, 0.95, 0.99])
pct_over_28 = (gaps > 28).mean() * 100
pct_over_35 = (gaps > 35).mean() * 100
pct_over_42 = (gaps > 42).mean() * 100

print(f"""
=== TMLR Audit Results ===
N (uncensored with 3+ reviews): {n}

Quantiles (days from 3rd review to decision):
  Median: {quantiles[0.5]:.1f}
  75th:   {quantiles[0.75]:.1f}
  90th:   {quantiles[0.90]:.1f}
  95th:   {quantiles[0.95]:.1f}
  99th:   {quantiles[0.99]:.1f}

Compliance with stated "no later than 5 weeks" (35 days):
  Share > 28 days: {pct_over_28:.1f}%
  Share > 35 days: {pct_over_35:.1f}% (violates stated max)
  Share > 42 days: {pct_over_42:.1f}%

Context:
  Total submissions: {len(df)}
  With 3+ reviews: {(df['n_reviews'] >= 3).sum()}
  With decisions: {(~df['censored']).sum()}
  Pending (no decision): {df['censored'].sum()}
""")