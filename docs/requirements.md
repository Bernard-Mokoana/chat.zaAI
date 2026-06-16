<!-- # Requirements (Chat-Only v0.2)

## Goal

Build a chatbot web app where authenticated users can have conversations (chat) to ask questions and troubleshoot.

## Primary User

General users.

## Core Use Cases (Day One)

1. Log in via Auth0.
2. Ask a question in chat and receive a response.
3. Continue a multi-turn conversation.

## Authentication

- Must use Auth0.
- Only authenticated users can access chat.

## Constraints

- Keep current stack: Next.js (`client`) + Python (`server`).
- Rebuild from clean `client/src`.

## Assumptions

- Single chat UI.
- Non-streaming responses initially.
- Minimal history: in-memory only (persistence can be added later).

## Non-Goals (Day One)

- Search mode.
- Advanced analytics.
- Team workspaces or admin dashboards. -->

<!-- Functional & Non-Functional Requirements -->

1. User registration and authentication
2. Create and manage conversations
3. Send messages and receive streaming Ai responses via websockets
4. Save all conversations with full history
5. Retrieve past conversations
6. Stream responses token by token
7. Rate limiting (requests + tokens)
8. Control moderation for harmful requests

<!-- Non-functional Requirements --> // How well it must perfom

1. Availability: 99.9% - Max 43 minutes downtime per month
2. Latency: First token <2 seconds - Users wait no more than 2 seconds
3. Scalability: 200M DAU, 20M concurrent conversations (assuming 10% concurrency)
4. Consistency: Zero message loss - Every message must be saved
5. Cost efficient: - LLM APIs are expensive, need optimization
6. Security: End-to-end encryption - Private conversations
