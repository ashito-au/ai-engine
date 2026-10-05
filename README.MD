AI Engine
A personal knowledge and idea-generation engine.
Core loop: Capture → Understand → Store → Retrieve → Connect → Generate
MVP
Save informative text
Extract topics/keywords
Store knowledge in SQLite
Search saved knowledge with TF-IDF retrieval
Generate an idea grounded in saved knowledge
Show which knowledge items were used
Works without an LLM; optionally uses OpenAI
Run locally
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
uvicorn backend.main:app --reload
Open http://127.0.0.1:8000
Optional AI generation
Copy .env.example to .env and add OPENAI_API_KEY. Without a key, the app uses a deterministic local generator.
Product direction
Next: URL/YouTube/PDF ingestion, embeddings/vector search, citations, knowledge graph, accounts, and automatic opportunity discovery.