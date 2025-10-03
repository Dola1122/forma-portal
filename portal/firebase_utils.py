from firebase_admin import firestore, storage
import uuid
from typing import Any, Dict, Iterable, List

db = firestore.client()


EXERCISE_FIELD_SPECS = {
    "id": {"type": "string", "default": ""},
    "name_en": {"type": "string", "default": ""},
    "name_ar": {"type": "string", "default": ""},
    "category_en": {"type": "string", "default": ""},
    "category_ar": {"type": "string", "default": ""},
    "equipment_en": {"type": "string", "default": ""},
    "equipment_ar": {"type": "string", "default": ""},
    "force_en": {"type": "string", "default": ""},
    "force_ar": {"type": "string", "default": ""},
    "level_en": {"type": "string", "default": ""},
    "level_ar": {"type": "string", "default": ""},
    "mechanic_en": {"type": "string", "default": ""},
    "mechanic_ar": {"type": "string", "default": ""},
    "video_url": {"type": "string", "default": ""},
    "type": {"type": "string", "default": "weight_reps"},
    "image_1": {"type": "string", "default": ""},
    "image_2": {"type": "string", "default": ""},
    "added_count": {"type": "int", "default": 0},
    "primaryMuscles_en": {"type": "array", "default_factory": list},
    "primaryMuscles_ar": {"type": "array", "default_factory": list},
    "secondaryMuscles_en": {"type": "array", "default_factory": list},
    "secondaryMuscles_ar": {"type": "array", "default_factory": list},
    "instructions_en": {"type": "array", "default_factory": list},
    "instructions_ar": {"type": "array", "default_factory": list},
}


def _coerce_string(value: Any) -> str:
    if value is None:
        return ""
    value_str = str(value)
    return value_str.strip()


def _coerce_int(value: Any) -> int:
    if value is None or value == "":
        return 0
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, int):
        return value
    try:
        return int(value)
    except (TypeError, ValueError):
        try:
            return int(float(value))
        except (TypeError, ValueError):
            return 0


def _ensure_iterable(value: Any) -> Iterable:
    if value is None:
        return []
    if isinstance(value, (list, tuple, set)):
        return value
    return [value]


def _coerce_array_of_strings(value: Any) -> List[str]:
    items = []
    for item in _ensure_iterable(value):
        if item is None:
            continue
        item_str = str(item).strip()
        if item_str:
            items.append(item_str)
    return items


def _default_value_for_field(field_spec: Dict[str, Any]) -> Any:
    if "default_factory" in field_spec:
        return field_spec["default_factory"]()
    default = field_spec.get("default")
    if isinstance(default, (list, dict, set)):
        return default.copy()
    return default


def sanitize_exercise_payload(payload: Dict[str, Any], *, apply_defaults: bool = False, include_unknown: bool = False) -> Dict[str, Any]:
    """Sanitize raw data destined for an exercise document to match expected Firestore types."""

    sanitized: Dict[str, Any] = {}
    processed_fields = set()

    for field, spec in EXERCISE_FIELD_SPECS.items():
        if field in payload:
            raw_value = payload[field]
            if spec["type"] == "string":
                sanitized[field] = _coerce_string(raw_value)
            elif spec["type"] == "int":
                sanitized[field] = _coerce_int(raw_value)
            elif spec["type"] == "array":
                sanitized[field] = _coerce_array_of_strings(raw_value)
            else:
                sanitized[field] = raw_value
            processed_fields.add(field)
        elif apply_defaults:
            sanitized[field] = _default_value_for_field(spec)

    if include_unknown:
        for field, value in payload.items():
            if field not in processed_fields and field not in sanitized:
                sanitized[field] = value

    return sanitized

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
        raw_data = doc.to_dict() or {}
        exercise_data = sanitize_exercise_payload(raw_data, apply_defaults=True, include_unknown=True)
        exercise_data["id"] = doc.id
        exercises.append(exercise_data)

    return exercises

def update_exercise(ex_id, data):
    sanitized = sanitize_exercise_payload(data, apply_defaults=False, include_unknown=False)
    sanitized.pop("id", None)

    if not sanitized:
        raise ValueError("No valid exercise fields provided for update")

    db.collection("exerciseData").document(ex_id).update(sanitized)

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
    
    exercise_data = sanitize_exercise_payload(
        {
            "id": exercise_id,
            "name_en": name,
            "type": exercise_type,
            "video_url": video_url,
        },
        apply_defaults=True,
        include_unknown=False,
    )

    # Ensure stored id matches document id
    exercise_data["id"] = exercise_id
    db.collection("exerciseData").document(exercise_id).set(exercise_data)
    return exercise_id