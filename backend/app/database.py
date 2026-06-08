from sqlalchemy.orm import declarative_base

# Base is kept for the User model definition.
# All actual DB operations go through the Supabase PostgREST client (see dependencies.py).
Base = declarative_base()
