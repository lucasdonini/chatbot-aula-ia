from langchain_core.chat_history import BaseChatMessageHistory
from langchain_core.messages import messages_from_dict, messages_to_dict
from pymongo.collection import Collection


class MongoChatMessageHistory(BaseChatMessageHistory):
    def __init__(self, session_id: str, collection: Collection):
        self.session_id = session_id
        self.collection = collection
        self._load()

    def _load(self):
        doc = self.collection.find_one({"session_id": self.session_id})
        self._messages = messages_from_dict(
            doc["messages"]) if doc and "messages" in doc else []

    @property
    def messages(self):
        return self._messages

    def add_message(self, message):
        self._messages.append(message)
        self.collection.update_one(
            {"session_id": self.session_id},
            {"$set": {"messages": messages_to_dict(self._messages)}},
            upsert=True
        )

    def clear(self):
        self._messages = []
        self.collection.delete_one({"session_id": self.session_id})
