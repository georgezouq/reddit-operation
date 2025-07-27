import configparser
import sys
import os
import praw
import prawcore

class RedditClient:
    """
    A client to interact with the Reddit API using PRAW.
    """

    def __init__(self, config_file='config.ini'):
        """
        Initializes the Reddit client by reading credentials from a config file.
        """
        try:
            config = configparser.ConfigParser()
            # Build the path to the config file, assuming it's in the project root
            project_root = os.path.dirname(os.path.dirname(__file__))
            config_path = os.path.join(project_root, config_file)

            if not os.path.exists(config_path):
                raise FileNotFoundError

            config.read(config_path)
            reddit_config = config['reddit']

            client_id = reddit_config['client_id']
            client_secret = reddit_config['client_secret']
            user_agent = reddit_config['user_agent']
            username = reddit_config['username']
            password = reddit_config['password']

            self.reddit = praw.Reddit(client_id=client_id,
                                      client_secret=client_secret,
                                      user_agent=user_agent,
                                      username=username,
                                      password=password)

            print(f"Connected to Reddit as: {self.reddit.user.me()} (Read-only: {self.reddit.read_only})")

        except FileNotFoundError:
            print(f"Error: '{config_file}' not found in the project root directory.", file=sys.stderr)
            sys.exit(1)
        except KeyError as e:
            print(f"Error: Missing key in '{config_file}': {e}", file=sys.stderr)
            sys.exit(1)
        except prawcore.exceptions.PrawcoreException as e:
            print(f"An API error occurred during authentication: {e}", file=sys.stderr)
            sys.exit(1)

    def search_posts(self, query, subreddits, limit=10, sort='new', days_old=7):
        """
        Searches for posts across a list of subreddits within a time frame.

        Args:
            query (str): The search query.
            subreddits (str): A '+' separated string of subreddit names.
            limit (int): The maximum number of results to return.
            sort (str): The sort order ('relevance', 'hot', 'top', 'new', 'comments').
            days_old (int): The number of days back to search.

        Returns:
            A generator of PRAW submission objects, or an empty list if an error occurs.
        """
        time_filters = {
            1: 'day',
            7: 'week',
            30: 'month',
            365: 'year',
        }
        # Find the most appropriate time_filter for the given number of days
        time_filter = 'all'
        for days, filter_name in sorted(time_filters.items()):
            if days_old <= days:
                time_filter = filter_name
                break

        try:
            subreddit_instance = self.reddit.subreddit(subreddits)
            print(f"\nSearching for posts about: '{query}' in r/{subreddits} (last {time_filter})")
            # We search for more than the limit to have a buffer
            return subreddit_instance.search(query, sort=sort, time_filter=time_filter, limit=limit * 2)
        except prawcore.exceptions.PrawcoreException as e:
            print(f"An API error occurred during search: {e}", file=sys.stderr)
            return []

    def post_comment(self, submission, comment_text):
        """
        Posts a comment to a given submission.

        Args:
            submission: The PRAW submission object to comment on.
            comment_text (str): The text of the comment to post.
        """
        try:
            submission.reply(comment_text)
            print(f"Successfully commented on post: '{submission.title}'")
        except praw.exceptions.APIException as e:
            print(f"Failed to comment on post '{submission.title}': {e}", file=sys.stderr)
        except prawcore.exceptions.PrawcoreException as e:
            print(f"An API error occurred while commenting: {e}", file=sys.stderr)
