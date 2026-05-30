import os
import time
import requests

WIRE_API_KEY = "ask_caae98a80d36460d051413e3ea943cb1da98b097c9cc3a7bfa00550572099c48"
WIRE_BASE_URL = "https://api.anakin.io/v1/url-scraper"  # Adjust if endpoint differs

import requests
import time

WIRE_API_KEY = "ask_caae98a80d36460d051413e3ea943cb1da98b097c9cc3a7bfa00550572099c48"

def scrape_website(url):

    headers = {
        "Authorization": f"Bearer {WIRE_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "url": url,
        "country": "us",
        "useBrowser": False,
        "generateJson": False
    }

    response = requests.post(
        "https://api.anakin.io/v1/url-scraper",
        json=payload,
        headers=headers
    )

    print("STATUS:", response.status_code)
    print("BODY:", response.text)
    print("JSON RESPONSE:", response.json())

    result = response.json()

    print("FULL RESULT:")
    print(result)

    if "jobId" in result:

        job_id = result["jobId"]

        print("Job ID:", job_id)

        return _poll_job(job_id, headers)

    elif "data" in result:

        return _extract_content(result["data"])

    elif (
        "cleanedHtml" in result
        or "text" in result
        or "content" in result
    ):

        return _extract_content(result)

    else:

        raise Exception(
            f"Unexpected Wire response: {result}"
        )



def _poll_job(job_id: str, headers: dict, max_retries: int = 20, delay: int = 3) -> str:
    """Poll Wire API until job is complete."""
    print(f"[Wire] Polling job: {job_id}")
    for attempt in range(max_retries):
        time.sleep(delay)
        try:
            print(f"[Wire] Polling URL: https://api.anakin.io/v1/url-scraper/{job_id}")

            response = requests.get(
            f"https://api.anakin.io/v1/url-scraper/{job_id}",
            headers=headers,
            timeout=30,
               )
            print(type(response))
            print(response)
            
            response.raise_for_status()
            print("STATUS:", response.status_code)
            print("RESPONSE:")
            print(response.text)

            result = response.json()

            status = result.get("status", "").lower()
            if status in ("completed", "done", "success"):
                data = result.get("data", result)
                return _extract_content(data)
            elif status in ("failed", "error"):
                raise Exception(f"Wire scrape job failed: {result.get('error', 'Unknown error')}")
            else:
                print(f"[Wire] Job status: {status} (attempt {attempt + 1}/{max_retries})")

        except requests.exceptions.RequestException as e:
            print(f"[Wire] Poll error: {str(e)}")

    raise Exception("Wire scrape job timed out after maximum retries.")


def _extract_content(data: dict) -> str:
    """
    Extract the most useful text content from Wire API response.
    Tries multiple possible field names.
    """
    if not data or not isinstance(data, dict):
        return ""

    # Priority order of fields to check
    content_fields = [
        "cleanedHtml",
        "cleaned_html",
        "text",
        "content",
        "markdown",
        "body",
        "innerText",
        "textContent",
        "html",
    ]

    for field in content_fields:
        value = data.get(field)
        if value and isinstance(value, str) and len(value.strip()) > 50:
            print(f"[Wire] Extracted content from field: '{field}' ({len(value)} chars)")
            return value.strip()

    # If nested under "result" or "page"
    for nested_key in ("result", "page", "scrape"):
        nested = data.get(nested_key)
        if isinstance(nested, dict):
            content = _extract_content(nested)
            if content:
                return content

    # Last resort: concatenate all string values
    all_text = " ".join(
        str(v) for v in data.values()
        if isinstance(v, str) and len(v) > 20
    )
    if len(all_text) > 100:
        print(f"[Wire] Using concatenated content ({len(all_text)} chars)")
        return all_text

    return ""