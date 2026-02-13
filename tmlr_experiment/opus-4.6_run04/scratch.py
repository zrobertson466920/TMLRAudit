import openreview
import time

client = openreview.api.OpenReviewClient(baseurl='https://api2.openreview.net')

# Bulk fetch all reviews and decisions using parent_invitations
print("Fetching all TMLR reviews...", flush=True)
t0 = time.time()
all_reviews = client.get_all_notes(parent_invitations='TMLR/-/Review')
print(f"  Got {len(all_reviews)} reviews in {time.time()-t0:.1f}s", flush=True)

print("Fetching all TMLR decisions...", flush=True)
t1 = time.time()
all_decisions = client.get_all_notes(parent_invitations='TMLR/-/Decision')
print(f"  Got {len(all_decisions)} decisions in {time.time()-t1:.1f}s", flush=True)

# Show a few examples
print("\nSample reviews:")
for r in all_reviews[:3]:
    print(f"  forum={r.forum}, cdate={r.cdate}, invitations={r.invitations}")

print("\nSample decisions:")
for d in all_decisions[:3]:
    print(f"  forum={d.forum}, cdate={d.cdate}, invitations={d.invitations}")

# Check: how many unique forums?
rev_forums = set(r.forum for r in all_reviews)
dec_forums = set(d.forum for d in all_decisions)
print(f"\nUnique forums with reviews: {len(rev_forums)}")
print(f"Unique forums with decisions: {len(dec_forums)}")
print(f"Forums with both: {len(rev_forums & dec_forums)}")