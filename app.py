from flask import Flask, jsonify, render_template_string
import openai
import feedparser
import os
from apscheduler.schedulers.background import BackgroundScheduler

app = Flask(__name__)
application = app  # Expose the WSGI callable for deployment

# Initialize OpenAI client
client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

RSS_FEED_URL = "https://rss.cnn.com/rss/edition_business.rss"

# Global variable to store the latest newsletter
latest_newsletter = None

def fetch_latest_articles():
    """Fetches the latest 5 articles from the RSS feed."""
    feed = feedparser.parse(RSS_FEED_URL)
    articles = []
    for entry in feed.entries[:5]:
        articles.append(f'"{entry.title}" - {entry.link}')
    return articles

def generate_newsletter(articles):
    """Generates a well-structured newsletter using OpenAI's API."""
    prompt = f"""
    You are composing a professional newsletter tailored for retired or semi-retired business owners. The newsletter should be structured into the following sections:

    1. **Business**: Insights on market trends, small business developments, and financial stability.
    2. **Wellness**: Health tips, routines, longevity, and mental well-being.
    3. **Purpose & New Beginnings**: Finding meaning, redefining life post-career, embracing change.
    4. **Personal Stories**: Uplifting narratives or mini-profiles.
    5. **Resources**: Practical tools like Self-Directed IRAs, digital literacy, Medicare tips, etc.

    Ensure the tone is formal and informative, avoiding personal pronouns and contractions. The content should be engaging yet maintain a professional demeanor.

    Trending topics to incorporate:
    {articles}
    """
    try:
        response = client.chat.completions.create(
            model="gpt-4-turbo",
            messages=[
                {"role": "system", "content": "You are a professional newsletter editor."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=1000
        )
        content = response.choices[0].message.content.strip()

        # Remove unintended trailing characters
        content = content.rstrip("#")

        return content

    except Exception as e:
        return f"⚠️ Error generating newsletter: {str(e)}"

def update_newsletter():
    """Fetches articles and updates the global newsletter."""
    global latest_newsletter
    articles = fetch_latest_articles()
    latest_newsletter = generate_newsletter(articles)
    print("✅ Newsletter updated.")

# Generate the first newsletter at startup
update_newsletter()

# Set up APScheduler to run update_newsletter every Monday at 9 AM
scheduler = BackgroundScheduler()
scheduler.add_job(update_newsletter, 'cron', day_of_week='mon', hour=9, minute=0)
scheduler.start()

@app.route("/")
def home():
    """Home route that displays the latest newsletter with a refresh button."""
    global latest_newsletter

    return render_template_string(f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Weekly Insights</title>
            <style>
                body {{
                    font-family: 'Georgia', serif;
                    padding: 50px;
                    background: linear-gradient(to right, #fdf6e3, #f0f0f0);
                    color: #333;
                }}
                h1 {{
                    font-size: 2.8em;
                    color: #444;
                    text-align: center;
                }}
                h2 {{
                    color: #2a4d69;
                }}
                #newsletter {{
                    background: #fff;
                    padding: 30px;
                    border-radius: 10px;
                    max-width: 800px;
                    margin: 20px auto;
                    box-shadow: 0 0 15px rgba(0,0,0,0.1);
                }}
                button {{
                    display: block;
                    margin: 20px auto;
                    background-color: #f4a261;
                    color: #fff;
                    padding: 12px 24px;
                    border: none;
                    font-size: 16px;
                    border-radius: 5px;
                    cursor: pointer;
                }}
                button:hover {{
                    background-color: #e76f51;
                }}
                footer {{
                    text-align: center;
                    margin-top: 40px;
                    font-size: 14px;
                    color: #777;
                }}
            </style>
        </head>
        <body>
            <h1>Weekly Insights</h1>
            <div id="newsletter">
                {latest_newsletter}
            </div>
            <button onclick="refreshNews()">🔄 Refresh Newsletter</button>
            <p id="loading" style="text-align:center; display:none;">⏳ Updating...</p>
            <footer>
                Created by Tegh Bindra | © 2025
            </footer>
            <script>
                function refreshNews() {{
                    document.getElementById("loading").style.display = "block";
                    fetch('/refresh')
                        .then(response => response.json())
                        .then(data => {{
                            document.getElementById("newsletter").innerHTML = data.newsletter;
                            document.getElementById("loading").style.display = "none";
                        }})
                        .catch(error => {{
                            alert("Failed to update.");
                            document.getElementById("loading").style.display = "none";
                        }});
                }}
            </script>
        </body>
        </html>
    """)

@app.route("/refresh")
def refresh_newsletter():
    """Manually refreshes the newsletter."""
    update_newsletter()
    return jsonify({"message": "Newsletter refreshed manually.", "newsletter": latest_newsletter})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)), debug=True)