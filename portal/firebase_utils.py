from firebase_admin import firestore

db = firestore.client()

def get_users_with_subcollections():
    users_ref = db.collection("users").stream()
    users = []
    for doc in users_ref:
        user_data = doc.to_dict()
        user_data["id"] = doc.id

        # 🔹 Get routines subcollection
        routines_ref = db.collection("users").document(doc.id).collection("routines").stream()
        user_data["routines"] = [{**r.to_dict(), "id": r.id} for r in routines_ref]

        # 🔹 Get routines_progress subcollection
        progress_ref = db.collection("users").document(doc.id).collection("routines_progress").stream()
        user_data["routines_progress"] = [{**p.to_dict(), "id": p.id} for p in progress_ref]

        users.append(user_data)
    return users

def get_exercises():
    docs = db.collection("exerciseData").stream()
    return [{**doc.to_dict(), "id": doc.id} for doc in docs]

def update_exercise(ex_id, data):
    db.collection("exerciseData").document(ex_id).update(data)

def delete_exercise(ex_id):
    db.collection("exerciseData").document(ex_id).delete()