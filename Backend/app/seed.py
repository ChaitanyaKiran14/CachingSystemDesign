import asyncio
from prisma import Prisma

db = Prisma()

async def main():
    await db.connect()
    user = await db.user.create(
        data={
            "username": "alice",
            "posts": {
                "create": [
                    {"caption": "My first post!", "imageUrl": "https://picsum.photos/200"},
                    {"caption": "Beautiful sunset 🌅", "imageUrl": "https://picsum.photos/201"},
                ]
            }
        }
    )
    print("✅ Seeded user:", user.username)
    await db.disconnect()

if __name__ == "__main__":
    asyncio.run(main())
