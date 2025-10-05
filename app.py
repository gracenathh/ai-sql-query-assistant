from flask import Flask, render_template, request, redirect, url_for, session, flash 
import os, re, sqlite3 
import pandas as pd
from openai import OpenAI 

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "dev-key")
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# helper
def resolve_db_path():
    """Prefer uploaded DB saved in session; else fall back to local chinook.db."""
    db_path = session.get("db_path")
    if db_path and os.path.exists(db_path):
        return db_path
    fallback = "chinook.db"
    if os.path.exists(fallback):
        return fallback
    return None

def get_db_schema(db_path, max_chars=12000):
    con = sqlite3.connect(db_path)
    cur = con.cursor()
    cur.execute("""
        SELECT name, sql
        FROM sqlite_master
        WHERE type='table' AND name NOT LIKE 'sqlite_%'
        ORDER BY name
    """)
    rows = cur.fetchall()
    parts = []
    for name, create_sql in rows:
        cur.execute(f"PRAGMA table_info('{name}')")
        cols = cur.fetchall()  # cid, name, type, notnull, dflt_value, pk
        col_list = ", ".join([f"{c[1]} {c[2] or ''}".strip() for c in cols])
        parts.append(f"-- {name} ({col_list})\n{create_sql}")
    con.close()
    schema = "\n\n".join(parts)
    if len(schema) > max_chars:
        schema = schema[:max_chars] + "\n... (truncated)"
    return schema

def run_sql(db_path, sql):
    import re, sqlite3, pandas as pd

    # Only allow SELECT
    if not re.match(r"^\s*SELECT\b", sql, flags=re.IGNORECASE):
        raise ValueError("Only SELECT statements are allowed.")

    # 1) remove trailing semicolons so we never end up with "…; LIMIT 1000"
    sql = re.sub(r";+\s*$", "", sql.strip())

    # 2) autolimit only if there isn't a LIMIT already
    if not re.search(r"\blimit\b\s+\d+", sql, flags=re.IGNORECASE):
        sql += " LIMIT 1000"

    con = sqlite3.connect(db_path)
    try:
        df = pd.read_sql_query(sql, con)
    finally:
        con.close()
    return df

def llm_generate_sql(api_key, schema_text, question, model="gpt-4o-mini", db_path = None):
    client = OpenAI(api_key=api_key)
    prompt = f"""
                You are an expert SQL developer. Use the following SQLite schema to write ONE efficient and correct SQL query.

                Rules:
                - Optimise for performance.
                - Use only necessary columns, avoid SELECT *.
                - Use proper WHERE and LIMIT clauses.
                - Use explicit JOINs; correct GROUP BY.
                - Return ONLY raw SQL (no markdown, code fences, or explanations).
                - Do not include a trailing semicolon.

                Schema:
                {schema_text}

                Question:
                {question}
                """
    resp = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": "You generate correct SQL for SQLite given a schema and a question."},
            {"role": "user", "content": prompt},
        ],
        temperature=0.0,
    )
    sql = resp.choices[0].message.content.strip()
    sql = re.sub(r"^```[a-zA-Z]*\n|```$", "", sql).strip()  # strip code fences if any
    return sql

# ---------- routes ----------

@app.route("/", methods=["GET", "POST"])
def setup():
    if request.method == "POST":
        # save API key in session
        api_key = request.form.get("api_key", "").strip()
        if not api_key:
            flash("Please enter your OpenAI API key.", "error")
            return render_template("setup.html")
        session["api_key"] = api_key

        # optional DB upload
        file = request.files.get("db_file")
        if file and file.filename:
            save_path = os.path.join(UPLOAD_DIR, file.filename)
            file.save(save_path)
            session["db_path"] = save_path
        else:
            session["db_path"] = None  # will fall back to chinook.db
        
        # NEW: schema-only flag
        schema_only = request.form.get("schema_only") == "true"
        session["schema_only"] = schema_only

        # which button?
        action = request.form.get("action")
        if action == "schema":
            return redirect(url_for("schema_view"))
        return redirect(url_for("query"))

    return render_template("setup.html")

@app.route("/schema")
def schema_view():
    if not session.get("api_key"):
        return redirect(url_for("setup"))
    db_path = resolve_db_path()
    if not db_path:
        flash("No database uploaded and default 'chinook.db' not found.", "error")
        return redirect(url_for("setup"))

    schema_text = get_db_schema(db_path)

    return render_template(
        "schema.html",
        schema_text=schema_text,
        db_path=db_path,
        schema_only=session.get("schema_only", False)
    )

@app.route("/query", methods=["GET", "POST"])
def query():
    if not session.get("api_key"):
        return redirect(url_for("setup"))

    db_path = resolve_db_path()
    if not db_path:
        flash("No database uploaded and default 'chinook.db' not found.", "error")
        return redirect(url_for("setup"))

    sql = None
    df_html = None
    error = None
    question = None

    # always show schema excerpt in the left/right panel
    schema_excerpt = get_db_schema(db_path, max_chars=8000)

    if request.method == "POST":
        question = request.form.get("question", "").strip()
        if not question:
            error = "Please enter a question."
        else:
            try:
                # 1) Get SQL from LLM
                #    (removed db_path kwarg – your llm_generate_sql doesn't take it)
                sql = llm_generate_sql(session["api_key"], schema_excerpt, question)

                # 2) Clean: strip trailing semicolons; autolimit only if not present
                sql_clean = re.sub(r";+\s*$", "", sql.strip())
                if not re.search(r"\blimit\b\s+\d+", sql_clean, flags=re.IGNORECASE):
                    sql_clean += " LIMIT 1000"
                sql = sql_clean  # for display

                # 3) Respect schema-only mode
                if session.get("schema_only"):
                    df_html = None   # skip execution
                else:
                    df = run_sql(db_path, sql_clean)
                    df_html = df.to_html(classes="table table-striped", index=False)

            except Exception as e:
                error = str(e)

    return render_template(
        "query.html",
        sql=sql,
        df_html=df_html,
        error=error,
        question=question,
        schema_excerpt=schema_excerpt,
        schema_only=session.get("schema_only", False),
    )


if __name__ == "__main__":
    app.run(debug=True)