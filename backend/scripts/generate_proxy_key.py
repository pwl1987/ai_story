#!/usr/bin/env python
"""
Proxy Encryption Key Generator

This script generates a Fernet encryption key for proxy password encryption.
The key is used to encrypt proxy passwords in the database.

⚠️  SECURITY WARNINGS:
=====================
- This key encrypts ALL proxy passwords in the database
- If you LOSE this key, ALL encrypted passwords are UNRECOVERABLE
- NEVER commit this key to Git or version control
- Store this key securely in environment variables (PROXY_ENCRYPTION_KEY)
- For production, use password managers (Kubernetes Secrets, AWS Secrets Manager, etc.)

Usage:
    python scripts/generate_proxy_key.py
    python scripts/generate_proxy_key.py --output .env

Environment Variable Configuration:
    Add the generated key to your .env file:
    PROXY_ENCRYPTION_KEY=<your-44-character-key-here>

@author: Epic 9 Team
@created: 2026-01-30
"""

import argparse
import os
import sys

from cryptography.fernet import Fernet


def generate_proxy_key():
    """
    Generate a Fernet encryption key for proxy password encryption.

    Returns:
        str: 44-character URL-safe base64-encoded key
    """
    key = Fernet.generate_key()
    return key.decode("utf-8") if isinstance(key, bytes) else key


def main():
    """Main entry point for key generation."""
    parser = argparse.ArgumentParser(
        description="Generate Fernet encryption key for proxy password encryption"
    )
    parser.add_argument(
        "--output", type=str, help="Optional: Output file path (e.g., .env.example)"
    )

    args = parser.parse_args()

    # Generate key
    key = generate_proxy_key()

    # Output to console
    print("=" * 70)
    print("🔐 Proxy Encryption Key Generated")
    print("=" * 70)
    print(f"\nKey (44 characters):\n{key}")
    print("\n⚠️  SECURITY INSTRUCTIONS:")
    print("-" * 70)
    print("1. Copy this key to your .env file:")
    print(f"   PROXY_ENCRYPTION_KEY={key}")
    print("\n2. NEVER commit this key to Git!")
    print("3. If you lose this key, all encrypted passwords are unrecoverable.")
    print("4. For production, use secure secret management systems.")
    print("-" * 70)

    # Optional: Write to file (e.g., .env.example)
    if args.output:
        file_path = args.output
        # Check if file exists
        if os.path.exists(file_path):
            print(f"\n⚠️  Warning: File '{file_path}' already exists.")
            try:
                confirm = input("Do you want to append to it? (y/N): ").strip().lower()
            except (EOFError, OSError):
                # Non-interactive environment (e.g., CI/CD), default to 'n'
                print("Non-interactive environment detected. Aborting.")
                return
            if confirm != "y":
                print("Aborted.")
                return

        try:
            with open(file_path, "a") as f:
                f.write("\n# ============================================\n")
                f.write("# Proxy Management (Epic 9 - Story 9.0)\n")
                f.write("# ============================================\n\n")
                f.write("# Proxy Encryption Key\n")
                f.write("# --------------------\n")
                f.write("# REQUIRED for proxy feature (Story 9.1+)\n")
                f.write("# Generate key using: uv run python scripts/generate_proxy_key.py\n")
                f.write("#\n")
                f.write("# ⚠️  SECURITY WARNINGS:\n")
                f.write("# - This key encrypts all proxy passwords\n")
                f.write("# - If you lose this key, all encrypted passwords are unrecoverable\n")
                f.write("# - NEVER commit this key to Git\n")
                f.write("# - Use password manager for production environments\n")
                f.write("#\n")
                f.write(f"# PROXY_ENCRYPTION_KEY={key}\n")
                f.write("\n# Proxy Health Check Configuration\n")
                f.write("# ----------------------------------\n")
                f.write("# These settings are used by Story 9.10 (Celery Beat health check)\n")
                f.write("# PROXY_HEALTH_CHECK_INTERVAL=300  # seconds (5 minutes)\n")
                f.write("# PROXY_HEALTH_CHECK_TIMEOUT=5\n")
                f.write("# PROXY_HEALTH_CHECK_URL=https://httpbin.org/ip\n")

            print(f"\n✅ Configuration added to {file_path}")
            print("   Please review the file and adjust as needed.")
        except Exception as e:
            print(f"\n❌ Error writing to {file_path}: {e}")
            sys.exit(1)


if __name__ == "__main__":
    main()
