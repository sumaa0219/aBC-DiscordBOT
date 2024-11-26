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
        result = {}
        for doc in docs:
            result[doc.id] = doc.to_dict()
        return result
    else:
        ref = db.collection(collection).document(document)
        doc = ref.get()
        if doc.exists:
            return doc.to_dict()
        else:
            return None


def writeDB(collection: str, document: str, field: json):
    ref = db.collection(collection).document(document)
    ref.set(field)


def writeDBDB(collection: str, field: json):
    ref = db.collection(collection)
    ref.add(field)


def deleteDB(collection: str, document: str):
    ref = db.collection(collection).document(document)
    ref.delete()
