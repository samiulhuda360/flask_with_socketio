# utils.py
import openai
from retrying import retry
from config import OPENAI_API_KEY

openai.api_key = OPENAI_API_KEY

def retry_if_exception(exception):
    """Return True if we should retry (in this case when there's an Exception), False otherwise"""
    return isinstance(exception, Exception)

@retry(retry_on_exception=retry_if_exception, stop_max_attempt_number=5)
def openAI_output(self):
    # pass
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "user",
                 "content": self },
            ]
        )
        output = response.choices[0]["message"]["content"].strip()
        return output
    except Exception as e:
        print("An error occurred. Retrying...")
        raise e