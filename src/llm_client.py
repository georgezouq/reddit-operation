import configparser
import os
import sys
from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate
from langchain.chains import LLMChain

class LLMClient:
    """
    A client to interact with a Language Model via an OpenAI-compatible API (like OpenRouter).
    """

    def __init__(self, config):
        """
        Initializes the LLM client using a pre-loaded config object.

        Args:
            config (ConfigParser): A pre-loaded ConfigParser object.
        """
        try:
            openrouter_config = config['openrouter']

            self.model = openrouter_config['model_name']
            self.llm = ChatOpenAI(
                model=self.model,
                openai_api_key=openrouter_config['api_key'],
                base_url=openrouter_config['base_url'],
                temperature=0.7,
            )

        except (FileNotFoundError, KeyError) as e:
            print(f"Error initializing LLMClient: {e}", file=sys.stderr)
            sys.exit(1)

    def analyze_post_relevance(self, post_title, post_content):
        """
        Analyzes if a post is relevant based on its title and content.
        Returns 'relevant' or 'irrelevant'.
        """
        prompt_template = PromptTemplate(
            input_variables=["title", "content"],
            template=(
                "Analyze the following Reddit post to determine if it's a user seeking help with photo editing. "
                "The user might want to remove objects/people, fix colors, improve quality, or similar tasks. "
                "Respond with only 'relevant' or 'irrelevant'.\n\n"
                "Title: {title}\n"
                "Content: {content}"
            )
        )
        chain = LLMChain(llm=self.llm, prompt=prompt_template)
        response = chain.run(title=post_title, content=post_content)
        return response.strip().lower()

    def generate_comment(self, post_title, post_content):
        """
        Generates a comment for a given post using a persona-based prompt.
        """
        if not self.llm:
            return "LLM not initialized."

        prompt_template = PromptTemplate(
            input_variables=["post_title", "post_content"],
            template=(
                "You are a helpful Reddit user who has had a great experience with a photo editing app called 'ClearCrowds'. "
                "Your task is to write a comment on a Reddit post asking for photo editing help. "
                "Your goal is to write a natural, helpful, and personal-sounding comment that shares your positive experience with the 'ClearCrowds' app, making it sound like a genuine user sharing a tip.\n\n"
                "**Post Information:**\n"
                "- **Title:** {post_title}\n"
                "- **Content:** {post_content}\n\n"
                "**Strict Rules for your comment:**\n"
                "1.  **Persona:** Write as if you are a regular person who has used the app. Use \"I\" and share a brief, relevant personal experience. For example, \"I had a photo just like this...\" or \"I remember trying to fix a similar issue...\".\n"
                "2.  **Natural Tone:** Avoid marketing language. Instead of \"It can do X and Y\", try \"I used it to do X and it worked surprisingly well for Y\".\n"
                "3.  **Mention the App:** Naturally and subtly mention the \"ClearCrowds\" app.\n"
                "4.  **Call to Action (Subtle):** You can mention it's on the App Store, but make it sound like a helpful tip, e.g., \"I think I got it from the App Store.\".\n"
                "5.  **Language:** The comment's language MUST match the language of the post title.\n"
                "6.  **Length:** Keep the comment concise, around 200-400 characters.\n"
                "7.  **Output Content:** Your output MUST ONLY be the final comment text. Do not add any extra explanations, notes, or introductory phrases.\n\n"
                "**Final Comment:**\n"
            )
        )
        chain = LLMChain(llm=self.llm, prompt=prompt_template)
        comment = chain.run(post_title=post_title, post_content=post_content)
        return comment.strip()
