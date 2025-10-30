from sqlalchemy import inspect
from db import engine
from models import Base

# Get the metadata of your Base class
metadata = Base.metadata

# Create an inspector object
inspector = inspect(engine)

# Iterate over all tables in the metadata
for table in metadata.tables.values():
    # Get the foreign key constraints for the table
    foreign_keys = inspector.get_foreign_keys(table.name)

    # Print the foreign key constraints
    print(f"Foreign key constraints for table {table.name}:")
    for fk in foreign_keys:
        print(f"- {fk['constrained_columns']}: {fk['column']}")