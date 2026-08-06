def normalize_email(email: str) -> str:
    """Trim and lowercase an email for storage and comparison."""
    return email.strip().lower()
