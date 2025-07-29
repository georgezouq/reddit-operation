import configparser
import sys
import praw
import prawcore
import logging

class RedditClient:
    """
    A client to interact with the Reddit API using PRAW, with multi-account support.
    """

    def __init__(self, config):
        """
        Initializes a pool of Reddit clients from the config.
        """
        self.account_configs = []
        self.clients = {}  # Store praw instances by index {0: client, 1: client}
        self.usernames = []
        self.current_account_index = 0
        self.read_only = True

        try:
            client_ids = [s.strip() for s in config.get('reddit', 'client_ids').split(',')]
            client_secrets = [s.strip() for s in config.get('reddit', 'client_secrets').split(',')]
            user_agents = [s.strip() for s in config.get('reddit', 'user_agents').split(',')]
            self.usernames = [s.strip() for s in config.get('reddit', 'usernames').split(',')]
            passwords = [s.strip() for s in config.get('reddit', 'passwords').split(',')]

            if not (len(client_ids) == len(client_secrets) == len(user_agents) == len(self.usernames) == len(passwords)):
                raise ValueError("Reddit credential lists in config.ini are not of the same length.")

            for i in range(len(client_ids)):
                self.account_configs.append({
                    'client_id': client_ids[i],
                    'client_secret': client_secrets[i],
                    'user_agent': user_agents[i],
                    'username': self.usernames[i],
                    'password': passwords[i],
                })

            if self.account_configs:
                self.username = self.usernames[0]
                self.read_only = not config.getboolean('reddit', 'enable_commenting', fallback=False)
                # Eagerly initialize the primary client for searching
                self._get_or_create_client(0)
                logging.info(f"Loaded {len(self.account_configs)} Reddit account configurations. Primary user: {self.username}. Read-only: {self.read_only}")
            else:
                logging.error("No Reddit accounts were configured.")

        except (configparser.NoOptionError, ValueError) as e:
            logging.critical(f"Error reading Reddit configuration: {e}")

    def _get_or_create_client(self, index):
        """
        Retrieves a PRAW client from the cache or creates it on demand.
        """
        if index in self.clients:
            return self.clients[index]

        if not (0 <= index < len(self.account_configs)):
            logging.error(f"Account index {index} is out of bounds.")
            return None

        config = self.account_configs[index]
        username = config['username']
        logging.info(f"Initializing PRAW client for user: {username}...")

        try:
            client = praw.Reddit(
                client_id=config['client_id'],
                client_secret=config['client_secret'],
                user_agent=config['user_agent'],
                username=username,
                password=config['password'],
                check_for_async=False
            )
            if client.user.me() is not None:
                logging.info(f"Successfully initialized and authenticated client for {username}.")
                self.clients[index] = client
                return client
            else:
                logging.error(f"Failed to verify authentication for user: {username}")
                return None
        except prawcore.exceptions.PrawcoreException as e:
            logging.error(f"Failed to initialize PRAW client for {username}: {e}")
            return None

    def search_posts(self, query, subreddits, time_filter='day', limit=100):
        """
        Searches for posts in specified subreddits using the primary client.
        """
        primary_client = self._get_or_create_client(0)
        if not primary_client:
            logging.error("Primary Reddit client failed to initialize. Cannot search posts.")
            return []
        logging.info(f"Searching for posts about: '{query}' in r/{subreddits} (last {time_filter})")
        subreddit = primary_client.subreddit(subreddits)
        try:
            return subreddit.search(query, time_filter=time_filter, limit=limit)
        except prawcore.exceptions.PrawcoreException as e:
            logging.error(f"An API error occurred during search: {e}")
            return []

    def post_comment(self, post, comment_text):
        """
        Posts a comment using the account currently pointed to by the round-robin index.
        """
        if self.read_only:
            # This check is technically redundant if enable_commenting is checked first,
            # but it's good for safety.
            raise Exception("COMMENTING_DISABLED")

        client = self._get_or_create_client(self.current_account_index)
        if not client:
            raise Exception(f"Failed to initialize Reddit client for user: {self.usernames[self.current_account_index]}")

        username = self.usernames[self.current_account_index]

        try:
            logging.info(f"Attempting to comment as user: {username}...")
            comment = post.reply(comment_text)
            logging.info(f"Successfully commented on post '{post.title}' as {username}. Comment ID: {comment.id}")
            return username
        except Exception as e:
            logging.error(f"Failed to comment as {username}. Error: {e}")
            raise e

    def rotate_account(self):
        """
        Advances the index to the next account for the next operation.
        """
        if not self.account_configs:
            return
        self.current_account_index = (self.current_account_index + 1) % len(self.account_configs)
        logging.info(f"Rotated to next account configuration: {self.usernames[self.current_account_index]}")
