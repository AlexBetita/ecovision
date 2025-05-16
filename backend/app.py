# app.py - EcoVision: Climate Visualizer API
import os

from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional, Dict, List, Any
from dotenv import load_dotenv

from db import database, create_schema, seed_data_from_file, drop_tables

load_dotenv() 

# Database connection
DATABASE_URL = f"mysql://{os.environ.get('MYSQL_USER', 'root')}:{os.environ.get('MYSQL_PASSWORD', '')}@{os.environ.get('MYSQL_HOST', 'localhost')}/{os.environ.get('MYSQL_DB', 'climate_data')}"

app = FastAPI(title="EcoVision API")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup():
    await database.connect()
    # await drop_tables()
    await create_schema()
    await seed_data_from_file()
    

@app.on_event("shutdown")
async def shutdown():
    await database.disconnect()