"""A minimal script that sends one prompt to an LLM and prints the reply.

This is a smoke test for the Avouch project: it confirms that the
environment, dependencies, and API credentials are all wired up correctly.
"""

import os

from dotenv import load_dotenv
from groq import Groq


def main() -> None:
    """Load credentials, call the LLM once, and print the response."""
    load_dotenv()

    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        raise RuntimeError(
            "GROQ_API_KEY not found. Check that your .env file exists "
            "and contains a line: GROQ_API_KEY=your_key"
        )

    client = Groq(api_key=api_key)

    prompt = "In one sentence, what is red-teaming in the context of AI safety?"

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3,
    )

    reply = response.choices[0].message.content
    print("PROMPT:", prompt)
    print("REPLY :", reply)


if __name__ == "__main__":
    main()
