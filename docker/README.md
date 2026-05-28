# Docker Services

## Quick Start

```bash
# Start all services
docker compose up -d

# Check status
docker compose ps

# View logs
docker compose logs -f mongodb
docker compose logs -f sftp

# Stop all services
docker compose down

# Stop and remove volumes (clears all data)
docker compose down -v
```

## MongoDB

- **Port:** 27017
- **Credentials:** admin / admin123
- **Database:** reconciliation
- **Data volume:** `mongo_data` (persistent)
- **Init script:** `docker/init-mongo.js` — auto-creates collections and indexes on first run

### Connect

```bash
# MongoDB Shell
docker exec -it reconciliation-mongo mongosh -u admin -p admin123

# From Python (with uv)
APP_MONGODB_URL=mongodb://admin:admin123@localhost:27017/reconciliation?authSource=admin \
  uv run python -c "
    from motor.motor_asyncio import AsyncIOMotorClient
    import asyncio
    async def main():
        client = AsyncIOMotorClient('mongodb://admin:admin123@localhost:27017/reconciliation?authSource=admin')
        print(await client.list_database_names())
    asyncio.run(main())
  "
```

## SFTP

- **Port:** 2222
- **Credentials:** foo / pass
- **Upload directory:** `./sftp_data` (mapped to `/home/foo/upload`)
- **Config:** `sftp_conf/users.conf`

### Upload files

```bash
# Via command line
sftp -P 2222 foo@localhost
# Password: pass
# Then: put m4becomvsp_07072024_combine.xlsx /upload/

# Via script
scp -P 2222 m4becomvsp_07072024_combine.xlsx foo@localhost:/upload/
```

### Add more users

Edit `sftp_conf/users.conf`:

```
# username:password:uid:gid:directory
foo:pass:::upload
bar:secret123:::upload
```

Then restart: `docker compose restart sftp`

## Environment Variables

Copy `.env.example` to `.env` and update:

```bash
APP_MONGODB_URL=mongodb://admin:admin123@localhost:27017/reconciliation?authSource=admin
APP_DB_NAME=reconciliation
SFTP_HOST=localhost
SFTP_PORT=2222
SFTP_USER=foo
SFTP_PASS=pass
```
