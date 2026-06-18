# AI Chatbot ERD

This document captures the core data model for the AI chatbot backend.

## ERD Diagram

![AI Chatbot ERD](ai-chatbot-erd.png)

## Editable Source

- Draw.io source: [AI Chatbot ERD.drawio](AI%20Chatbot%20ERD.drawio)

## Main Entities

- `users`: stores account and identity details.
- `conversations`: groups messages by chat thread and owner.
- `messages`: stores user/assistant message history for each conversation.
- `refresh_token`: manages refresh-token lifecycle and user linkage.
- `tiers`: defines subscription tiers with token and message limits.
- `email_verification_token`: tracks email verification tokens and their state.
- `reset_password_token`: manages password reset token lifecycle.
- `usage_logs`: tracks usage and telemetry events.
- `audit-log`: records user actions for security and compliance auditing.

## Relationship Summary

- One `user` can have many `conversations`.
- One `conversation` can have many `messages`.
- One `user` can have many `refresh_token` records (over time/devices).
- `usage_logs` link activity to user/session-level behavior.
