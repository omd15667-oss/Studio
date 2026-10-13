"""Initialize the SQLite database (create tables)."""
from db.session import engine
from db.session import Base

print("Creating database tables...")
Base.metadata.create_all(bind=engine)
print("Done.")
