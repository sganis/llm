import sys
import os
from dotenv import load_dotenv
from pathlib import Path
import subprocess
from openai import OpenAI

# Load the .env file from the parent directory
env_path = Path(__file__).resolve().parent.parent.parent / "src-tauri" / ".env.dev"
load_dotenv(dotenv_path=env_path)

api_key = os.getenv("OPENAI_API_KEY")
assert api_key, "API key not found. Make sure you have a .env file in the parent directory."

client = OpenAI()
model = "gpt-4o-mini"

# Run git diff and capture the output
result1 = subprocess.run(["git", "diff", "--cached"], capture_output=True, text=True)
result2 = subprocess.run(["git", "diff"], capture_output=True, text=True)

diff = result1.stdout.strip() + result2.stdout.strip()

if not diff:
    print("Nothing to commit.")
    sys.exit()

def generate_commit_message(model, diff):
    """Generate a concise commit message using OpenAI."""
    while True:
        completion = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {
                    "role": "user",
                    "content": f"""
                    Analyze the following git diff output and generate a concise, meaningful commit message. 
                    Focus on the purpose of the changes rather than listing modified files. 
                    Keep the response in a single line without markdown formatting.
                    Make several messages if needed for clarity but all of them in a single line.
                    If I ask this question again with the same diff, add more details.
                    Git diff output: {diff}
                    """
                }
            ]
        )

        commit_message = completion.choices[0].message.content.strip()
        print(f"\n\n{commit_message}\n")

        user_input = input(
            "\n" + "="*40 + 
            "\n  Is this message good?:\n" +
            "="*40 + 
            "\n  [  Enter  ] → Accept and commit" +
            "\n  [    g    ] → Generate a new message" +
            "\n  [ Any key ] → Cancel\n" +
            "="*40 + "\n> "
        ).strip().lower()

        if user_input == "":
            return commit_message  # Accept the message
        elif user_input == "g":
            print("Regenerating commit message...\n")
        else:
            print("Commit canceled.")
            sys.exit()

# Generate commit message
commit_message = generate_commit_message(model, diff)

# Commit and push immediately
print("Committing...")
commit_output = subprocess.run(
    ["git", "commit", "-am", f"{commit_message} [Generated by {model}]"], 
    capture_output=True, text=True
)
print(commit_output.stdout, commit_output.stderr)

push_output = subprocess.run(["git", "push"], capture_output=True, text=True)
print(push_output.stdout, push_output.stderr)
