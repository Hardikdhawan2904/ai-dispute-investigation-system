# Database Setup — BFSI Dispute Investigation Platform

Step-by-step instructions to stand up the database on a new system. Two ways to
do it — pick one.

---

## Option A — Run the schema file directly (recommended for a DBA / manual setup)

**1. Install PostgreSQL** (if not already installed)
- Windows: https://www.postgresql.org/download/windows/
- Mac: `brew install postgresql@16`
- Linux: `sudo apt install postgresql`

**2. Create the database**
```bash
psql -U postgres -c "CREATE DATABASE bfsi_dispute_db;"
```

**3. Run the schema file against it**
```bash
psql -U postgres -d bfsi_dispute_db -f schema.sql
```
This creates all 13 tables, indexes, and foreign keys in one shot. `schema.sql`
is in the same `docs/` folder as this file.

**4. Verify**
```bash
psql -U postgres -d bfsi_dispute_db -c "\dt"
```
You should see 13 tables listed.

**5. (Optional) Load sample data**

`schema.sql` only creates empty tables. If you also want the full demo dataset
(1,000 customers, 11,500+ transactions, 99 merchants, historical disputes,
etc.), load `data.sql` right after `schema.sql`:
```bash
psql -U postgres -d bfsi_dispute_db -f data.sql
```
Skip this step if you want to start with a completely empty database instead.

---

## Option B — Let the application create it automatically

The backend creates the same schema itself on first startup — no `schema.sql`
needed, just an empty database for it to connect to.

**1. Install PostgreSQL** and create an empty database (steps 1–2 above).

**2. Install Python dependencies**
```bash
cd backend
python -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate     # Mac/Linux
pip install -r requirements.txt
```

**3. Configure environment variables**
```bash
copy .env.example .env          # Windows
# cp .env.example .env          # Mac/Linux
```
Then edit `.env` and set:
```
DATABASE_URL=postgresql://postgres:<your-password>@localhost:5432/bfsi_dispute_db
GROQ_API_KEY=<your key from https://console.groq.com/keys>
```

**4. Start the backend**
```bash
uvicorn main:app --reload
```
On startup, `init_db()` calls SQLAlchemy's `Base.metadata.create_all()`, which
creates every table defined in `backend/database/models.py` if it doesn't
already exist. Nothing else to run.

To load the sample dataset here too, stop the app and run `data.sql` (see
step 5 in Option A) against the same database once the tables exist.

---

## Which option to use

- **Option A** if your boss wants to inspect/review the schema before anything
  runs, or hand it to a DBA who won't be touching the Python app.
- **Option B** if they're setting up the full project to actually run it —
  simpler, and guaranteed to stay in sync with the code since it's generated
  from the same model definitions every time.

Both produce the identical schema — `schema.sql` is a hand-mirrored copy of
what `Base.metadata.create_all()` generates from `backend/database/models.py`.

## Requirements

- PostgreSQL 13+
- Python 3.11+ (developed on 3.13)
- A Groq API key (free tier available) for the AI agents to run
