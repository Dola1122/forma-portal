from firebase_admin import firestore, storage
import uuid

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
    """
    Retrieves all exercises from the Firestore database with default values for missing fields
    """
    docs = db.collection("exerciseData").stream()
    exercises = []
    
    for doc in docs:
        # Get the document data and ensure id is included
        exercise_data = doc.to_dict()
        exercise_data["id"] = doc.id
        
        # Set default values for commonly used fields if they don't exist
        defaults = {
            "name_en": "",
            "name_ar": "",
            "category_en": "",
            "category_ar": "",
            "equipment_en": "",
            "equipment_ar": "",
            "force_en": "",
            "force_ar": "",
            "level_en": "",
            "level_ar": "",
            "mechanic_en": "",
            "mechanic_ar": "",
            "added_count": 0,
            "video_url": "",
            "type": "weight_reps",
            "primaryMuscles_en": [],
            "primaryMuscles_ar": [],
            "secondaryMuscles_en": [],
            "secondaryMuscles_ar": [],
            "instructions_en": [],
            "instructions_ar": [],
            "image_1": "",
            "image_2": ""
        }
        
        # Apply defaults for missing fields
        for key, default_value in defaults.items():
            if key not in exercise_data:
                exercise_data[key] = default_value
        
        exercises.append(exercise_data)
        
    return exercises

def update_exercise(ex_id, data):
    db.collection("exerciseData").document(ex_id).update(data)

def delete_exercise(ex_id):
    """
    Deletes an exercise from Firestore and its associated images from Storage.
    """
    try:
        # First try to delete the images from storage
        bucket = storage.bucket()
        
        # Delete image 1
        blob1 = bucket.blob(f"exercise_images/{ex_id}/1.jpg")
        try:
            blob1.delete()
        except Exception:
            # Image might not exist, continue
            pass
            
        # Delete image 2
        blob2 = bucket.blob(f"exercise_images/{ex_id}/2.jpg")
        try:
            blob2.delete()
        except Exception:
            # Image might not exist, continue
            pass
            
        # Delete the Firestore document
        db.collection("exerciseData").document(ex_id).delete()
        return True
    except Exception as e:
        print(f"Error deleting exercise: {str(e)}")
        return False

def create_exercise(name, exercise_type="weight_reps", video_url=""):
    """
    Creates a new exercise in Firestore.
    """
    exercise_id = name.lower().replace(" ", "_")
    
    # Check if id already exists
    existing = db.collection("exerciseData").document(exercise_id).get()
    if existing.exists:
        # Generate a unique id by appending a random string
        unique_suffix = uuid.uuid4().hex[:6]
        exercise_id = f"{exercise_id}_{unique_suffix}"
    
    exercise_data = {
        "name": name,
        "type": exercise_type,
        "video_url": video_url,
        "image_1": "",
        "image_2": ""
    }
    
    db.collection("exerciseData").document(exercise_id).set(exercise_data)
    return exercise_id