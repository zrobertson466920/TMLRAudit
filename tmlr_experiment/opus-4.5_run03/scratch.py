import openreview

client = openreview.api.OpenReviewClient(baseurl='https://api2.openreview.net')

# Test different invitation patterns
print("Testing invitation patterns...")

# The invitations we saw were like 'TMLR/Paper6656/-/Review'
# Try with a specific paper number first
test_reviews = client.get_notes(invitation='TMLR/Paper6656/-/Review', limit=5)
print(f"Specific paper review: {len(test_reviews)}")

# Try getting all notes and filtering - use signature pattern for reviewers
# Reviewers sign as TMLR/Paper{N}/Reviewer_XXX
print("\nTrying to get reviews via replyto (replies to submissions)...")

# Get a few submissions first
subs = client.get_notes(invitation='TMLR/-/Submission', limit=10)
print(f"Got {len(subs)} test submissions")

# Check replies to first submission
for sub in subs[:3]:
    replies = client.get_notes(forum=sub.forum)
    n_reviews = sum(1 for r in replies if any('/Review' in inv for inv in r.invitations))
    n_decisions = sum(1 for r in replies if any('/Decision' in inv for inv in r.invitations))
    print(f"  Forum {sub.forum}: {n_reviews} reviews, {n_decisions} decisions, {len(replies)} total notes")