from fastapi import FastAPI
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from llama_index.llms.ollama import Ollama

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/", response_class=HTMLResponse)
def get_chat_page():
    with open("static/index.html", "r") as file:
        return file.read()

@app.get("/chat/{message}")
def chat(message: str):
    llm = Ollama(model="gemma3:1b", request_timeout=240.0, base_url="ollama:11434")
    response = llm.complete(message, timeout=None)
    print(f"OKOKOKOK: {message} -> {response}")
    return response

# --------------------------------------------------------------------------

from typing import Union
import pandas as pd
from sqlalchemy import create_engine
import time
import psycopg2
import os

#app = FastAPI()

@app.get("/initialize")
def initialize():
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
            DROP TABLE IF EXISTS teaches;
            DROP TABLE IF EXISTS attends;
            DROP TABLE IF EXISTS likes;
            CREATE TABLE teaches (lecturer VARCHAR(50), course VARCHAR(50));
            CREATE TABLE attends (student VARCHAR(50), course VARCHAR(50));
            CREATE TABLE likes (student VARCHAR(50), lecturer VARCHAR(50));
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


