import openreview

client = openreview.api.OpenReviewClient(baseurl='https://api2.openreview.net')

# content.venueid worked - let's explore what venue IDs exist
print("Exploring venue-based queries...")
for vid in ['TMLR', 'TMLR/Accepted', 'TMLR/Rejected', 'TMLR/Withdrawn']:
    try:
        notes = client.get_notes(content={'venueid': vid}, limit=3)
        print(f"  venueid='{vid}': {len(notes)} notes")
        if notes:
            n = notes[0]
            print(f"    sample: forum={n.forum} invitations={n.invitations}")
            if hasattr(n.content, 'get'):
                print(f"    content keys: {list(n.content.keys())[:10]}")
            else:
                print(f"    content type: {type(n.content)}")
    except Exception as e:
        print(f"  venueid='{vid}': Error - {e}")

# Also check: can we query notes by signature pattern or other bulk methods?
# Let's see if there's an invitation for all decisions at venue level
print("\nTrying to find decision/review invitations...")
for inv in ['TMLR/-/Review', 'TMLR/-/Official_Review', 'TMLR/-/Decision', 
            'TMLR/-/Acceptance_Decision']:
    notes = client.get_notes(invitation=inv, limit=3)
    print(f"  {inv}: {len(notes)} notes")