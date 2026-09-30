# Common Foundation Architecture

```text
React + Vite
     |
     | REST
     v
FastAPI modular monolith
     |
     +---- PostgreSQL
     |       +---- pgvector (later)
     |
     +---- Ollama (later, AI modules only)
```

No Docker. No mobile application in the current implementation.

The backend is organized by business capability so each team member can own an end-to-end module.
