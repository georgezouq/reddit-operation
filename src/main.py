import time
import configparser
import logging
from datetime import datetime
from reddit_client import RedditClient
from llm_client import LLMClient
from database_client import DatabaseClient

# --- Logging Setup ---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

def load_config():
    config = configparser.ConfigParser()
    config.read('config.ini')
    return config

def process_post(post, reddit_client, llm_client, db_client, config) -> bool:
    # Filter out posts with 'Solved' flair
    if hasattr(post, 'link_flair_text') and post.link_flair_text and 'solved' in post.link_flair_text.lower():
        logging.info(f"Post {post.id} is marked as 'Solved'. Skipping.")
        return False

    # First, check the post's status in our database
    status, failure_count = db_client.get_post_status(post.id)

    if status == 'COMMENT_POSTED':
        logging.info(f"Post {post.id} has already been successfully commented on. Skipping.")
        return False

    if failure_count >= 3:
        logging.warning(f"Post {post.id} has failed {failure_count} times and will be skipped permanently.")
        return False

    # Prepare the data payload for logging
    comment_successful = False
    post_data = {
        'post_id': post.id,
        'subreddit': post.subreddit.display_name,
        'post_title': post.title,
        'post_content': post.selftext,
        'post_url': f"https://www.reddit.com{post.permalink}",
        'post_author': post.author.name if post.author else 'N/A',
        'post_created_utc': datetime.utcfromtimestamp(post.created_utc),
        'post_flair': getattr(post, 'link_flair_text', None),
        'status': 'PROCESSING',
        'bot_username': reddit_client.username,
        'commenting_account': None,
        'comment_failure_count': failure_count,
        'is_relevant': None,
        'llm_analysis_raw': None,
        'generated_comment': None,
        'error_message': None
    }

    try:
        if post.author and post.author.name in reddit_client.usernames:
            logging.info("Skipping own post.")
            db_client.log_interaction({ # Log minimal info for skipped own post
                'post_id': post.id,
                'status': 'SKIPPED_OWN_POST',
                'bot_username': reddit_client.username
            })
            return False

        analysis_result = llm_client.analyze_post_relevance(post.title, post.selftext)
        is_relevant = 'relevant' in analysis_result.lower()
        post_data.update({'is_relevant': is_relevant, 'llm_analysis_raw': analysis_result})

        if not is_relevant:
            logging.info("Post deemed not relevant.")
            post_data['status'] = 'SKIPPED_IRRELEVANT'
            db_client.log_interaction(post_data)
            return False

        comment_text = llm_client.generate_comment(post.title, post.selftext)
        post_data['generated_comment'] = comment_text
        logging.info(f'Generated Comment: "{comment_text}"')

        if config.getboolean('reddit', 'enable_commenting'):
            try:
                successful_username = reddit_client.post_comment(post, comment_text)
                post_data['commenting_account'] = successful_username
                post_data['status'] = 'COMMENT_POSTED'
                comment_successful = True
            except Exception as e:
                error_message = str(e)
                logging.error(f"Failed to comment on post '{post.title}'. Error: {error_message}")
                post_data['status'] = 'COMMENT_FAILED'
                post_data['error_message'] = error_message
                post_data['comment_failure_count'] += 1
        else:
            logging.info("(Commenting disabled, comment not posted)")
            post_data['status'] = 'COMMENT_DISABLED'

    except Exception as e:
        error_msg = f"An unexpected error occurred while processing post {post.id}: {e}"
        logging.error(error_msg)
        post_data['status'] = 'ERROR'
        post_data['error_message'] = str(e)
        post_data['comment_failure_count'] += 1 # Also count this as a failure
    finally:
        # Log the interaction unless it was already logged (e.g., for irrelevance)
        if post_data.get('status') != 'SKIPPED_IRRELEVANT':
            db_client.log_interaction(post_data)

    return comment_successful

def main():
    """
    Main function to run the Reddit bot.
    Initializes clients, searches for posts, and processes them.
    """
    db_client = None
    try:
        logging.info("Initializing clients...")
        config = load_config()
        reddit_client = RedditClient(config)
        llm_client = LLMClient(config)
        db_client = DatabaseClient(config)
        logging.info(f"Connected to Reddit as: {reddit_client.username} (Read-only: {reddit_client.read_only})")
        logging.info(f"Connected to OpenRouter with model: {llm_client.model}")
        logging.info("Successfully connected to the database.")

        query = config.get('reddit', 'search_query')
        subreddits = config.get('reddit', 'subreddits')
        time_filter = config.get('reddit', 'time_filter')
        limit = config.getint('reddit', 'limit')
        comment_interval = config.getint('reddit', 'comment_interval', fallback=60)

        logging.info(f"\nSearching for posts about: '{query}' in r/{subreddits} (last {time_filter})")
        posts = list(reddit_client.search_posts(query, subreddits, time_filter, limit))
        logging.info(f"--- Found {len(posts)} posts. Starting analysis and commenting workflow. ---")

        for i, post in enumerate(posts):
            logging.info(f"\n--- Processing Post ###########{i+1}: '{post.title}' ---")
            logging.info(f"URL: https://www.reddit.com{post.permalink}")
            comment_successful = process_post(post, reddit_client, llm_client, db_client, config)

            # Rotate to the next account for the next post, regardless of the outcome.
            reddit_client.rotate_account()

            # Wait before processing the next post only if a comment was successfully posted.
            if comment_successful and i < len(posts) - 1:
                logging.info(f"\n--- Comment successful. Waiting for {comment_interval} seconds before next post... ---")
                time.sleep(comment_interval)
            elif i < len(posts) - 1:
                logging.info("\n--- No comment posted or an error occurred. Proceeding to next post immediately. ---")

        logging.info("\n--- Workflow finished. ---")

    except Exception as e:
        logging.critical(f"A critical error occurred in the main workflow: {e}")
    finally:
        if db_client:
            db_client.close_connection()

if __name__ == "__main__":
    main()
