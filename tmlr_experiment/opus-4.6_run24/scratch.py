import openreview
import time

client = openreview.api.OpenReviewClient(baseurl='https://api2.openreview.net')

# Test: can we use replyInvitation to get all reviews across all papers?
# The invitation pattern for reviews is TMLR/Paper{N}/-/Review
# Let's try using the invitation group approach

# Try fetching notes by replyInvitation 
print("Testing bulk fetch approaches...")

# Approach: use get_all_notes with invitation for the submission, 
# then get direct replies via replyForum
# But first, let's see if we can use the V1 client for details='replies'

# Actually, let's try the V1 API endpoint
print("Trying V1 API...")
client_v1 = openreview.Client(baseurl='https://api.openreview.net')
try:
    notes_v1 = client_v1.get_notes(invitation='TMLR/-/Submission', details='replies', limit=2)
    print(f"V1: got {len(notes_v1)} notes")
    if notes_v1:
        replies = notes_v1[0].details.get('replies', [])
        print(f"  First note replies: {len(replies)}")
        for r in replies[:5]:
            print(f"    invitation={r.get('invitation','N/A')}, cdate={r.get('cdate','N/A')}")
except Exception as e:
    print(f"V1 Error: {type(e).__name__}: {e}")

# Alternative: fetch all notes that are replies to TMLR submissions
# by using content.venueid or similar
print("\nTrying to fetch all forum replies for a known forum...")
try:
    all_replies = client.get_all_notes(forum='sFGmQZ7GQf')
    print(f"Forum sFGmQZ7GQf: {len(all_replies)} notes")
except Exception as e:
    print(f"Error: {e}")

# Can we pass multiple forums? No. But we can try the 'details' with directReplies
print("\nTrying details='directReplies'...")
try:
    notes = client.get_notes(invitation='TMLR/-/Submission', details='directReplies', limit=2, sort='cdate:asc')
    for n in notes:
        dr = n.details.get('directReplies', [])
        print(f"  Paper {n.number}: {len(dr)} directReplies")
        for r in dr[:3]:
            print(f"    invitations={r.get('invitations','N/A')}, cdate={r.get('cdate','N/A')}")
except Exception as e:
    print(f"Error: {e}")