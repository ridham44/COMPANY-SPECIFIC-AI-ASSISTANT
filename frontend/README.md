# Frontend

Two pages, talking to the backend over plain fetch calls:

- `/knowledge-base` - drag-and-drop upload, a table of documents with status
  badges (processing/indexed/failed), delete and re-index.
- `/chat` - ask a question, get an answer with source chips underneath,
  browse and delete past conversations in the sidebar.

There's no auth yet (that's a later phase), so the top bar has a "Workspace"
box that just sets `company_id` by hand for testing - each workspace name is
its own isolated knowledge base.

## Running it

```bash
cd frontend
npm install
cp .env.local.example .env.local   # points at the backend, edit if needed
npm run dev
```

Then open http://localhost:3000. The backend needs to be running separately
(see `../backend/README.md` and `../SETUP.md`).
