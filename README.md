# LegalGuard ID - Legal Document Review System

AI-powered compliance checker for company documents against Indonesian law using OpenAI gpt-4o and RAG (Retrieval-Augmented Generation).

## Key Features

1.  **Document Training**: Analyzes uploaded documents to create a structured "training module" of key clauses and legal mapping.
2.  **RAG Integration**: Stores training modules in PostgreSQL (pgvector) for semantic retrieval and long-term knowledge.
3.  **Indonesian Law Compliance**: Reviews documents against up-to-date Indonesian law categories (Employment, Contract, Corporate, Data Privacy, etc.).
4.  **Modern Interface**: Premium dark-mode web dashboard for seamless document management and review.

## Setup Instructions

### 1. Prerequisites
- Python 3.10+
- PostgreSQL with `pgvector` extension installed.

### 2. Environment Configuration
Create a `.env` file in the root directory (use `.env.example` as a template):
```env
OPENAI_API_KEY=your_key_here
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/your_db
```

### 3. Installation
```bash
# Activate virtual environment
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 4. Running the Application
```bash
# Start the FastAPI server
python -m app.main
```
Access the application at `http://localhost:8000`.

## Technology Stack
- **Backend**: FastAPI, SQLAlchemy, PostgreSQL + pgvector
- **AI/LLM**: OpenAI `gpt-4o` (latest model), LangChain
- **Frontend**: Vanilla JS, Modern CSS (Glassmorphism), Semantic HTML
- **Document Processing**: pdfplumber, python-docx
