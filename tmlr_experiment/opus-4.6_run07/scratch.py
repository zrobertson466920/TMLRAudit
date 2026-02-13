import openreview
import time

client = openreview.api.OpenReviewClient(baseurl='https://api2.openreview.net')

# Strategy: fetch all submissions first, then batch-fetch reviews and decisions
# by using specific invitation per paper but in rapid succession

# First, get all submission numbers
print("Fetching all TMLR submissions...")
submissions = client.get_all_notes(invitation='TMLR/-/Submission')
print(f"Fetched {len(submissions)} submissions")

# Build a dict: number -> forum_id
sub_map = {s.number: s.forum for s in submissions}
numbers = sorted(sub_map.keys())
print(f"Paper numbers range: {numbers[0]} to {numbers[-1]}")

# Now try: can we fetch ALL reviews across all papers with a single call?
# The invitation format is TMLR/Paper{N}/-/Review
# Let's try content-based or signature-based approaches

# Check if there's an invitation group we can use
print("\nTrying to get invitations list...")
try:
    invitations = client.get_all_invitations(prefix='TMLR/-/')
    print(f"Got {len(invitations)} invitations with prefix TMLR/-/")
    for inv in invitations[:20]:
        print(f"  {inv.id}")
except Exception as e:
    print(f"Error: {e}")

# Try regex pattern with proper OpenReview v2 syntax
print("\nTrying regex patterns...")
for pattern in [
    'TMLR/Paper.*/-/Review',
    'TMLR/Paper.*/-/Decision', 
    'TMLR/.*/Review',
    'TMLR/.*/Decision',
]:
    try:
        notes = client.get_notes(invitation=pattern, limit=3)
        print(f"  '{pattern}': {len(notes)} notes")
    except Exception as e:
        print(f"  '{pattern}': error {type(e).__name__}: {e}")

# What about using the invitation search with regex flag?
print("\nTrying with invitation regex...")
try:
    notes = client.get_notes(content={'venue': 'TMLR'}, limit=3)
    print(f"Content venue search: {len(notes)}")
except Exception as e:
    print(f"Content search error: {e}")

# Let's time how fast individual paper queries are
print("\nTiming individual paper review+decision fetches...")
t0 = time.time()
count = 0
for num in numbers[:50]:
    try:
        reviews = client.get_notes(invitation=f'TMLR/Paper{num}/-/Review', limit=10)
        decisions = client.get_notes(invitation=f'TMLR/Paper{num}/-/Decision', limit=5)
        count += 1
    except:
        pass
elapsed = time.time() - t0
print(f"  50 papers: {elapsed:.1f}s ({elapsed/50*1000:.0f}ms per paper)")
print(f"  Estimated for {len(numbers)} papers: {elapsed/50*len(numbers)/60:.1f} min")