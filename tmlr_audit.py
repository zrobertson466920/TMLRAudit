import openreview
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import os

# Connect to OpenReview API
client = openreview.api.OpenReviewClient(baseurl='https://api2.openreview.net')

print("Fetching TMLR submissions...")
submissions = client.get_all_notes(invitation='TMLR/-/Submission', details='replies')
print(f"Found {len(submissions)} submissions")

records = []
for note in submissions:
    replies = note.details.get('replies', [])
    review_times = []
    decision_time = None
    decision_content = None

    for reply in replies:
        invitations = reply.get('invitations', [])
        cdate = reply.get('cdate')
        if cdate is None:
            continue
        for inv in invitations:
            if '/Review' in inv and 'Official_Recommendation' not in inv:
                review_times.append(cdate)
                break
            if '/Decision' in inv:
                if decision_time is None or cdate < decision_time:
                    decision_time = cdate
                    decision_content = reply.get('content', {})
                break

    review_times_sorted = sorted(review_times)
    t_third_review = review_times_sorted[2] if len(review_times_sorted) >= 3 else None

    # Extract decision recommendation
    rec = ''
    if decision_content:
        rec = decision_content.get('recommendation', '')
        if isinstance(rec, dict):
            rec = rec.get('value', '')
        rec = str(rec).lower()

    records.append({
        'id': note.id,
        'n_reviews': len(review_times),
        't_third_review': t_third_review,
        't_decision': decision_time,
        'censored': decision_time is None,
        'recommendation': rec
    })

df = pd.DataFrame(records)
ms_per_day = 1000 * 60 * 60 * 24

df['gap_days'] = (df['t_decision'] - df['t_third_review']) / ms_per_day
analysis = df[(~df['censored']) & (df['t_third_review'].notna()) & (df['gap_days'] >= 0)].copy()

os.makedirs('images', exist_ok=True)

print(f"N = {len(analysis)}")
print(f"Median: {analysis['gap_days'].median():.1f}")

# --- Print audit statistics ---
gaps = analysis['gap_days']
print(f"\n=== TMLR Audit Results ===")
print(f"N (uncensored): {len(analysis)}")
print(f"\nQuantiles (days from 3rd review to decision):")
print(f"  Median: {gaps.quantile(0.50):.1f}")
print(f"  75th:   {gaps.quantile(0.75):.1f}")
print(f"  90th:   {gaps.quantile(0.90):.1f}")
print(f"  95th:   {gaps.quantile(0.95):.1f}")
print(f"  99th:   {gaps.quantile(0.99):.1f}")
print(f"\nCompliance:")
print(f"  Share > 28 days: {(gaps > 28).mean() * 100:.1f}%")
print(f"  Share > 35 days: {(gaps > 35).mean() * 100:.1f}%")
print(f"  Share > 42 days: {(gaps > 42).mean() * 100:.1f}%")
print(f"\nCensored (no decision yet): {df['censored'].sum()}")

# --- Figure 1: Histogram by week ---
fig, ax = plt.subplots(figsize=(10, 5))

max_weeks = 20
gaps_weeks = analysis['gap_days'] / 7
bins = np.arange(0, max_weeks + 1, 1)

counts, bin_edges, patches = ax.hist(gaps_weeks.clip(upper=max_weeks), bins=bins,
                                      edgecolor='white', linewidth=0.5)

for patch, left_edge in zip(patches, bin_edges[:-1]):
    if left_edge < 4:
        patch.set_facecolor('#2ecc71')
    elif left_edge < 5:
        patch.set_facecolor('#f39c12')
    else:
        patch.set_facecolor('#e74c3c')

ax.axvline(x=4, color='#27ae60', linestyle='--', linewidth=2, label='4-week reviewer deadline')
ax.axvline(x=5, color='#e67e22', linestyle='--', linewidth=2, label='5-week AE target')

ax.set_xlabel('Weeks from third review to decision', fontsize=12)
ax.set_ylabel('Number of submissions', fontsize=12)
ax.set_title('Distribution of TMLR Decision Times (N = {:,})'.format(len(analysis)), fontsize=14)
ax.legend(fontsize=10)
ax.set_xlim(0, max_weeks)
ax.xaxis.set_major_locator(mticker.MultipleLocator(2))
ax.xaxis.set_minor_locator(mticker.MultipleLocator(1))

pct_within_4 = (analysis['gap_days'] <= 28).mean() * 100
ax.annotate(f'{pct_within_4:.1f}% within 4 weeks',
            xy=(4, counts[3] if len(counts) > 3 else 0),
            xytext=(8, max(counts) * 0.85),
            fontsize=11, fontweight='bold',
            arrowprops=dict(arrowstyle='->', color='#27ae60'),
            color='#27ae60')

plt.tight_layout()
plt.savefig('images/tmlr_histogram.png', dpi=150)
print("\nSaved images/tmlr_histogram.png")

# --- Figure 2: Median by year ---
analysis['decision_date'] = pd.to_datetime(analysis['t_decision'], unit='ms')
analysis['decision_year'] = analysis['decision_date'].dt.year

yearly = analysis.groupby('decision_year').agg(
    median_days=('gap_days', 'median'),
    p25=('gap_days', lambda x: x.quantile(0.25)),
    p75=('gap_days', lambda x: x.quantile(0.75)),
    count=('gap_days', 'count')
).reset_index()

yearly = yearly[yearly['count'] >= 20]

fig2, ax2 = plt.subplots(figsize=(8, 5))

ax2.plot(yearly['decision_year'], yearly['median_days'], 'o-', color='#2c3e50',
         linewidth=2.5, markersize=8, label='Median', zorder=3)
ax2.fill_between(yearly['decision_year'], yearly['p25'], yearly['p75'],
                 alpha=0.2, color='#3498db', label='25th–75th percentile')

ax2.axhline(y=28, color='#27ae60', linestyle='--', linewidth=1.5, label='4-week target')
ax2.axhline(y=35, color='#e67e22', linestyle='--', linewidth=1.5, label='5-week target')

for _, row in yearly.iterrows():
    ax2.annotate(f'n={int(row["count"])}',
                xy=(row['decision_year'], row['median_days']),
                xytext=(0, 10), textcoords='offset points',
                fontsize=9, fontweight='bold', ha='center', color='#2c3e50')

ax2.set_xlabel('Year of decision', fontsize=12)
ax2.set_ylabel('Days from third review to decision', fontsize=12)
ax2.set_title('TMLR Median Decision Time by Year', fontsize=14)
ax2.legend(fontsize=10, loc='lower left')
ax2.set_ylim(0, None)
ax2.xaxis.set_major_locator(mticker.MaxNLocator(integer=True))

plt.tight_layout()
plt.savefig('images/tmlr_yearly.png', dpi=150)
print("Saved images/tmlr_yearly.png")

print("\n=== Yearly Breakdown ===")
for _, row in yearly.iterrows():
    print(f"  {int(row['decision_year'])}: median={row['median_days']:.1f} days, "
          f"IQR=[{row['p25']:.0f}, {row['p75']:.0f}], n={int(row['count'])}")

# --- Figure 3: Rejection rate by wait time ---
outcome = analysis[analysis['recommendation'] != ''].copy()
outcome['rejected'] = outcome['recommendation'].str.contains('reject')
outcome['accepted'] = outcome['recommendation'].str.contains('accept') & ~outcome['rejected']

print(f"\n=== Decision Outcomes ===")
print(f"Papers with outcome data: {len(outcome)}")
for r in sorted(outcome['recommendation'].unique()):
    print(f"  {r}: {(outcome['recommendation'] == r).sum()}")

bins_rej = np.arange(0, outcome['gap_days'].max() + 5, 5)
outcome['bin'] = pd.cut(outcome['gap_days'], bins=bins_rej)

grouped = outcome.groupby('bin', observed=True).agg(
    n=('rejected', 'size'),
    n_rejected=('rejected', 'sum'),
    n_accepted=('accepted', 'sum')
).reset_index()
grouped['rejection_rate'] = grouped['n_rejected'] / grouped['n']
grouped['acceptance_rate'] = grouped['n_accepted'] / grouped['n']
grouped['bin_mid'] = grouped['bin'].apply(lambda x: x.mid)

# Filter to bins with meaningful sample size
grouped = grouped[grouped['n'] >= 20]

fig3, ax3_main = plt.subplots(figsize=(10, 6))

# Bar chart for sample sizes
ax3_twin = ax3_main.twinx()
ax3_twin.bar(grouped['bin_mid'], grouped['n'], width=4, alpha=0.4, color='#cccccc', label='N per bin')
ax3_twin.set_ylabel('N (submissions per 5-day bin)', color='gray')
ax3_twin.tick_params(axis='y', labelcolor='gray')

# Line plot for rejection rate
ax3_main.plot(grouped['bin_mid'], grouped['rejection_rate'] * 100, 'o-', color='firebrick',
              linewidth=2, markersize=5, label='Rejection rate', zorder=5)
ax3_main.set_xlabel('Days from 3rd review to decision', fontsize=12)
ax3_main.set_ylabel('Rejection rate (%)', color='firebrick', fontsize=12)
ax3_main.tick_params(axis='y', labelcolor='firebrick')

# Reference lines
ax3_main.axvline(x=28, color='#27ae60', linestyle='--', linewidth=1.5, label='4-week reviewer deadline')
ax3_main.axvline(x=35, color='#e67e22', linestyle='--', linewidth=1.5, label='5-week AE target')

ax3_main.set_title('TMLR: Rejection Rate by Decision Wait Time (N = {:,})'.format(len(outcome)), fontsize=14)
ax3_main.set_xlim(0, 105)
ax3_main.set_ylim(0, 50)

# Combined legend
lines1, labels1 = ax3_main.get_legend_handles_labels()
lines2, labels2 = ax3_twin.get_legend_handles_labels()
ax3_main.legend(lines1 + lines2, labels1 + labels2, loc='upper right', fontsize=10)

plt.tight_layout()
plt.savefig('images/tmlr_rejection_by_wait.png', dpi=150)
print("\nSaved images/tmlr_rejection_by_wait.png")

# Print summary table by coarse bins
print("\n=== Rejection Rate by Wait Time (Coarse) ===")
coarse_bins = [(15, 35), (35, 55), (55, 75), (75, 100)]
for lo, hi in coarse_bins:
    mask = (outcome['gap_days'] > lo) & (outcome['gap_days'] <= hi)
    subset = outcome[mask]
    if len(subset) > 0:
        rej_rate = subset['rejected'].mean() * 100
        print(f"  {lo}–{hi} days: N={len(subset)}, rejection rate={rej_rate:.1f}%")

print("\n=== Rejection Rate by Wait Time (5-day bins) ===")
print(f"{'Bin':>14} {'N':>6} {'Rej%':>7} {'Acc%':>7}")
for _, row in grouped.iterrows():
    print(f"{str(row['bin']):>14} {row['n']:>6.0f} {row['rejection_rate']*100:>6.1f}% {row['acceptance_rate']*100:>6.1f}%")