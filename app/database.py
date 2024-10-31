import os
from pymongo import MongoClient
from dotenv import load_dotenv
# Conexión a MongoDB
client = MongoClient(os.getenv('MONGODB_URI'))
db = client['simulador']
