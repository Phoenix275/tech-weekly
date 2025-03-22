from flask import Flask, jsonify, render_template_string
import openai
import feedparser
import os
from apscheduler.schedulers.background import BackgroundScheduler

app = Flask(__name__)
application = app

client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

RSS_FEED_URL = "https://rss.cnn.com/rss/edition_business.rss"
latest_blog_post = None

def fetch_latest_articles():
    feed = feedparser.parse(RSS_FEED_URL)
    articles = []
    for entry in feed.entries[:5]:
        articles.append(f'"{entry.title}" - {entry.link}')
    return articles

def generate_blog_post(articles):
    prompt = f"""
    You are writing a warm, personal weekly newsletter for retired or semi-retired business owners.
    This newsletter is heartfelt, relatable, and focused on real-life stories and guidance.

    Please organize the blog into the following 5 sections using <h2> headers:
    1. Business
    2. Wellness
    3. Purpose + New Beginning
    4. Personal Stories
    5. Resources (Include something on Self-Directed IRAs)

    Avoid technical jargon. Make it conversational, simple, and engaging like a letter to a friend.
    Write like it’s coming from someone who genuinely cares about their reader’s next chapter.

    Trending topics:
    {articles}
    """
    try:
        response = client.chat.completions.create(
            model="gpt-4-turbo",
            messages=[
                {"role": "system", "content": "You write warm, engaging newsletters."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=1000
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"⚠️ Error generating newsletter: {str(e)}"

def update_blog_post():
    global latest_blog_post
    articles = fetch_latest_articles()
    latest_blog_post = generate_blog_post(articles)
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
            <title>Weekly Wisdom</title>
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
            <h1>Weekly Wisdom</h1>
            <div id="newsletter">
                {latest_blog_post}
            </div>
            <button onclick="refreshNews()">🔄 Refresh Newsletter</button>
            <p id="loading" style="text-align:center;">⏳ Updating...</p>
            <footer>
                Created with ❤️ by Tegh Bindra | © 2025
            </footer>
            <script>
                function refreshNews() {{
                    document.getElementById("loading").style.display = "block";
                    fetch('/refresh')
                        .then(response => response.json())
                        .then(data => {{
                            document.getElementById("newsletter").innerHTML = data.blog_post;
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

@app.route("/latest-tech-news")
def latest_tech_news():
    global latest_blog_post
    if latest_blog_post is None:
        update_blog_post()
    return jsonify({"blog_post": latest_blog_post})

@app.route("/refresh")
def refresh_blog():
    update_blog_post()
    return jsonify({"message": "Newsletter refreshed manually.", "blog_post": latest_blog_post})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)), debug=True)