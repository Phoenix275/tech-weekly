from flask import Flask, jsonify, render_template_string
import openai
import feedparser
import os
from apscheduler.schedulers.background import BackgroundScheduler

app = Flask(__name__)
application = app  # Expose the WSGI callable for Gunicorn

# Initialize OpenAI client (New format)
client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

RSS_FEED_URL = "https://rss.cnn.com/rss/edition_technology.rss"

# Global variable to store the latest blog post
latest_blog_post = None

def fetch_latest_articles():
    """Fetches the latest 5 articles from the RSS feed."""
    feed = feedparser.parse(RSS_FEED_URL)
    articles = []
    for entry in feed.entries[:5]:
        articles.append(f"{entry.title}: {entry.link}")
    return articles

def generate_blog_post(articles):
    """Generates a blog post using OpenAI's API based on the latest articles."""
    prompt = f"Write a concise, engaging blog post summarizing the following articles: {articles}"
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are a tech blogger."},
            {"role": "user", "content": prompt}
        ],
        max_tokens=500
    )
    return response.choices[0].message.content.strip()

def update_blog_post():
    """Fetches articles and updates the global blog post."""
    global latest_blog_post
    articles = fetch_latest_articles()
    latest_blog_post = generate_blog_post(articles)
    print("✅ Blog post updated.")

# Set up APScheduler to run update_blog_post every Monday at 9 AM
scheduler = BackgroundScheduler()
scheduler.add_job(update_blog_post, 'cron', day_of_week='mon', hour=9, minute=0)
scheduler.start()

@app.route("/")
def home():
    """Home route that displays the latest news with a refresh button."""
    global latest_blog_post
    if latest_blog_post is None:
        update_blog_post()  # Ensures there's content on first load
    
    return render_template_string(f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Tech Weekly</title>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    text-align: center;
                    padding: 50px;
                    background-color: #f4f4f4;
                }}
                h1 {{
                    color: #333;
                    font-size: 2.5em;
                }}
                p {{
                    font-size: 1.2em;
                    color: #555;
                }}
                #blog-content {{
                    background: white;
                    padding: 20px;
                    border-radius: 8px;
                    box-shadow: 0px 0px 10px rgba(0, 0, 0, 0.1);
                    max-width: 800px;
                    margin: 20px auto;
                    text-align: left;
                }}
                button {{
                    background-color: #007BFF;
                    color: white;
                    padding: 12px 24px;
                    border: none;
                    cursor: pointer;
                    font-size: 16px;
                    border-radius: 5px;
                    transition: 0.3s;
                }}
                button:hover {{
                    background-color: #0056b3;
                }}
                #loading {{
                    display: none;
                    font-size: 16px;
                    color: #007BFF;
                }}
            </style>
        </head>
        <body>
            <h1>Tech Weekly</h1>
            <p>🚀 AI-powered tech news updates every Monday at 9 AM.</p>
            <div id="blog-content">
                <h2>Latest Tech News</h2>
                <p id="news-text">{latest_blog_post}</p>
            </div>
            <button onclick="refreshNews()">🔄 Refresh News</button>
            <p id="loading">Updating news... ⏳</p>
            <script>
                function refreshNews() {{
                    document.getElementById("loading").style.display = "block";
                    fetch('/refresh')
                        .then(response => response.json())
                        .then(data => {{
                            document.getElementById("news-text").innerText = data.blog_post;
                            document.getElementById("loading").style.display = "none";
                        }})
                        .catch(error => {{
                            alert('Error updating news.');
                            document.getElementById("loading").style.display = "none";
                        }});
                }}
            </script>
        </body>
        </html>
    """)

@app.route("/latest-tech-news")
def latest_tech_news():
    """Returns the latest blog post. If not available, update it first."""
    global latest_blog_post
    if latest_blog_post is None:
        update_blog_post()
    return jsonify({"blog_post": latest_blog_post})

@app.route("/refresh")
def refresh_blog():
    """Manually refreshes the blog post."""
    update_blog_post()
    return jsonify({"message": "Blog post refreshed manually.", "blog_post": latest_blog_post})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)), debug=True)