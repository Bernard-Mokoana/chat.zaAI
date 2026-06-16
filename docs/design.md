# Design (Chat-Only v0.2)

## Frontend (Next.js)
- Auth0 login/logout + route protection.
- Chat UI: messages list + input.
- Client calls backend endpoint: `POST /api/chat`.

## Backend (Python)
- `POST /api/chat` takes a message + optional conversation context.
- Validates Auth0 token.
- Returns JSON: `{ answer, messages? }`.

## Data Flow
User -> Auth0 -> Frontend -> Backend -> Response -> UI.

## Notes
- Start with non-streaming responses.
- Add search later as a parallel mode or separate page.
