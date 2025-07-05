import urllib.parse
import requests


def build_share_url(url: str) -> str:
    """Return a LinkedIn share URL for the given link."""
    query = urllib.parse.urlencode({"url": url})
    return f"https://www.linkedin.com/sharing/share-offsite/?{query}"


def post_to_linkedin(person_id: str, access_token: str, text: str, url: str) -> bool:
    """Post a simple update to LinkedIn using the UGC API."""
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
        "X-Restli-Protocol-Version": "2.0.0",
    }
    payload = {
        "author": f"urn:li:person:{person_id}",
        "lifecycleState": "PUBLISHED",
        "specificContent": {
            "com.linkedin.ugc.ShareContent": {
                "shareCommentary": {"text": text},
                "shareMediaCategory": "ARTICLE",
                "media": [{"status": "READY", "originalUrl": url}],
            }
        },
        "visibility": {"com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"},
    }
    resp = requests.post(
        "https://api.linkedin.com/v2/ugcPosts", json=payload, headers=headers
    )
    return resp.status_code == 201
