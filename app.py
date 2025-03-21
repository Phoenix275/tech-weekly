from flask import Flask, jsonify, render_template_string
import openai
import feedparser
import os
from apscheduler.schedulers.background import BackgroundScheduler

app = Flask(__name__)
application = app  # Expose the WSGI callable for Gunicorn

# Initialize OpenAI client
client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

RSS_FEED_URL = "https://rss.cnn.com/rss/edition_business.rss"

# Global variable to store the latest blog post
latest_blog_post = None

def fetch_latest_articles():
    """Fetches the latest 5 articles from the RSS feed."""
    feed = feedparser.parse(RSS_FEED_URL)
    articles = []
    for entry in feed.entries[:5]:
        articles.append(f'"{entry.title}" - {entry.link}')
    return articles

def generate_blog_post(articles):
    """Generates a well-structured blog post using OpenAI's API."""
    prompt = f"""
    You are a professional business journalist writing for The Wall Street Journal or Forbes.
    Write an engaging, easy-to-read business news article based on the following trending topics:

    {articles}

    **Format Guidelines:**
    - Use a clear and engaging <h1> title.
    - Use <h2> headings for major topics.
    - Use <p> paragraphs for clarity and visual spacing.
    - Avoid dense blocks of text.
    - Keep it relevant for Baby Boomer business owners.
    - Avoid mentioning AI in the article body.

    Example Structure:
    <h1>How Small Businesses Are Embracing Change</h1>
    <p>From inflation to innovation, businesses are adapting...</p>

    <h2>Healthcare & Insurance</h2>
    <p>What Baby Boomers need to know about current policies...</p>
    """

    try:
        response = client.chat.completions.create(
            model="gpt-4-turbo",
            messages=[
                {"role": "system", "content": "You are a professional business journalist."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=700
        )
        content = response.choices[0].message.content.strip()

        if "Sure" in content or "I'd be happy to help" in content:
            return "⚠️ Error: AI response was irrelevant. Please refresh again."
        
        return content

    except Exception as e:
        return f"⚠️ Error generating news: {str(e)}"

def update_blog_post():
    global latest_blog_post
    articles = fetch_latest_articles()
    latest_blog_post = generate_blog_post(articles)
    print("✅ Blog post updated.")

# Generate on startup
update_blog_post()

# Schedule weekly refresh
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
            <title>Business & Tech Weekly</title>
            <style>
                body {{
                    font-family: 'Arial', sans-serif;
                    text-align: center;
                    padding: 50px;
                    background: linear-gradient(to right, #f6d365, #fda085);
                    color: black;
                }}
                h1 {{
                    font-size: 2.8em;
                    margin-bottom: 10px;
                    color: black;
                }}
                h2, h3, p, strong {{
                    color: black !important;
                }}
                #blog-content {{
                    background: white;
                    padding: 20px;
                    border-radius: 8px;
                    box-shadow: 0px 4px 10px rgba(0, 0, 0, 0.2);
                    max-width: 800px;
                    margin: 20px auto;
                    text-align: left;
                    font-size: 1.1em;
                    line-height: 1.6;
                    color: black;
                }}
                button {{
                    background-color: #FFD700;
                    color: black;
                    padding: 12px 24px;
                    border: none;
                    cursor: pointer;
                    font-size: 16px;
                    font-weight: bold;
                    border-radius: 5px;
                    transition: 0.3s;
                    margin-top: 10px;
                }}
                button:hover {{
                    background-color: #FFC107;
                }}
                #loading {{
                    display: none;
                    font-size: 16px;
                    color: black;
                    margin-top: 10px;
                }}
                footer {{
                    margin-top: 40px;
                    font-size: 14px;
                    color: white;
                }}
            </style>
        </head>
        <body>
            <h1>Business & Tech Weekly</h1>
            <p style="color: black;">Stay informed on the latest trends in business and innovation.</p>
            <div id="blog-content">
                <h2>Latest Insights</h2>
                <div id="news-text">{latest_blog_post}</div>

                <h2>Healthcare Spotlight</h2>
                <p>As the Baby Boomer generation continues to age, healthcare remains a pivotal concern. From navigating Medicare to exploring long-term care options and retirement planning, it’s more important than ever to stay informed about healthcare developments and insurance updates tailored for seasoned entrepreneurs and retirees alike.</p>
            </div>

            <button onclick="refreshNews()">🔄 Refresh News</button>
            <p id="loading">Updating news... ⏳</p>

            <footer>
                <p>Created by <strong>Tegh Bindra</strong> | © 2025</p>
            </footer>

            <script>
                function refreshNews() {{
                    document.getElementById("loading").style.display = "block";
                    fetch('/refresh')
                        .then(response => response.json())
                        .then(data => {{
                            document.getElementById("news-text").innerHTML = data.blog_post;
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
    global latest_blog_post
    if latest_blog_post is None:
        update_blog_post()
    return jsonify({"blog_post": latest_blog_post})

@app.route("/refresh")
def refresh_blog():
    update_blog_post()
    return jsonify({"message": "Blog post refreshed manually.", "blog_post": latest_blog_post})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)), debug=True)