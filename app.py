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
latest_blog_post = None

def fetch_latest_articles():
    """Fetches the latest 5 articles from the RSS feed."""
    feed = feedparser.parse(RSS_FEED_URL)
    articles = []
    for entry in feed.entries[:5]:
        articles.append(f'"{entry.title}" - {entry.link}')
    return articles

def generate_blog_post(articles):
    """Generates a well-structured blog post designed for business-minded readers."""
    prompt = f"""
    You are a professional business journalist writing for publications like Forbes, The Wall Street Journal, and Business Insider.
    Write an engaging, insightful blog post covering the following business and technology news:

    {articles}

    **Guidelines:**
    - Keep the tone professional, informative, and engaging.
    - Use clear, structured headings (`<h2>` format) to separate key topics.
    - Avoid jargon; make content easy to digest for business owners.
    - Focus on how these trends affect businesses and leadership.
    - Write in a way that resonates with experienced professionals.

    Example Structure:
    ```
    <h1>How Emerging Technologies Are Reshaping Business</h1>

    <h2>New Innovations in Digital Marketing</h2>
    <p>Companies are leveraging cutting-edge technology to improve customer engagement...</p>

    <h2>The Future of Cybersecurity for Small Businesses</h2>
    <p>With increasing digital threats, business owners must invest in...</p>

    <h2>What This Means for Business Leaders</h2>
    <p>Executives should start preparing for these changes by...</p>
    ```
    """
    
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a business journalist."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=700
        )
        content = response.choices[0].message.content.strip()

        # Ensure OpenAI does not return irrelevant generic responses
        if "Sure" in content or "I'd be happy to help" in content:
            return "⚠️ Error: AI response was irrelevant. Please refresh again."
        
        return content

    except Exception as e:
        return f"⚠️ Error generating news: {str(e)}"

def update_blog_post():
    """Fetches articles and updates the global blog post."""
    global latest_blog_post
    articles = fetch_latest_articles()
    latest_blog_post = generate_blog_post(articles)
    print("✅ Blog post updated.")

# Generate the first blog post at startup
update_blog_post()

# Set up APScheduler to run update_blog_post every Monday at 9 AM
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
                    font-family: 'Georgia', serif;
                    text-align: center;
                    padding: 50px;
                    background: url('https://source.unsplash.com/1600x900/?business,office') no-repeat center center fixed;
                    background-size: cover;
                    color: #333;
                }}
                h1 {{
                    font-size: 2.8em;
                    font-weight: bold;
                    margin-bottom: 15px;
                }}
                p {{
                    font-size: 1.2em;
                }}
                #blog-content {{
                    background: rgba(255, 255, 255, 0.9);
                    padding: 25px;
                    border-radius: 10px;
                    box-shadow: 0px 5px 15px rgba(0, 0, 0, 0.2);
                    max-width: 900px;
                    margin: 20px auto;
                    text-align: left;
                    font-size: 1.1em;
                    line-height: 1.6;
                }}
                h2 {{
                    color: #0056b3;
                    margin-top: 20px;
                    font-size: 1.8em;
                }}
                ul {{
                    padding-left: 20px;
                    line-height: 1.6;
                }}
                button {{
                    background-color: #28a745;
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
                    background-color: #218838;
                }}
                #loading {{
                    display: none;
                    font-size: 16px;
                    color: #28a745;
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
            <h1>Business & Tech Weekly</h1>
            <p>Stay informed on the latest business trends and technology innovations.</p>
            <div id="blog-content">
                <h2>Latest Insights</h2>
                <div id="news-text">{latest_blog_post}</div>
            </div>
            <button onclick="refreshNews()">🔄 Refresh News</button>
            <p id="loading">Updating news... ⏳</p>

            <footer>
                <p>© 2025 Business & Tech Weekly | Created by <strong>Tegh Bindra</strong></p>
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
    return jsonify({"message": "Blog post refreshed.", "blog_post": latest_blog_post})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)), debug=True)