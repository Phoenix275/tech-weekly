from flask import Flask, jsonify, render_template_string
import openai
import os
from apscheduler.schedulers.background import BackgroundScheduler
import datetime
import json

app = Flask(__name__)
application = app

openai.api_key = os.getenv("OPENAI_API_KEY")

def generate_newsletter():
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4-turbo",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a newsletter generator for baby boomers planning to sell their companies. "
                        "Generate a JSON object with exactly these keys: 'featured', 'quick_tips', 'spotlight', and 'looking_ahead'. "
                        "Ensure 'quick_tips' is an array of strings. Write the content so that it reads like a long, engaging blog post "
                        "with detailed explanations, creative tips, and insightful commentary. Output only the JSON without any extra text."
                    )
                },
                {
                    "role": "user",
                    "content": "Generate the detailed newsletter content for this week."
                }
            ],
            temperature=0.7,
            max_tokens=800
        )
        content = response.choices[0].message['content'].strip()
        # Debug: print the raw API response to the logs
        print("Raw API response:", content)
        # Remove markdown formatting if present
        if content.startswith("```") and content.endswith("```"):
            content = content.strip("```")
        newsletter_data = json.loads(content)
        return newsletter_data
    except Exception as e:
        print("Error generating newsletter:", e)
        return {
            "featured": "Error generating newsletter.",
            "quick_tips": ["Error generating newsletter."],
            "spotlight": "Error generating newsletter.",
            "looking_ahead": "Error generating newsletter."
        }

current_newsletter = generate_newsletter()

def update_newsletter():
    global current_newsletter
    current_newsletter = generate_newsletter()
    print("Newsletter updated at", datetime.datetime.now())

scheduler = BackgroundScheduler()
scheduler.add_job(update_newsletter, 'cron', day_of_week='mon', hour=9, minute=0)
scheduler.start()

@app.route("/")
def home():
    newsletter_html = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
      <meta charset="UTF-8">
      <meta name="viewport" content="width=device-width, initial-scale=1.0">
      <title>Business & Tech Weekly</title>
      <link rel="stylesheet" href="styles.css">
    </head>
    <body>
      <header>
        <h1>Business & Tech Weekly</h1>
        <p>Your trusted newsletter for business exits & tech insights – every Monday at 9 AM.</p>
      </header>
      <main class="container">
        <section class="newsletter-section">
          <h2>Featured Article</h2>
          <p>{current_newsletter.get('featured', '')}</p>
        </section>
        <section class="newsletter-section">
          <h2>Quick Tips</h2>
          <ul>
    """
    for tip in current_newsletter.get('quick_tips', []):
        newsletter_html += f"<li>{tip}</li>"
    newsletter_html += f"""
          </ul>
        </section>
        <section class="newsletter-section">
          <h2>Spotlight</h2>
          <p>{current_newsletter.get('spotlight', '')}</p>
        </section>
        <section class="newsletter-section">
          <h2>Looking Ahead</h2>
          <p>{current_newsletter.get('looking_ahead', '')}</p>
        </section>
        <button onclick="refreshNewsletter()">🔄 Refresh Newsletter</button>
      </main>
      <footer>
        Created by <strong>Tegh Bindra</strong> | © 2025
      </footer>
      <script>
        function refreshNewsletter() {{
          fetch('/refresh')
            .then(response => response.json())
            .then(data => {{
              location.reload();
            }})
            .catch(error => {{
              alert('Error refreshing newsletter.');
            }});
        }}
      </script>
    </body>
    </html>
    """
    return render_template_string(newsletter_html)

@app.route("/latest-newsletter")
def latest_newsletter():
    return jsonify(current_newsletter)

@app.route("/refresh")
def refresh_newsletter():
    update_newsletter()
    return jsonify({"message": "Newsletter refreshed.", "newsletter": current_newsletter})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)), debug=True)