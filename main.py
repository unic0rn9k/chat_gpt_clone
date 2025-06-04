from fastapi import Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from llama_index.llms.ollama import Ollama
from concurrent.futures import ThreadPoolExecutor
import pandas as pd
from sqlalchemy import create_engine
import psycopg2
from psycopg2 import pool
from fastapi import FastAPI, Depends, Form
import datetime as dt
from psycopg2.extras import execute_values
from fastapi.templating import Jinja2Templates
import uuid
from fastapi.responses import RedirectResponse

psycopg2.extras.register_uuid()

templates = Jinja2Templates(directory="templates")
app = FastAPI(debug=True)

executor = ThreadPoolExecutor(max_workers=10)

app.mount("/static", StaticFiles(directory="static"), name="static")

DATABASE_URL = "postgresql://postgres:postgres@postgres:5432/mydb"
connection_pool = psycopg2.pool.SimpleConnectionPool(
    minconn=1,
    maxconn=10,
    dsn=DATABASE_URL
)

init_tables = """
            CREATE TABLE users (
                username VARCHAR(255) PRIMARY KEY,
                password VARCHAR(255) NOT NULL
            );
            
            CREATE TABLE chats (
                id UUID PRIMARY KEY,
                topic VARCHAR(255),
                username VARCHAR(255) NOT NULL,
                FOREIGN KEY (username) REFERENCES users(username)
            );
            
            CREATE TABLE messages (
                author VARCHAR(255),
                id INT NOT NULL,
                chat_id UUID NOT NULL,
                content TEXT,
                timestamp TIMESTAMP,
                PRIMARY KEY (id, author),
                FOREIGN KEY (chat_id) REFERENCES chats(id)
            );
"""

def get_db_conn():
    conn = None
    try:
        conn = connection_pool.getconn()
        yield conn
    finally:
        if conn:
            connection_pool.putconn(conn)

with connection_pool.getconn().cursor() as cur:
    try:
        cur.execute(init_tables)
    except Exception as e:
        pass
    finally:
        cur.close()

@app.get("/", response_class=HTMLResponse)
async def get_chat_page():
    with open("static/login.html", "r") as file:
        return file.read()
    
@app.get("/register", response_class=HTMLResponse)
async def get_register_page():
    with open("static/register.html", "r") as file:
        return file.read()

import re

@app.post("/generate/{chat_id}")
async def generate(chat_id: str, request: Request, conn=Depends(get_db_conn)):
    body = await request.json()
    message = body.get("message")

    if not message:
        return JSONResponse(content={"error": "Missing message"}, status_code=400)

    with conn.cursor() as cur:
        cur.execute("SELECT COUNT(*) FROM messages;")
        msg_count = cur.fetchone()[0]

        now = dt.datetime.now()

        llm = Ollama(model="qwen3:0.6b", request_timeout=240.0, base_url="ollama:11434")
        bot_response = f"{llm.complete(message, timeout=None)}"

        # Insert user and bot messages
        data = [
            ("User", msg_count, message, now, chat_id),
            ("Bot", msg_count + 1, bot_response, now, chat_id),
        ]
        insert_query = """
            INSERT INTO messages (author, id, content, timestamp, chat_id)
            VALUES %s
        """
        execute_values(cur, insert_query, data)

        # Check current topic
        cur.execute("SELECT topic FROM chats WHERE id = %s", (chat_id,))
        current_topic = cur.fetchone()[0]
        
        default_topic_pattern = r"^Chat from \d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}(?:\.\d+)?$"
        if re.match(default_topic_pattern, current_topic):
            topic_prompt = f"Generate a topic for a chat based on following prompt, It should be max 8 words and rephrase the message. Here is the message: {message}\n\n"
            response = llm.complete(topic_prompt, timeout=30.0)
            clean_text = re.sub(r"<think>.*?</think>", "", response.text, flags=re.DOTALL).strip()

            chat_topic = clean_text.split("\n")[0].strip()

            if len(chat_topic) > 60:
                chat_topic = chat_topic[:60] + "..."

            cur.execute("UPDATE chats SET topic = %s WHERE id = %s", (chat_topic, chat_id))
        
    conn.commit()

    return JSONResponse(content={"text": bot_response, "topic": chat_topic if 'chat_topic' in locals() else current_topic})


def get_db_connection():
    return psycopg2.connect(
        dbname="mydb",
        user="postgres",
        password="postgres",
        host="postgres",
        port=5432
    )

@app.post("/register")
async def register(request: Request):
    data = await request.json()  # Manually parse JSON
    username = data.get("username")
    password = data.get("password")

    if not username or not password:
        return JSONResponse(status_code=400, content={"error": "Username and password required"})

    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        cur.execute("SELECT username FROM users WHERE username = %s;", (username,))
        if cur.fetchone():
            return JSONResponse(status_code=400, content={"error": "Username already exists"})

        cur.execute(
            "INSERT INTO users (username, password) VALUES (%s, %s);",
            (username, password)
        )
        conn.commit()
        cur.close()
        return {"message": "User registered successfully"}
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": f"Registration failed: {e}"})
    finally:
        if conn:
            conn.close()

def available_chats(username, conn):
    return pd.read_sql(f"select * from chats where username = '{username}'", conn)

@app.post("/new_chat")
async def new_chat(username: str = Form(...), password: str = Form(...), conn=Depends(get_db_conn)):
    cur = conn.cursor()
    now = dt.datetime.now()

    id = uuid.uuid4()
    cur.execute(
        "INSERT INTO chats (id, topic, username) VALUES (%s, %s, %s);",
        (id, f'Chat from {now}', username))

    conn.commit()
    conn.close()
    return RedirectResponse(url=f"/chat/{id}", status_code=303)

@app.post("/login")
async def login(request: Request, username: str = Form(...), password: str = Form(...), conn=Depends(get_db_conn)):
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE username = %s AND password = %s", (username, password))
    user = cur.fetchone()

    if user:
        cur.execute("SELECT id, topic FROM chats WHERE username = %s", (username,))
        chats = [{"id": row[0], "topic": row[1]} for row in cur.fetchall()]
        conn.close()

        return templates.TemplateResponse("chat_list.html", {
            "request": request,
            "username": username,
            "chats": chats
        })
    else:
        conn.close()
        return RedirectResponse("/static/loginerror.html", status_code=303)

@app.get("/chat/{id}", response_class=HTMLResponse)
async def chat(request: Request, id: str, conn=Depends(get_db_conn)):
    cur = conn.cursor()
    # Get the chat owner username (to know who owns this chat)
    cur.execute("SELECT username FROM chats WHERE id = %s", (id,))
    result = cur.fetchone()
    if not result:
        return HTMLResponse("Chat not found", status_code=404)
    chat_owner = result[0]

    # Get all messages for this chat ordered by timestamp
    cur.execute(
        "SELECT author, content FROM messages WHERE chat_id = %s ORDER BY timestamp ASC",
        (id,)
    )
    messages = [{"author": row[0], "content": row[1]} for row in cur.fetchall()]
    cur.close()
    conn.close()

    # For demo, assume user viewing the chat is the chat owner
    username = chat_owner

    return templates.TemplateResponse("chat_page.html", {
        "request": request,
        "chat_id": id,
        "messages": messages,
        "username": username
    })


@app.get("/initialize")
async def initialize():
    conn = None
    try:
        conn = psycopg2.connect(
            dbname="mydb",
            user="postgres",
            password="postgres",
            host="postgres",
            port=5432
        )
        cur = conn.cursor()
        cur.execute(f"""
            DROP TABLE IF EXISTS messages;
            DROP TABLE IF EXISTS chats;
            DROP TABLE IF EXISTS users;
            {init_tables}
        """)
        conn.commit()
        cur.close()
        return "✅ Table created successfully!"
    except Exception as e:
        return f"❌ Failed to connect or create table: {e}"
    finally:
        if conn:
            conn.close()
