import openai
import feedparser
import requests
import os

# Initialize OpenAI client
client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))  # Ensure your API key is set

# Define the RSS feed URL
RSS_FEED_URL = "https://rss.cnn.com/rss/edition_technology.rss"

def fetch_latest_articles():
    """Fetches the latest articles from the RSS feed."""
    feed = feedparser.parse(RSS_FEED_URL)
    articles = []

    for entry in feed.entries[:5]:  # Get the latest 5 articles
        articles.append(f"{entry.title}: {entry.link}")

    return articles

def generate_blog_post(articles):
    """Generates a blog post using OpenAI's API based on the latest articles."""
    prompt = f"""
    Write a concise, engaging blog post summarizing the latest tech news:
    {articles}
    """

    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are a tech blogger."},
            {"role": "user", "content": prompt}
        ],
        max_tokens=500
    )

    return response.choices[0].message.content.strip()

def main():
    print("🔄 Fetching latest articles...")
    latest_articles = fetch_latest_articles()

    print("📝 Generating blog post using AI...")
    blog_content = generate_blog_post(latest_articles)

    print("\n📰 **Tech Weekly Blog Post:**\n")
    print(blog_content)

    # Save to index.html
    html_content = f"""<!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Tech Weekly</title>
    </head>
    <body>
        <h1>Welcome to Tech Weekly</h1>
        <p>{blog_content}</p>
    </body>
    </html>"""

    with open("index.html", "w") as file:
        file.write(html_content)

    print("✅ Blog post saved successfully to index.html!")

    # Push the updated file to GitHub automatically
    os.system("git add index.html")
    os.system('git commit -m "Auto-update blog post"')
    os.system("git push origin main")

if __name__ == "__main__":
    main()