#!/usr/bin/env python3
"""
FlaskMag Password Hash Generator
Generates SHA-256 hashes for use in auth_config.yaml
"""

import hashlib
import sys


def hash_password(password):
    """Generate SHA-256 hash of password"""
    return hashlib.sha256(password.encode()).hexdigest()


def main():
    print("=" * 60)
    print("FlaskMag Password Hash Generator")
    print("=" * 60)
    print()

    if len(sys.argv) > 1:
        # Password provided as command line argument
        password = sys.argv[1]
    else:
        # Interactive mode
        password = input("Enter password to hash: ")

    if not password:
        print("Error: Password cannot be empty")
        sys.exit(1)

    hashed = hash_password(password)

    print()
    print("-" * 60)
    print("Hashed Password:")
    print("-" * 60)
    print(hashed)
    print("-" * 60)
    print()
    print("Add this to ~/.flaskmag_cache/auth_config.yaml:")
    print()
    print("  usernames:")
    print("    your_username:")
    print("      name: Your Display Name")
    print(f"      password: {hashed}")
    print()


if __name__ == "__main__":
    main()
