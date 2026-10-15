"""Small SQLite service shared by real Hermes tool and HTTP adapters.

The service is intentionally model-free. Human-authored fixtures are not LLM output.
"""
import sqlite3
import uuid
from contextlib import contextmanager
from pathlib import Path


class LearningError(ValueError):
    pass


class Store:
    def __init__(self, path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as db:
            db.executescript("""
                CREATE TABLE IF NOT EXISTS metadata (key TEXT PRIMARY KEY, value TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS contexts (
                    id TEXT PRIMARY KEY, label TEXT NOT NULL, active INTEGER NOT NULL,
                    run_id TEXT NOT NULL, origin TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS hints (
                    id INTEGER PRIMARY KEY, context_id TEXT NOT NULL, run_id TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS attempts (
                    id TEXT PRIMARY KEY, context_id TEXT NOT NULL, run_id TEXT NOT NULL UNIQUE,
                    answer TEXT NOT NULL, assistance TEXT NOT NULL, status TEXT NOT NULL);
            """)
            db.execute("INSERT OR IGNORE INTO metadata VALUES ('store_id', ?)", (str(uuid.uuid4()),))

    @contextmanager
    def _connect(self):
        db = sqlite3.connect(self.path, timeout=5)
        try:
            db.row_factory = sqlite3.Row
            db.execute("PRAGMA journal_mode=WAL")
            db.execute("PRAGMA busy_timeout=5000")
            with db:
                yield db
        finally:
            db.close()

    def state(self):
        with self._connect() as db:
            return {
                "api_version": 1,
                "store_id": db.execute("SELECT value FROM metadata WHERE key='store_id'").fetchone()[0],
                "contexts": [dict(r) for r in db.execute("SELECT * FROM contexts ORDER BY rowid")],
                "attempts": [dict(r) for r in db.execute("SELECT * FROM attempts ORDER BY rowid")],
            }

    @staticmethod
    def _active(db, context_id):
        row = db.execute("SELECT * FROM contexts WHERE id=? AND active=1", (context_id,)).fetchone()
        if row is None:
            raise LearningError("No active tracking context. Use the explicit Start/Resume action first.")
        return row

    def start(self, label, *, origin):
        if origin not in {"workspace_action", "slash_command"}:
            raise LearningError("Only an explicit workspace action or user slash command can start tracking.")
        if not isinstance(label, str) or not label.strip() or len(label) > 120:
            raise LearningError("Provide a label of 1 to 120 characters.")
        context = {"id": str(uuid.uuid4()), "label": label.strip(), "active": 1,
                   "run_id": str(uuid.uuid4()), "origin": origin}
        with self._connect() as db:
            db.execute("INSERT INTO contexts VALUES (:id,:label,:active,:run_id,:origin)", context)
        return context

    def hint(self, context_id):
        with self._connect() as db:
            db.execute("BEGIN IMMEDIATE")
            context = self._active(db, context_id)
            db.execute("INSERT INTO hints(context_id,run_id) VALUES (?,?)", (context_id, context["run_id"]))
        return {"hint": "A client timeout tells you what the client observed, not whether the server completed the write. Trace those separately."}

    def leave(self, context_id):
        with self._connect() as db:
            db.execute("BEGIN IMMEDIATE")
            self._active(db, context_id)
            db.execute("UPDATE contexts SET active=0 WHERE id=?", (context_id,))
        return {"ok": True}

    def new_run(self, context_id):
        run_id = str(uuid.uuid4())
        with self._connect() as db:
            db.execute("BEGIN IMMEDIATE")
            self._active(db, context_id)
            db.execute("UPDATE contexts SET run_id=? WHERE id=?", (run_id, context_id))
        return {"run_id": run_id}

    def submit(self, context_id, run_id, answer):
        if not isinstance(answer, str) or not answer.strip() or len(answer) > 8000:
            raise LearningError("Write an answer of 1 to 8000 characters.")
        with self._connect() as db:
            db.execute("BEGIN IMMEDIATE")
            context = self._active(db, context_id)
            existing = db.execute("SELECT * FROM attempts WHERE context_id=? AND run_id=?", (context_id, run_id)).fetchone()
            if existing:
                if existing["answer"] != answer:
                    raise LearningError("This submission already committed a different answer. Start a new attempt.")
                return {"attempt": dict(existing), "duplicate": True, "criteria": list(CRITERIA)}
            if context["run_id"] != run_id:
                raise LearningError("This activity run is no longer current. Refresh before submitting.")
            assisted = db.execute("SELECT 1 FROM hints WHERE context_id=? AND run_id=? LIMIT 1", (context_id, run_id)).fetchone()
            attempt = {"id": str(uuid.uuid4()), "context_id": context_id, "run_id": run_id,
                       "answer": answer, "assistance": "targeted_hint" if assisted else "none",
                       "status": "awaiting_assessment"}
            db.execute("INSERT INTO attempts VALUES (:id,:context_id,:run_id,:answer,:assistance,:status)", attempt)
        return {"attempt": attempt, "duplicate": False, "criteria": list(CRITERIA)}


CRITERIA = (
    "Distinguish a client timeout from whether the first server-side write completed.",
    "Explain that an unprotected retry may repeat the effect; do not assume timeout means rollback.",
    "Describe how a correctly implemented idempotency mechanism can recognize the repeat, and note that retries alone do not provide this guarantee.",
)
