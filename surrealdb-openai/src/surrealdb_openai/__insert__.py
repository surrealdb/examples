import asyncio
from surrealdb_openai.__main__ import surreal_insert


def main():
    asyncio.run(surreal_insert())

if __name__ == "__main__":
    main()