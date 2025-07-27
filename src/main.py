import time
from reddit_client import RedditClient

def search_posts(client, query, subreddits, limit=10, days_old=7):
    """
    Uses the Reddit client to search for posts and returns a list of submissions.
    """
    results = client.search_posts(query, subreddits, limit=limit, days_old=days_old)
    
    posts = []
    if results:
        for submission in results:
            posts.append(submission)
            if len(posts) >= limit:
                break
    return posts

def comment_on_posts(client, posts, comment_text, interval_seconds):
    """
    Comments on a list of posts with a given interval.
    """
    print("\n--- Starting to comment on posts ---")
    for i, post in enumerate(posts):
        if post.author == client.reddit.user.me():
            print(f"Skipping post by yourself: '{post.title}'")
            continue

        client.post_comment(post, comment_text)
        
        if i < len(posts) - 1:
            print(f"Waiting for {interval_seconds} seconds before the next comment...")
            time.sleep(interval_seconds)
    print("--- Finished commenting ---")

def main():
    """
    Main entry point for the Reddit scraper application.
    """
    # --- Define your search parameters here ---
    keywords = [
        "quitar", "quitar fondo", "editar", "ayuda photoshop", "arreglar"
    ]
    days_to_search = 1
    results_limit = 20
    subreddits_to_search = "photoshoprequest+picrequests"
    # ------------------------------------------

    # --- Define your comment and behavior here ---
    comment_text = "I have also encountered this problem and it has not been resolved yet"
    enable_commenting = False
    comment_interval_seconds = 20
    # ------------------------------------------

    client = RedditClient()
    query = ' OR '.join(keywords)

    # 1. Search for posts
    found_posts = search_posts(
        client, query, subreddits_to_search, limit=results_limit, days_old=days_to_search
    )

    # 2. Print found posts
    if not found_posts:
        print("No posts found matching your criteria.")
        return

    print("--- Found the following posts ---")
    for i, post in enumerate(found_posts, 1):
        print(f"\n--- Post #{i} ---")
        print(f"URL: https://www.reddit.com{post.permalink}")
        print(f"Title: {post.title}")
        if post.selftext:
            content_preview = post.selftext[:300].replace('\n', ' ') + ('...' if len(post.selftext) > 300 else '')
            print(f"Content: {content_preview}")
        print(f"Comment to post: '{comment_text}'")
        print("-" * 20)

    # 3. Comment on posts if enabled
    if enable_commenting:
        comment_on_posts(client, found_posts, comment_text, comment_interval_seconds)
    else:
        print("\nCommenting is disabled. Exiting.")

if __name__ == "__main__":
    main()
