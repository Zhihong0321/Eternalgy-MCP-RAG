from sqlmodel import create_engine, SQLModel
from sqlalchemy.schema import CreateTable
from sqlalchemy.dialects import postgresql
import models

def generate_ddl():
    engine = create_engine("postgresql://user:pass@localhost/db")
    metadata = SQLModel.metadata
    
    # Sort tables to respect foreign keys (roughly, though CreateTable doesn't strictly order them, we can list them)
    # Better to iterate over tables in metadata
    
    ddl_statements = []
    
    for table in metadata.sorted_tables:
        create_table = CreateTable(table)
        # Compile to Postgres string
        ddl = create_table.compile(engine, dialect=postgresql.dialect())
        ddl_statements.append(str(ddl).strip() + ";")
        
    return "\n\n".join(ddl_statements)

if __name__ == "__main__":
    print(generate_ddl())
