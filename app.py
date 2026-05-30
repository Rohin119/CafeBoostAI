import os
import time
from flask import Flask, request, jsonify, render_template, Response
from flask_cors import CORS
from wire import scrape_website
from gemini import analyze_with_gemini

from io import BytesIO
from flask import send_file

from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer
)

from reportlab.lib.styles import getSampleStyleSheet


app = Flask(__name__)
CORS(app)
latest_html = ""
latest_report = {}

# Simple in-memory rate limiting
request_counts = {}

def rate_limit_check(ip):
    now = time.time()
    if ip not in request_counts:
        request_counts[ip] = []
    # Keep only requests in the last 60 seconds
    request_counts[ip] = [t for t in request_counts[ip] if now - t < 60]
    if len(request_counts[ip]) >= 5:
        return False
    request_counts[ip].append(now)
    return True

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/analyze", methods=["POST"])
def analyze():
    # Get client IP for rate limiting
    client_ip = request.headers.get("X-Forwarded-For", request.remote_addr)

    if not rate_limit_check(client_ip):
        return jsonify({"error": "Rate limit exceeded. Please wait a minute before trying again."}), 429

    data = request.get_json()
    if not data or "url" not in data:
        return jsonify({"error": "URL is required."}), 400

    url = data["url"].strip()
    if not url:
        return jsonify({"error": "URL cannot be empty."}), 400

    # Basic URL validation
    if not url.startswith(("http://", "https://")):
        url = "https://" + url

    try:
        # Step 1: Scrape website using Anakin Wire
        print(f"[CafeBoost] Scraping: {url}")
        global latest_html

        website_content = scrape_website(url)

        latest_html = website_content

        if not website_content:
         return jsonify({"error": "Could not retrieve website content. Please check the URL and try again."}), 400
        
        # Step 2: Analyze with Gemini
        print("[CafeBoost] Sending to Gemini for analysis...")
        report = analyze_with_gemini(website_content, url)
        global latest_report
        latest_report = report

        return jsonify({"success": True, "report": report})

    except Exception as e:
        print(f"[CafeBoost] Error: {str(e)}")
        return jsonify({"error": f"Analysis failed: {str(e)}"}), 500
    
@app.route("/download-html")
def download_html():

    global latest_html

    if not latest_html:
        return "No HTML available. Run an analysis first."

    return Response(
        latest_html,
        mimetype="text/html",
        headers={
            "Content-Disposition":
            "attachment; filename=website.html"
        }
    )

@app.route("/download-pdf")
def download_pdf():

    global latest_report

    if not latest_report:
        return "No report available"

    buffer = BytesIO()

    doc = SimpleDocTemplate(buffer)

    styles = getSampleStyleSheet()

    content = []

    content.append(
        Paragraph("CafeBoost AI Report", styles["Title"])
    )

    content.append(Spacer(1, 12))

    content.append(
        Paragraph(
            f"Overall Score: {latest_report.get('overall_score',0)}",
            styles["Normal"]
        )
    )

    content.append(
        Paragraph(
            f"SEO Score: {latest_report.get('seo_score',0)}",
            styles["Normal"]
        )
    )

    content.append(
        Paragraph(
            f"UX Score: {latest_report.get('ux_score',0)}",
            styles["Normal"]
        )
    )

    content.append(
        Paragraph(
            f"Business Score: {latest_report.get('business_score',0)}",
            styles["Normal"]
        )
    )

    content.append(Spacer(1, 20))

    content.append(
        Paragraph(
            "Executive Summary",
            styles["Heading2"]
        )
    )

    content.append(
        Paragraph(
            latest_report.get("summary",""),
            styles["BodyText"]
        )
    )

    doc.build(content)

    buffer.seek(0)

    return send_file(
        buffer,
        as_attachment=True,
        download_name="CafeBoost_Report.pdf",
        mimetype="application/pdf"
    )


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    debug = os.environ.get("FLASK_ENV", "production") == "development"
    app.run(host="0.0.0.0", port=port, debug=debug)