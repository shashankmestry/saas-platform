"""Test environment defaults applied before application imports."""

import os

# Required by Settings when local .env lacks Storage credentials.
os.environ.setdefault("SUPABASE_SECRET_KEY", "test-supabase-secret-key")
