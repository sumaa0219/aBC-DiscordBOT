import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore
import json

cred = credentials.Certificate("firebase-adminsdk.json")
firebase_admin.initialize_app(cred)

db = firestore.client()


def readDB(collection: str, document=None):
    if document is None:
        ref = db.collection(collection)
        docs = ref.stream()
        result = []
        for doc in docs:
            result.append(doc.to_dict())
        return result if result else None
    else:
        ref = db.collection(collection).document(document)
        doc = ref.get()
        if doc.exists:
            return doc.to_dict()
        else:
            return None
    # try:
    #     dict = {}
    #     for doc in ref.get():
    #         dict[doc.id] = doc.to_dict()
    #     print(dict)
    #     return dict
    # except TypeError as e:
    #     return None


def writeDB(collection: str, document: str, field: json):
    ref = db.collection(collection).document(document)
    ref.set(field)
