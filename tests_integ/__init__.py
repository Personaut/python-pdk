"""Integration tests for Personaut PDK.

These tests require active API credentials and network access.
They are separate from unit tests and should be run explicitly.

Usage:
    pytest tests_integ/ -v --tb=short

Environment variables required:
    - GOOGLE_API_KEY: For Gemini tests
    - AWS_ACCESS_KEY_ID: For Bedrock tests
    - AWS_SECRET_ACCESS_KEY: For Bedrock tests
    - AWS_DEFAULT_REGION: For Bedrock tests (default: us-east-1)
"""
