import psycopg2
import logging
import configparser
import os
from datetime import datetime

class DatabaseClient:
    """
    A client to interact with the PostgreSQL database.
    """

    def __init__(self, config):
        """
        Initializes the database client using a pre-loaded config object.

        Args:
            config (ConfigParser): A pre-loaded ConfigParser object.
        """
        self.conn = None
        try:
            # It's better to have a separate section for the database
            db_url = config['postgresql']['db_url']
            
            self.conn = psycopg2.connect(db_url)
            logging.info("Successfully connected to the database.")
            self.create_table_if_not_exists()

        except (Exception, psycopg2.Error) as error:
            logging.error(f"Error while connecting to PostgreSQL: {error}")
            self.conn = None # Ensure conn is None on failure

    def create_table_if_not_exists(self):
        """
        Creates the 'reddit_interactions' table if it doesn't already exist.
        """
        if not self.conn:
            return
            
        create_table_query = """
        CREATE TABLE IF NOT EXISTS reddit_interactions (
            id SERIAL PRIMARY KEY,
            post_id VARCHAR(20) UNIQUE NOT NULL,
            subreddit VARCHAR(100) NOT NULL,
            post_title TEXT,
            post_content TEXT,
            post_url VARCHAR(512) NOT NULL,
            post_author VARCHAR(100),
            post_created_utc TIMESTAMP WITH TIME ZONE,
            post_flair VARCHAR(100),
            commenting_account VARCHAR(255),
            comment_failure_count INT NOT NULL DEFAULT 0,
            processed_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            is_relevant BOOLEAN,
            llm_analysis_raw TEXT,
            generated_comment TEXT,
            status VARCHAR(50) NOT NULL,
            error_message TEXT
        );
        """
        try:
            with self.conn.cursor() as cur:
                cur.execute(create_table_query)
                self.conn.commit()
        except (Exception, psycopg2.Error) as error:
            logging.error(f"Error while creating table: {error}")

    def log_interaction(self, post_data):
        """
        Logs a post interaction to the database.
        Handles potential unique constraint violations gracefully by doing nothing.
        `post_data` is a dictionary containing all the necessary fields.
        """
        if not self.conn:
            logging.error("Cannot log interaction, no database connection.")
            return

        insert_query = """
        INSERT INTO reddit_interactions (
            post_id, subreddit, post_title, post_content, post_url, post_author, 
            post_created_utc, post_flair, commenting_account, is_relevant, llm_analysis_raw, 
            generated_comment, status, error_message, comment_failure_count
        ) VALUES (
            %(post_id)s, %(subreddit)s, %(post_title)s, %(post_content)s, %(post_url)s, %(post_author)s,
            %(post_created_utc)s, %(post_flair)s, %(commenting_account)s, %(is_relevant)s, %(llm_analysis_raw)s, 
            %(generated_comment)s, %(status)s, %(error_message)s, %(comment_failure_count)s
        )
        ON CONFLICT (post_id) DO UPDATE SET
            subreddit = EXCLUDED.subreddit,
            post_title = EXCLUDED.post_title,
            post_content = EXCLUDED.post_content,
            post_url = EXCLUDED.post_url,
            post_author = EXCLUDED.post_author,
            post_created_utc = EXCLUDED.post_created_utc,
            post_flair = EXCLUDED.post_flair,
            processed_at = CURRENT_TIMESTAMP,
            commenting_account = EXCLUDED.commenting_account,
            comment_failure_count = EXCLUDED.comment_failure_count,
            is_relevant = EXCLUDED.is_relevant,
            llm_analysis_raw = EXCLUDED.llm_analysis_raw,
            generated_comment = EXCLUDED.generated_comment,
            status = EXCLUDED.status,
            error_message = EXCLUDED.error_message;
        """
        
        try:
            with self.conn.cursor() as cur:
                cur.execute(insert_query, post_data)
                self.conn.commit()
        except (Exception, psycopg2.Error) as error:
            logging.error(f"Error logging interaction for post {post_data.get('post_id')}: {error}")
            if self.conn:
                self.conn.rollback()

    def fetch_all_interactions(self):
        """
        Fetches all records from the 'reddit_interactions' table.
        Returns a list of dictionaries, where each dictionary represents a row.
        """
        if not self.conn:
            logging.error("Cannot fetch, no database connection.")
            return []

        select_query = "SELECT * FROM reddit_interactions ORDER BY processed_at DESC;"
        
        try:
            with self.conn.cursor() as cur:
                cur.execute(select_query)
                # Get column names from the cursor description
                colnames = [desc[0] for desc in cur.description]
                records = cur.fetchall()
                # Convert list of tuples to list of dictionaries
                return [dict(zip(colnames, record)) for record in records]
        except (Exception, psycopg2.Error) as error:
            logging.error(f"Error fetching records: {error}")
            return []

    def close_connection(self):
        """
        Closes the database connection if it's open.
        """
        if self.conn:
            self.conn.close()
            logging.info("Database connection closed.")

    def get_post_status(self, post_id):
        """
        Retrieves the status and comment failure count for a specific post.
        Returns a tuple (status, failure_count).
        If the post is not found, returns (None, 0).
        """
        if not self.conn:
            logging.error("Cannot get post status, no database connection.")
            return (None, 0)

        query = "SELECT status, comment_failure_count FROM reddit_interactions WHERE post_id = %s;"
        try:
            with self.conn.cursor() as cur:
                cur.execute(query, (post_id,))
                result = cur.fetchone()
                if result:
                    return result[0], result[1]  # status, failure_count
                else:
                    return None, 0
        except (Exception, psycopg2.Error) as error:
            print(f"Error fetching status for post {post_id}: {error}")
            return (None, 0)  # Fail-safe
