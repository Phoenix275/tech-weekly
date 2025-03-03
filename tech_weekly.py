import openai
import feedparser
import requests

# Initialize OpenAI client
client = openai.OpenAI()

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
        messages=[{"role": "system", "content": "You are a tech blogger."},
                  {"role": "user", "content": prompt}],
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

if __name__ == "__main__":
    main()