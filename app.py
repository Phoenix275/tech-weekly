from flask import Flask, jsonify, render_template_string
import openai
import feedparser
import os
from apscheduler.schedulers.background import BackgroundScheduler

app = Flask(__name__)
application = app  # Expose the WSGI callable for Gunicorn

# Initialize OpenAI client
client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

RSS_FEED_URL = "https://rss.cnn.com/rss/edition_technology.rss"

# Global variable to store the latest blog post
latest_blog_post = "Loading latest business insights..."

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
    You are a professional business journalist writing for Forbes or The Wall Street Journal.
    Your audience consists of business owners aged 50+.
    
    Based on these trending articles, write a **detailed and engaging** business insight post:
    
    {articles}

    **Format Guidelines:**
    - **Use HTML structure** for proper formatting.
    - **Use <h2> for headings**.
    - **Use <p> for paragraphs** (no single giant block of text).
    - **Make the article informative, engaging, and easy to read.**
    - **Avoid generic AI phrases** like "Sure! I'd be happy to help."

    Example:
    ```
    <h1>How 5G is Changing Business Communication</h1>
    <p>Businesses are adopting 5G networks at a rapid pace...</p>

    <h2>Faster Networks, Faster Growth</h2>
    <p>New technology allows companies to expand digitally...</p>
    ```
    """
    
    try:
        response = client.chat.completions.create(
            model="gpt-4-turbo",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=700
        )
        content = response.choices[0].message.content.strip()

        # Ensure OpenAI does not return irrelevant responses
        if not content or "Sure" in content or "I'd be happy to help" in content:
            return "<p>Error: AI did not generate useful content. Try refreshing.</p>"
        
        return content

    except Exception as e:
        return f"<p>Error generating news: {str(e)}</p>"

def update_blog_post():
    """Fetches articles and updates the global blog post."""
    global latest_blog_post
    articles = fetch_latest_articles()
    latest_blog_post = generate_blog_post(articles)
    print("✅ Blog post updated.")

# Generate the first blog post at startup
update_blog_post()

# Set up APScheduler to update blog post every Monday at 9 AM
scheduler = BackgroundScheduler()
scheduler.add_job(update_blog_post, 'cron', day_of_week='mon', hour=9, minute=0)
scheduler.start()

@app.route("/")
def home():
    """Home route that displays the latest news with a refresh button."""
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
                    background: linear-gradient(to right, #ff9966, #ff5e62);
                    color: white;
                }}
                h1 {{
                    font-size: 2.5em;
                    margin-bottom: 10px;
                }}
                p, h2 {{
                    color: black; /* Ensure text is visible */
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
                }}
                h2 {{
                    color: #007BFF;
                    margin-top: 15px;
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
                    margin-top: 10px;
                }}
                button:hover {{
                    background-color: #0056b3;
                }}
                #loading {{
                    display: none;
                    font-size: 16px;
                    color: #007BFF;
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
            <p>📈 Stay informed on the latest business trends and technology innovations.</p>
            <div id="blog-content">
                <h2>Latest Insights</h2>
                <div id="news-text">{latest_blog_post}</div>
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