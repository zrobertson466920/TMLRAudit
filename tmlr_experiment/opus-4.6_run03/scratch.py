import openreview

client = openreview.api.OpenReviewClient(baseurl='https://api2.openreview.net')

# Get total counts
for label, inv in [('Reviews', 'TMLR/-/Review'), ('Decisions', 'TMLR/-/Decision')]:
    result = client.get_notes(parent_invitations=inv, limit=1, with_count=True)
    print(f"{label} total: {result[0]}")

# Check Review_Release separately - maybe that's the public timestamp
result = client.get_notes(parent_invitations='TMLR/-/Review_Release', limit=3, with_count=True)
print(f"\nReview_Release total: {result[0]}")
if isinstance(result[1], list):
    for r in result[1][:3]:
        print(f"  forum={r.forum}, cdate={r.cdate}, invitations={r.invitations}")