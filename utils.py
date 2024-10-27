from openai import OpenAI
import sqlite3
from tenacity import retry, wait_random_exponential, stop_after_attempt
import os


def setup_database():
    con = sqlite3.connect('api_config.db')
    cur = con.cursor()

    # Create the api_keys table if it doesn't exist
    cur.execute("""
        CREATE TABLE IF NOT EXISTS api_keys (
            id INTEGER PRIMARY KEY,
            openai_api TEXT,
            pexels_api TEXT
        )
    """)

    con.commit()
    con.close()


def get_openai_api_keys():
    try:
        setup_database()

        con = sqlite3.connect('api_config.db')
        cur = con.cursor()
        cur.execute("SELECT openai_api, pexels_api FROM api_keys WHERE id = 1")
        api_keys = cur.fetchone()
        con.close()
        if api_keys:
            return {"openai_api": api_keys[0], "pexels_api": api_keys[1]}
    except sqlite3.OperationalError:
        return None

api_keys = get_openai_api_keys()

if api_keys:
    openai_api_key = api_keys["openai_api"]
    Pexels_API_KEY = api_keys["pexels_api"]
    # print("OpenAI API Key:", openai.api_key)
    # print("Pexels API Key:", Pexels_API_KEY)
else:
    openai_api_key = ""
    Pexels_API_KEY = ""
    print("API keys not found in the database.")

def retry_if_exception(exception):
    """Return True if we should retry (in this case when there's an Exception), False otherwise"""
    return isinstance(exception, Exception)

@retry(wait=wait_random_exponential(min=30, max=150), stop=stop_after_attempt(6))
def openAI_output(prompt):
    os.environ['OPENAI_API_KEY'] = openai_api_key
    # Create an instance of the OpenAI client
    client = OpenAI()
    
    # Format the messages for the chat completion
    messages = [{"role": "user", "content": prompt}]  # Add the prompt as a user message
    
    response = client.chat.completions.create(
        model="gpt-4o-mini",  # Keep the specified model name
        messages=messages,
        temperature=1,
        max_tokens=1500,
        top_p=1,
        frequency_penalty=0,
        presence_penalty=0
    )
    
    # Access the content correctly
    content = response.choices[0].message.content
    return content.strip()
