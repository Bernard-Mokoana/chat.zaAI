# FullStack AI Chatbot

This repository contains a small end-to-end chatbot system with three runtime parts:

- `client/`: a Next.js chat UI
- `server/`: a FastAPI app that creates sessions and hosts the WebSocket endpoint
- `worker/`: a Python background process that consumes Redis stream messages, calls a Hugging Face inference model, and publishes replies

The app currently uses:

- Redis for session persistence and stream-based message passing between server and worker
- PostgreSQL (via SQLAlchemy models) as the relational data layer foundation for users, conversations, messages, refresh tokens, and usage logs

## Current Architecture

The project is currently built around a token-based chat session flow:

1. The client collects a user's name.
2. The client calls `POST /token?name=...` on the FastAPI server.
3. The server creates a UUID token, stores a chat session in Redis JSON, and sets a 1-hour expiry.
4. The client opens `ws://.../chat?token=...`.
5. User messages are written by the server into the Redis stream `message_channel`.
6. The worker reads from `message_channel`, updates Redis chat history, calls the Hugging Face model, and writes the answer into `response_channel`.
7. The server listens for matching replies on `response_channel` and forwards them to the correct WebSocket client.

## High-level Design

The system is split into three runtime services connected through Redis:

- `client` (Next.js): browser UI, session bootstrap, WebSocket chat transport, local message rendering/state
- `server` (FastAPI): token/session management, WebSocket gateway, Redis stream producer/consumer bridge
- `worker` (Python): background consumer that reads user messages, calls the model, and publishes responses

Core data movement:

1. Browser gets a token from FastAPI and opens a WebSocket with that token.
2. Server writes user messages to Redis stream `message_channel`.
3. Worker consumes `message_channel`, updates Redis JSON history, generates a model reply, then writes to `response_channel`.
4. Server listens for the token-matched reply and pushes it back over the same client WebSocket.

Data persistence is currently hybrid:

- Active chat session flow: Redis JSON + Redis Streams
- Relational domain model and migrations: PostgreSQL + SQLAlchemy + Alembic (newly added scaffolding)

## Chatbot Architecture

![Chatbot Architecture](Application%20Architecture/Chatbot_Architecture.jpg)

## Data Model (ERD)

The backend entity relationships are documented here:

- [AI Chatbot ERD documentation](docs/ai-chatbot-erd.md)
- [Database read/write strategy and failover runbook](docs/database-read-write-strategy.md)
- Editable Draw.io source: [docs/AI Chatbot ERD.drawio](docs/AI%20Chatbot%20ERD.drawio)
- Image export: [Application Architecture/AI Chatbot ERD.jpg](Application%20Architecture/AI%20Chatbot%20ERD.jpg)

## Repository Layout

```text
.
|-- client/                         Next.js frontend
|   |-- src/app/                    App Router pages
|   |-- src/features/chat/          Chat UI and session logic
|   |-- src/services/               HTTP, WebSocket, and localStorage helpers
|   `-- package.json
|-- backend/server/                         FastAPI API + WebSocket gateway
|   |-- src/routes/chat.py          Token + refresh + WebSocket routes
|   |-- src/socket/                 WebSocket helpers
|   |-- src/database/               SQLAlchemy config + relational models
|   `-- src/redis/                  Redis connection and stream helpers
|   |-- alembic/                    Migration environment
|   `-- alembic.ini                 Alembic configuration
|-- backend/worker/                         Redis consumer + model caller
|   |-- src/model/gptj.py           Hugging Face inference client
|   `-- src/redis/                  Redis cache/stream helpers
|-- docs/                           Notes on design and requirements
|-- Application Architecture/       Draw.io architecture source
|-- requirements.txt                Python dependencies
`-- README.md
```

## Tech Stack

### Frontend

![Next.js](https://img.shields.io/badge/Next.js-111111?style=for-the-badge&logo=nextdotjs&logoColor=white)
![React](https://img.shields.io/badge/React-20232A?style=for-the-badge&logo=react&logoColor=61DAFB)
![TypeScript](https://img.shields.io/badge/TypeScript-3178C6?style=for-the-badge&logo=typescript&logoColor=white)
![Tailwind CSS](https://img.shields.io/badge/Tailwind_CSS-38B2AC?style=for-the-badge&logo=tailwindcss&logoColor=white)
![Axios](https://img.shields.io/badge/Axios-5A29E4?style=for-the-badge&logo=axios&logoColor=white)
![Motion](https://img.shields.io/badge/Motion-000000?style=for-the-badge&logo=framer&logoColor=white)

### Backend

![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white)
![Uvicorn](https://img.shields.io/badge/Uvicorn-4051B5?style=for-the-badge&logo=uvicorn&logoColor=white)
![Redis](https://img.shields.io/badge/Redis-DC382D?style=for-the-badge&logo=redis&logoColor=white)
![Redis JSON](https://img.shields.io/badge/Redis_JSON-B91C1C?style=for-the-badge&logo=redis&logoColor=white)
![WebSockets](https://img.shields.io/badge/WebSockets-0F172A?style=for-the-badge&logo=socketdotio&logoColor=white)
![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-D71F00?style=for-the-badge&logo=sqlalchemy&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-336791?style=for-the-badge&logo=postgresql&logoColor=white)
![Alembic](https://img.shields.io/badge/Alembic-111111?style=for-the-badge&logo=alembic&logoColor=white)

### Model Worker

![Hugging Face](https://img.shields.io/badge/Hugging_Face-FFD21E?style=for-the-badge&logo=huggingface&logoColor=black)
![Redis Streams](https://img.shields.io/badge/Redis_Streams-DC2626?style=for-the-badge&logo=redis&logoColor=white)

## How The Client Behaves

The Next.js app has two pages:

- `/`: asks for a display name, creates a session token, stores `chat_name` and `chat_token` in `localStorage`, then redirects to `/chat`
- `/chat`: restores the name from storage, opens a WebSocket connection, restores Redis-backed history when possible, and keeps a local copy of rendered messages in `localStorage`

Important implementation details:

- The client expects `NEXT_PUBLIC_WS_URL` to be set. `client/src/services/ws/chatSocket.ts` throws during import if it is missing.
- The server CORS config currently allows `http://localhost:3001`.
- Because of that, the frontend should be run on port `3001` unless you change the server CORS config.

## API Surface

### HTTP

- `GET /test`
  Returns a simple health payload.

- `POST /token?name=...`
  Creates a chat session and returns:

```json
{
  "token": "uuid",
  "messages": [],
  "name": "user name",
  "session_start": "ISO timestamp"
}
```

- `GET /refresh_token?token=...`
  Returns the stored session if the token still exists, otherwise returns `400`.

### WebSocket

- `GET /chat?token=...`
  Accepts raw text user messages and returns bot responses for that token.

## Redis Usage

Redis is doing two jobs in this project:

- Session storage:
  Each chat token is stored as a Redis JSON document with message history and a 1-hour TTL.
- Stream-based message passing:
  - `message_channel`: user messages from server to worker
  - `response_channel`: model responses from worker back to server

The worker also prefixes stored messages in Redis history:

- human messages are stored as `Human: ...`
- bot messages are stored as `Bot: ...`

The client strips those prefixes back out when rebuilding chat history.

## Environment Variables

There is no checked-in sample env file yet, so use these values as a reference.

### Root Python dependencies

Install from the repository root:

```powershell
pip install -r requirements.txt
```

### `server/.env`

```env
APP_ENV=development
REDIS_URL=redis://localhost:6379/0
DATABASE_PRIMARY_URL=postgresql+psycopg://postgres:password@localhost:5432/chatbot
DATABASE_REPLICA_URL=postgresql+psycopg://postgres:password@localhost:5432/chatbot
DATABASE_READ_FROM_REPLICA=true
DATABASE_ALLOW_REPLICA_FALLBACK=true
```

Notes:

- `server/src/redis/config.py` currently reads `REDIS_URL`.
- `backend/database/config/databaseConfig.py` requires `DATABASE_PRIMARY_URL`.
- `DATABASE_REPLICA_URL` is optional in local development when `DATABASE_ALLOW_REPLICA_FALLBACK=true`; production should provide a real read-replica URL or explicitly set `DATABASE_READ_FROM_REPLICA=false` during maintenance.
- `python server/main.py` only starts Uvicorn when `APP_ENV=development`.

### Database migrations (Alembic)

From the `server/` directory:

```powershell
alembic upgrade head
```

To create a new migration after model changes:

```powershell
alembic revision --autogenerate -m "describe_change"
alembic upgrade head
```

### `worker/.env`

```env
REDIS_URL=redis://localhost:6379/0
HUGGINFACE_INFERENCE_TOKEN=hf_xxx
MODEL_ID=katanemo/Arch-Router-1.5B
MAX_NEW_TOKENS=25
```

Notes:

- The code expects the variable name `HUGGINFACE_INFERENCE_TOKEN` exactly as spelled above.
- `MODEL_ID` is optional if `MODEL_URL` is provided, but `MODEL_ID` is the simplest option.

### `client/.env.local`

```env
NEXT_PUBLIC_API_URL=http://localhost:3500
NEXT_PUBLIC_WS_URL=ws://localhost:3500
```

Notes:

- The WebSocket helper removes a trailing `/chat` if you include it, so either `ws://localhost:3500` or `ws://localhost:3500/chat` will work.

## Running Locally

You need four processes:

1. Redis with Redis JSON support
2. FastAPI server
3. Worker
4. Next.js client

### 1. Start Redis

Use Redis Stack or another Redis instance with Redis JSON available. The app relies on `.json()` operations for session history.

### 2. Start the FastAPI server

From the repository root:

```powershell
cd server
python main.py
```

If you do not want to rely on `APP_ENV=development`, you can also run:

```powershell
cd server
uvicorn main:api --host 0.0.0.0 --port 3500 --reload
```

### 3. Start the worker

```powershell
cd worker
python main.py
```

### 4. Start the client

```powershell
cd client
npm install
npm run dev -- --port 3001
```

Then open `http://localhost:3001`.

## End-to-End Flow

Once everything is running:

1. Visit the landing page.
2. Enter a name.
3. The client creates a session token.
4. The chat page opens a WebSocket connection using that token.
5. Messages are sent over the socket as plain text.
6. The worker generates a response through Hugging Face.
7. The response is pushed back to the browser and rendered in the chat UI.

## Project Notes

This repo also contains planning material that is useful for future work:

- [docs/design.md](docs/design.md)
- [docs/requirements.md](docs/requirements.md)
- [docs/ai-chatbot-erd.md](docs/ai-chatbot-erd.md)
- [docs/AI Chatbot ERD.drawio](docs/AI%20Chatbot%20ERD.drawio)
- [Application Architecture/Chatbot Architecture.drawio](<Application Architecture/Chatbot Architecture.drawio>)
- [Application Architecture/Chatbot_Architecture.jpg](Application%20Architecture/Chatbot_Architecture.jpg)
- [Application Architecture/AI Chatbot ERD.jpg](Application%20Architecture/AI%20Chatbot%20ERD.jpg)
- `notes.txt`

Some of those notes describe future Auth0-based work that is not yet implemented in the current codebase.

## Known Gaps And Gotchas

- No automated test suite is present yet.
- `server/main.py` does not start anything unless `APP_ENV=development` is set.
- The client requires `NEXT_PUBLIC_WS_URL`; without it, the frontend will fail at import time.
- The FastAPI CORS allowlist is hard-coded to `http://localhost:3001`.
- Redis JSON support is required, not just a plain Redis server.
- The worker currently sends back whole model responses rather than token-by-token streaming.

## Next Good Improvements

- Add `.env.example` files for `client`, `server`, and `worker`
- Add a Docker Compose setup for Redis + server + worker + client
- Add tests for session creation, token refresh, and WebSocket flow
- Align CORS and frontend default port
- Add deployment instructions once the runtime setup stabilizes
