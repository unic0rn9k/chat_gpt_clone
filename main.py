from fastapi import FastAPI
from fastapi import Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from llama_index.llms.ollama import Ollama
from fastapi import FastAPI
from concurrent.futures import ThreadPoolExecutor
import pandas as pd
from sqlalchemy import create_engine
import psycopg2
from psycopg2 import pool
from fastapi import FastAPI, Depends
import datetime as dt
from psycopg2.extras import execute_values

app = FastAPI(debug=True)
executor = ThreadPoolExecutor(max_workers=10)

app.mount("/static", StaticFiles(directory="static"), name="static")

DATABASE_URL = "postgresql://postgres:postgres@postgres:5432/mydb"
connection_pool = psycopg2.pool.SimpleConnectionPool(
    minconn=1,
    maxconn=10,
    dsn=DATABASE_URL
)

def get_db_conn():
    conn = None
    try:
        conn = connection_pool.getconn()
        yield conn
    finally:
        if conn:
            connection_pool.putconn(conn)

@app.get("/", response_class=HTMLResponse)
async def get_chat_page():
    with open("static/index.html", "r") as file:
        return file.read()
    
@app.get("/login", response_class=HTMLResponse)
async def get_login_page():
    with open("static/login.html", "r") as file:
        return file.read()
    
@app.get("/register", response_class=HTMLResponse)
async def get_register_page():
    with open("static/register.html", "r") as file:
        return file.read()

@app.get("/chat/{message}")
async def chat(message: str, conn=Depends(get_db_conn)):
    with conn.cursor() as cur:
        cur.execute("SELECT COUNT(*) FROM messages;")
        msg_count = cur.fetchone()[0]

        now = dt.datetime.now()

        llm = Ollama(model="qwen3:0.6b", request_timeout=240.0, base_url="ollama:11434")
        response = f"{llm.complete(message, timeout=None)}"
        data = [
            ("user", msg_count, message, now, 0),
            ("bot", msg_count, response, now, 0)
        ]

        insert_query = """
            INSERT INTO messages (author, id, content, timestamp, chat_id)
            VALUES %s
        """

        execute_values(cur, insert_query, data)
    conn.commit()

    return response

#app = FastAPI()
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

        cur.execute("SELECT username FROM USER WHERE username = %s;", (username,))
        if cur.fetchone():
            return JSONResponse(status_code=400, content={"error": "Username already exists"})

        cur.execute(
            "INSERT INTO USER (username, password) VALUES (%s, %s);",
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

@app.post("/login")
async def login(request: Request):
    data = await request.json()  # Manually parse JSON
    username = data.get("username")
    password = data.get("password")

    if not username or not password:
        return JSONResponse(status_code=400, content={"error": "Username and password required"})

    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        cur.execute("SELECT password FROM USER WHERE username = %s;", (username,))
        record = cur.fetchone()
        cur.close()

        if not record or record[0] != password:
            return JSONResponse(status_code=401, content={"error": "Invalid username or password"})

        return {"message": "Login successful"}
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": f"Login failed: {e}"})
    finally:
        if conn:
            conn.close()

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
        cur.execute("""
            CREATE TABLE users (
                username VARCHAR(255) PRIMARY KEY,
                password VARCHAR(255) NOT NULL
            );
            
            CREATE TABLE chats (
                id INT PRIMARY KEY,
                topic VARCHAR(255),
                username VARCHAR(255) NOT NULL,
                FOREIGN KEY (username) REFERENCES users(username)
            );
            
            CREATE TABLE messages (
                author VARCHAR(255),
                id INT NOT NULL,
                chat_id INT NOT NULL,
                content TEXT,
                timestamp TIMESTAMP,
                PRIMARY KEY (id, author),
                FOREIGN KEY (author) REFERENCES users(username),
                FOREIGN KEY (chat_id) REFERENCES chats(id)
            );
        """)
        conn.commit()
        cur.close()
        return "✅ Table created successfully!"
    except Exception as e:
        return f"❌ Failed to connect or create table: {e}"
    finally:
        if conn:
            conn.close()

@app.get("/load_data")
def load_data():
    try:
        engine = create_engine("postgresql://postgres:postgres@postgres:5432/mydb")

        teaches = pd.read_csv("teaches.csv")
        likes = pd.read_csv("likes.csv")
        attends = pd.read_csv("attends.csv")

        teaches.to_sql('teaches', engine, index=False, if_exists='replace')
        likes.to_sql('likes', engine, index=False, if_exists='replace')
        attends.to_sql('attends', engine, index=False, if_exists='replace')
        return "✅"
    except Exception as e:
        return f"❌ {e}"

@app.get("/query")
def query():
    q = 'SELECT * FROM teaches NATURAL JOIN attends NATURAL JOIN likes'
    conn = None
    try:
        conn = psycopg2.connect(
            dbname="mydb",
            user="postgres",
            password="postgres",
            host="postgres",
            port=5432
        )
        df = pd.read_sql_query(q, conn)
        return HTMLResponse(content=f'{df}')
    except Exception as e:
        return f"❌ Failed to connect or create table: {e}"
    finally:
        if conn:
            conn.close()


