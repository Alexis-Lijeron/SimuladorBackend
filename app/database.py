from pymongo import MongoClient

# Conexión a MongoDB
client = MongoClient('mongodb+srv://rapupena2909:Hola2020@ecommerce.t4bf6tt.mongodb.net/?retryWrites=true&w=majority&appName=ecommerce/')
db = client['simulador']
