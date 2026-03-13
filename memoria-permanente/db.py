from pymongo import MongoClient
import os

from MongoChatMessageHistory import MongoChatMessageHistory

client = MongoClient(os.getenv("MONGODB_URL"))
db = client[os.getenv("MONGODB_DBNAME")]
collection = db["session_history"]

def get_session_history(session_id) -> MongoChatMessageHistory:
    # Função que retorna o histórico de uma sessão específica
    return MongoChatMessageHistory(session_id, collection)