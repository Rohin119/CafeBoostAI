import os
import json
import re
import google.generativeai as genai



GEMINI_API_KEY = "AQ.Ab8RN6JlClW0ZihXGd4xTT5mOr1fJVZh-iQSSdEmvmOwnImjFw"

genai.configure(api_key=GEMINI_API_KEY)

ANALYSIS_PROMPT = """You are an expert cafe website consultant and digital marketing specialist with 15+ years of experience.

Analyze the following cafe website content thoroughly and return a detailed JSON report.

WEBSITE URL: {url}

WEBSITE CONTENT:
{content}

---

Your analysis must be thorough, specific, and actionable. Reference actual details from the website content.

Return ONLY a valid JSON object (no markdown, no backticks, no extra text) with exactly this structure:

{{
  "overall_score": <integer 0-100>,
  "seo_score": <integer 0-100>,
  "ux_score": <integer 0-100>,
  "business_score": <integer 0-100>,
  "score_breakdown": {{
    "overall_reasoning": "<2-3 sentences explaining the overall score>",
    "seo_reasoning": "<2-3 sentences explaining the SEO score>",
    "ux_reasoning": "<2-3 sentences explaining the UX score>",
    "business_reasoning": "<2-3 sentences explaining the business score>"
  }},
  "problems": [
    "<specific problem 1>",
    "<specific problem 2>",
    "<specific problem 3>",
    "<specific problem 4>",
    "<specific problem 5>"
  ],
  "missing_features": [
    "<missing feature 1>",
    "<missing feature 2>",
    "<missing feature 3>",
    "<missing feature 4>"
  ],
  "marketing_suggestions": [
    "<marketing suggestion 1>",
    "<marketing suggestion 2>",
    "<marketing suggestion 3>",
    "<marketing suggestion 4>"
  ],
  "improvements": [
    {{
      "title": "<short improvement title>",
      "description": "<detailed actionable description>",
      "priority": "<High|Medium|Low>",
      "impact": "<High|Medium|Low>"
    }},
    {{
      "title": "<short improvement title>",
      "description": "<detailed actionable description>",
      "priority": "<High|Medium|Low>",
      "impact": "<High|Medium|Low>"
    }},
    {{
      "title": "<short improvement title>",
      "description": "<detailed actionable description>",
      "priority": "<High|Medium|Low>",
      "impact": "<High|Medium|Low>"
    }},
    {{
      "title": "<short improvement title>",
      "description": "<detailed actionable description>",
      "priority": "<High|Medium|Low>",
      "impact": "<High|Medium|Low>"
    }},
    {{
      "title": "<short improvement title>",
      "description": "<detailed actionable description>",
      "priority": "<High|Medium|Low>",
      "impact": "<High|Medium|Low>"
    }}
  ],
  "priority_fixes": [
    "<priority fix 1 - most urgent>",
    "<priority fix 2>",
    "<priority fix 3>"
  ],
  "summary": "<3-4 sentence executive summary of the website's current state and potential>",
  "strengths": [
    "<strength 1>",
    "<strength 2>",
    "<strength 3>"
  ]
}}

Be specific and reference actual content from the website. Avoid generic advice — every recommendation should be tailored to this specific cafe.
"""


def analyze_with_gemini(content: str, url: str) -> dict:
    """
    Send extracted website content to Google Gemini for analysis.
    Returns structured JSON report.
    """
    if not GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY environment variable is not set.")

    # Trim content if too long (Gemini has context limits)
    max_content_length = 30000
    if len(content) > max_content_length:
        content = content[:max_content_length] + "\n\n[Content truncated for analysis]"
        print(f"[Gemini] Content trimmed to {max_content_length} chars")

    prompt = ANALYSIS_PROMPT.format(url=url, content=content)

    try:
        model = genai.GenerativeModel(
            model_name="gemini-2.5-flash",
            generation_config={
                "temperature": 0.3,
                "top_p": 0.95,
                "top_k": 40,
                "max_output_tokens": 8192,
            },
        )

        print("[Gemini] Sending analysis request...")
        response = model.generate_content(prompt)

        raw_text = response.text.strip()

        print(f"[Gemini] Received response ({len(raw_text)} chars)")

        print("\n========== GEMINI RAW RESPONSE ==========")
        print(raw_text)
        print("========== END RESPONSE ==========\n")

# Parse JSON from response
        report = _parse_json_response(raw_text)

        return report

    except Exception as e:
        print(f"[Gemini] Error: {str(e)}")
        raise Exception(f"Gemini analysis failed: {str(e)}")


def _parse_json_response(raw_text: str) -> dict:
    """
    Robustly parse JSON from Gemini response.
    Handles markdown code blocks and other formatting.
    """
    # Remove markdown code fences if present
    text = raw_text.strip()
    text = re.sub(r"^```(?:json)?\s*", "", text)
    text = re.sub(r"\s*```$", "", text)
    text = text.strip()

    try:
        data = json.loads(text)
        return _validate_and_normalize(data)
    except json.JSONDecodeError:
        # Try to extract JSON object from text
        json_match = re.search(r"\{[\s\S]*\}", text)
        if json_match:
            try:
                data = json.loads(json_match.group())
                return _validate_and_normalize(data)
            except json.JSONDecodeError:
                pass

    # Return a default structure if parsing fails entirely
    print("[Gemini] Warning: Could not parse JSON response, returning default structure")
    return _default_report()


def _validate_and_normalize(data: dict) -> dict:
    """Ensure all required fields exist with sensible defaults."""
    def clamp(val, lo=0, hi=100):
        try:
            return max(lo, min(hi, int(val)))
        except (TypeError, ValueError):
            return 50

    return {
        "overall_score": clamp(data.get("overall_score", 50)),
        "seo_score": clamp(data.get("seo_score", 50)),
        "ux_score": clamp(data.get("ux_score", 50)),
        "business_score": clamp(data.get("business_score", 50)),
        "score_breakdown": data.get("score_breakdown", {
            "overall_reasoning": "Analysis completed.",
            "seo_reasoning": "SEO analysis completed.",
            "ux_reasoning": "UX analysis completed.",
            "business_reasoning": "Business analysis completed.",
        }),
        "problems": data.get("problems", []),
        "missing_features": data.get("missing_features", []),
        "marketing_suggestions": data.get("marketing_suggestions", []),
        "improvements": data.get("improvements", []),
        "priority_fixes": data.get("priority_fixes", []),
        "summary": data.get("summary", "Analysis completed successfully."),
        "strengths": data.get("strengths", []),
    }


def _default_report() -> dict:
    return {
        "overall_score": 50,
        "seo_score": 50,
        "ux_score": 50,
        "business_score": 50,
        "score_breakdown": {
            "overall_reasoning": "Unable to parse detailed analysis. Please try again.",
            "seo_reasoning": "Unable to parse SEO details.",
            "ux_reasoning": "Unable to parse UX details.",
            "business_reasoning": "Unable to parse business details.",
        },
        "problems": ["Analysis parsing error — please retry"],
        "missing_features": [],
        "marketing_suggestions": [],
        "improvements": [],
        "priority_fixes": [],
        "summary": "The analysis encountered a parsing error. Please try again.",
        "strengths": [],
    }