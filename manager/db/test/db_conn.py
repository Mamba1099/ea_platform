from sqlalchemy import text

from manager.db.database import engine


def main():
    with engine.connect() as connection:
        result = connection.execute(text("SELECT version()"))

        print("PostgreSQL connection successful:")
        print(result.scalar())


if __name__ == "__main__":
    main()
