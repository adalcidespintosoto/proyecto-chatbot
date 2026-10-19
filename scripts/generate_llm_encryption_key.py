"""Print a random master key for encrypting custom LLM provider credentials."""

import secrets


if __name__ == "__main__":
    print(secrets.token_urlsafe(48))
