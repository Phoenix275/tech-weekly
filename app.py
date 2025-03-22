from flask import Flask, jsonify, render_template_string
import openai
import feedparser
import os
import markdown
from apscheduler.schedulers.background import BackgroundScheduler

app = Flask(__name__)
application = app  # Expose the WSGI callable for Gunicorn

# Initialize OpenAI client
client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

RSS_FEED_URL = "https://rss.cnn.com/rss/edition_business.rss"

latest_blog_post = None

def fetch_latest_articles():
    feed = feedparser.parse(RSS_FEED_URL)
    return [f'"{entry.title}" - {entry.link}' for entry in feed.entries[:5]]

def generate_blog_post(articles):
    prompt = f"""
    You are a professional newsletter editor writing for an audience of retired and semi-retired business leaders.
    Write a warm but informative newsletter for the month based on the following articles:

    {articles}

    Sections:
    1. Business: Market Trends and Financial Stability
    2. Wellness: Fostering Health and Vitality
    3. Purpose & New Beginnings
    4. Personal Stories
    5. Resources (like Self-Directed IRAs, Medicare, Tech for Seniors, etc.)

    Format:
    - Use Markdown.
    - Each section should start with a markdown H2 (##), and title with H1 (#).
    - Paragraphs should be friendly but professional.
    - No boilerplate like "Warmly" or "Sure! I'd be happy to help."
    - Avoid excessive hashtags like ### in the middle.
    """

    try:
        response = client.chat.completions.create(
            model="gpt-4-turbo",
            messages=[
                {"role": "system", "content": "You are a professional newsletter writer."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=1200
        )
        markdown_text = response.choices[0].message.content.strip()
        return markdown.markdown(markdown_text)
    except Exception as e:
        return f"<p><strong>⚠️ Error generating newsletter:</strong> {str(e)}</p>"

def update_blog_post():
    global latest_blog_post
    articles = fetch_latest_articles()
    latest_blog_post = generate_blog_post(articles)
    print("✅ Newsletter content updated.")

update_blog_post()

scheduler = BackgroundScheduler()
scheduler.add_job(update_blog_post, 'cron', day_of_week='mon', hour=9, minute=0)
scheduler.start()

@app.route("/")
def home():
    return render_template_string("""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Business & Life Weekly</title>
            <style>
                body {
                    font-family: 'Georgia', serif;
                    text-align: center;
                    padding: 40px;
                    background: linear-gradient(to right, #fceabb, #f8b500);
                    color: #333;
                }
                h1 {
                    font-size: 2.8em;
                    color: #2c3e50;
                }
                h2 {
                    color: #444;
                    margin-top: 25px;
                }
                #blog-content {
                    background: white;
                    padding: 30px;
                    border-radius: 10px;
                    box-shadow: 0px 6px 15px rgba(0, 0, 0, 0.15);
                    max-width: 800px;
                    margin: 30px auto;
                    text-align: left;
                    font-size: 1.15em;
                    line-height: 1.7;
                }
                button {
                    background-color: #5a9;
                    color: white;
                    padding: 12px 24px;
                    border: none;
                    font-size: 16px;
                    border-radius: 6px;
                    cursor: pointer;
                    margin-top: 10px;
                }
                button:hover {
                    background-color: #4c8;
                }
                #loading {
                    display: none;
                    font-size: 16px;
                    color: #444;
                    margin-top: 10px;
                }
                footer {
                    margin-top: 40px;
                    font-size: 14px;
                    color: #555;
                }
            </style>
        </head>
        <body>
            <h1>Business & Life Weekly</h1>
            <p>Curated insights for a fulfilling and informed retirement journey.</p>
            <div id="blog-content">
                {{ latest_blog_post | safe }}
            </div>
            <button onclick="refreshNews()">🔄 Refresh Newsletter</button>
            <p id="loading">Updating newsletter... ⏳</p>

            <footer>
                <p>© 2025 Business & Life Weekly | Built by Tegh Bindra</p>
            </footer>

            <script>
                function refreshNews() {
                    document.getElementById("loading").style.display = "block";
                    fetch('/refresh')
                        .then(response => response.json())
                        .then(data => {
                            document.getElementById("blog-content").innerHTML = data.blog_post;
                            document.getElementById("loading").style.display = "none";
                        })
                        .catch(error => {
                            alert('Error refreshing content.');
                            document.getElementById("loading").style.display = "none";
                        });
                }
            </script>
        </body>
        </html>
    """, latest_blog_post=latest_blog_post)

@app.route("/refresh")
def refresh_blog():
    update_blog_post()
    return jsonify({"message": "Newsletter refreshed manually.", "blog_post": latest_blog_post})

@app.route("/latest-tech-news")
def latest_tech_news():
    if latest_blog_post is None:
        update_blog_post()
    return jsonify({"blog_post": latest_blog_post})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)), debug=True)