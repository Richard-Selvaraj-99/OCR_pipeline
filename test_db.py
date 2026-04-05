try:
    from app.db.mongo import client
    print("✅ Successfully imported client!")
    
    # This actually tries to talk to the cloud
    import asyncio
    async def check():
        try:
            info = await client.server_info()
            print("✅ Connected to MongoDB Atlas!")
            print(f"Server Info: {info.get('version')}")
        except Exception as e:
            print(f"❌ Connection failed: {e}")

    asyncio.run(check())

except ImportError as e:
    print(f"❌ Import Error: {e}")
except Exception as e:
    print(f"❌ Unexpected Error: {e}")