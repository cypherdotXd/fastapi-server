from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi


MONGO_URI = "mongodb+srv://ashkumar222222:QuQ9ymgox2gDKY3G@cluster0.ap7fnee.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"

# Create a new client and connect to the server
client = MongoClient(MONGO_URI, server_api=ServerApi('1'))
db = client.get_database("imagelabeller")
users_collection = db.get_collection("users")

# Send a ping to confirm a successful connection
try:
    client.admin.command('ping')
    print("Pinged your deployment. You successfully connected to MongoDB!")
except Exception as e:
    print(e)