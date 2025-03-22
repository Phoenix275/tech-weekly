from flask import Flask, jsonify, render_template_string
import openai
import feedparser
import os
import markdown
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler

app = Flask(__name__)
application = app  # For Gunicorn

client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

RSS_FEED_URL = "https://rss.cnn.com/rss/edition_business.rss"
latest_blog_post = None

def fetch_latest_articles():
    feed = feedparser.parse(RSS_FEED_URL)
    return [f'"{entry.title}" - {entry.link}' for entry in feed.entries[:5]]

def generate_blog_post(articles):
    current_month = datetime.now().strftime("%B %Y")

    prompt = f"""
You are a professional newsletter editor writing for retired and semi-retired business leaders. Create a warm and professional newsletter for {current_month}, using the following articles for inspiration:

{articles}

Newsletter Structure (Use Markdown with H1 and H2 headers — no bullet points or lists):
# Business & Life Weekly — {current_month} Edition

1. ## Business
Cover market trends, financial insights, and investment stability.

2. ## Wellness
Offer health advice, lifestyle tips, and aging-related wellness.

3. ## Purpose & New Beginnings
Highlight how retirees can find purpose post-career.

4. ## Personal Stories
Include an inspiring transformation or reader story.

5. ## Resources
Offer helpful tools like Self-Directed IRAs, Medicare tips, or tech guides.

- Do NOT include "Warmly" or overly casual tone.
- DO write in a personal but professional, friendly newsletter tone.
"""

    try:
        response = client.chat.completions.create(
            model="gpt-4-turbo",
            messages=[
                {"role": "system", "content": "You are a professional newsletter editor."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=1500
        )
        content_md = response.choices[0].message.content.strip()
        content_html = markdown.markdown(content_md)
        return content_html

    except Exception as e:
        return f"<p><strong>⚠️ Error generating newsletter:</strong> {str(e)}</p>"

def update_blog_post():
    global latest_blog_post
    latest_blog_post = generate_blog_post(fetch_latest_articles())
    print("✅ Newsletter updated.")

update_blog_post()

scheduler = BackgroundScheduler()
scheduler.add_job(update_blog_post, 'cron', day_of_week='mon', hour=9, minute=0)
scheduler.start()

@app.route("/")
def home():
    global latest_blog_post
    return render_template_string(f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Business & Life Weekly</title>
        <style>
            body {{
                font-family: 'Georgia', serif;
                text-align: center;
                padding: 40px;
                background: linear-gradient(to right, #fceabb, #f8b500);
                color: #333;
            }}
            h1 {{
                font-size: 2.8em;
                color: #2c3e50;
            }}
            h2 {{
                color: #444;
                margin-top: 25px;
            }}
            #blog-content {{
                background: white;
                padding: 30px;
                border-radius: 10px;
                box-shadow: 0px 6px 15px rgba(0, 0, 0, 0.15);
                max-width: 800px;
                margin: 30px auto;
                text-align: left;
                font-size: 1.15em;
                line-height: 1.7;
            }}
            button {{
                background-color: #5a9;
                color: white;
                padding: 12px 24px;
                border: none;
                font-size: 16px;
                border-radius: 6px;
                cursor: pointer;
                margin-top: 10px;
            }}
            button:hover {{
                background-color: #4c8;
            }}
            #loading {{
                display: none;
                font-size: 16px;
                color: #444;
                margin-top: 10px;
            }}
            footer {{
                margin-top: 40px;
                font-size: 14px;
                color: #555;
            }}
        </style>
    </head>
    <body>
        <h1>Business & Life Weekly</h1>
        <p>Curated insights for a fulfilling and informed retirement journey.</p>
        <div id="blog-content">
            {latest_blog_post}
        </div>
        <button onclick="refreshNews()">🔄 Refresh Newsletter</button>
        <p id="loading">Updating newsletter... ⏳</p>
        <footer>
            <p>© 2025 Business & Life Weekly | Built by Tegh Bindra</p>
        </footer>
        <script>
            function refreshNews() {{
                document.getElementById("loading").style.display = "block";
                fetch('/refresh')
                    .then(response => response.json())
                    .then(data => {{
                        document.getElementById("blog-content").innerHTML = data.blog_post;
                        document.getElementById("loading").style.display = "none";
                    }})
                    .catch(error => {{
                        alert('Error refreshing content.');
                        document.getElementById("loading").style.display = "none";
                    }});
            }}
        </script>
    </body>
    </html>
    """, latest_blog_post=latest_blog_post)

@app.route("/latest-tech-news")
def latest_tech_news():
    global latest_blog_post
    if latest_blog_post is None:
        update_blog_post()
    return jsonify({"blog_post": latest_blog_post})

@app.route("/refresh")
def refresh_blog():
    update_blog_post()
    return jsonify({"message": "Newsletter refreshed.", "blog_post": latest_blog_post})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)), debug=True)