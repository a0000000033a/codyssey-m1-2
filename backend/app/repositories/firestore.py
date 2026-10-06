from google.cloud.firestore_v1.base_query import FieldFilter


class FirestoreRepository:
    def __init__(self, client):
        self.client = client

    def get(self, collection, id):
        snapshot = self.client.collection(collection).document(id).get()
        return snapshot.to_dict() if snapshot.exists else None

    def put(self, collection, id, value):
        self.client.collection(collection).document(id).set(value)

    def delete(self, collection, id):
        self.client.collection(collection).document(id).delete()

    def list(self, collection, filters=None):
        query = self.client.collection(collection)
        for key, value in (filters or {}).items():
            query = query.where(filter=FieldFilter(key, "==", value))
        return [dict(snapshot.to_dict(), id=snapshot.id) for snapshot in query.stream()]

    def batch_put(self, collection, rows):
        for offset in range(0, len(rows), 400):
            batch = self.client.batch()
            for id, row in rows[offset:offset+400]:
                batch.set(self.client.collection(collection).document(id), row)
            batch.commit()

    def atomic(self, callback):
        from google.cloud import firestore
        client = self.client
        class TransactionView:
            def get(self, collection, id):
                snapshot = client.collection(collection).document(id).get(transaction=transaction)
                return snapshot.to_dict() if snapshot.exists else None

            def put(self, collection, id, value):
                transaction.set(client.collection(collection).document(id), value)

            def delete(self, collection, id):
                transaction.delete(client.collection(collection).document(id))

        transaction = client.transaction()
        @firestore.transactional
        def run(transaction):
            return callback(TransactionView())
        return run(transaction)
