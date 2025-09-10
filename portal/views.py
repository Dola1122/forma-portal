from django.shortcuts import render
from .firebase_utils import get_users_with_subcollections
from .firebase_utils import get_exercises, update_exercise, delete_exercise
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from firebase_admin import firestore, storage

db = firestore.client()

def users_view(request):
    users = get_users_with_subcollections()
    return render(request, "portal/users.html", {"users": users})

def exercises_view(request):
    exercises = get_exercises()
    return render(request, "portal/exercises.html", {"exercises": exercises})

def update_exercise_type(request, ex_id):
    if request.method == "POST":
        new_type = request.POST.get("exercise_type")
        update_exercise(ex_id, {"type": new_type})
        return JsonResponse({"success": True})
    return JsonResponse({"success": False})

def update_video_url(request, ex_id):
    if request.method == "POST":
        new_url = request.POST.get("video_url")
        update_exercise(ex_id, {"video_url": new_url})
        return JsonResponse({"success": True})
    return JsonResponse({"success": False})

def delete_exercise_view(request, ex_id):
    if request.method == "POST":
        delete_exercise(ex_id)
        return JsonResponse({"success": True})
    return JsonResponse({"success": False})

@csrf_exempt
def upload_exercise_image(request):
    if request.method == "POST":
        exercise_name = request.POST.get("exercise_name")
        image_type = request.POST.get("image_type")  # "1" or "2"
        image_file = request.FILES.get("image")

        if not exercise_name or not image_type or not image_file:
            return JsonResponse({"success": False, "error": "Missing fields"})

        try:
            # Path in Firebase Storage
            blob_path = f"exercise_images/{exercise_name}/{image_type}.jpg"
            bucket = storage.bucket()
            blob = bucket.blob(blob_path)

            # Read the file content
            image_content = image_file.read()
            
            # Upload file
            blob.upload_from_string(
                image_content, 
                content_type=image_file.content_type
            )

            # Make public (or use signed URL if you want restricted access)
            blob.make_public()
            public_url = blob.public_url

            # Update Firestore with new image URL
            field_name = f"image_{image_type}"
            db.collection("exerciseData").document(exercise_name).update({
                field_name: public_url
            })

            return JsonResponse({"success": True, "newImageUrl": public_url})
        except Exception as e:
            import traceback
            print(f"Error uploading image: {str(e)}")
            print(traceback.format_exc())
            return JsonResponse({"success": False, "error": str(e)})
            
    return JsonResponse({"success": False, "error": "Invalid method"})

@csrf_exempt
def create_exercise(request):
    """
    Creates a new exercise in the database with all fields
    """
    if request.method == "POST":
        try:
            import json
            if request.content_type == 'application/json':
                data = json.loads(request.body.decode('utf-8'))
            else:
                # Handle form data
                data = {
                    'id': request.POST.get("id", "").strip(),
                    'name_en': request.POST.get("name", "").strip(),
                    'type': request.POST.get("type", "weight_reps"),
                    'video_url': request.POST.get("video_url", "")
                }

            exercise_id = data.get('id')
            if not exercise_id:
                return JsonResponse({"success": False, "error": "Exercise ID is required"})
                
            # Store the exercise document
            db.collection("exerciseData").document(exercise_id).set(data)
            return JsonResponse({"success": True, "id": exercise_id})
        except Exception as e:
            import traceback
            print(f"Error creating exercise: {str(e)}")
            print(traceback.format_exc())
            return JsonResponse({"success": False, "error": str(e)})
            
    return JsonResponse({"success": False, "error": "Invalid method"})

@csrf_exempt
def update_field(request, ex_id):
    """
    Updates a single field in the exercise document
    """
    if request.method == "POST":
        try:
            import json
            if request.content_type == 'application/json':
                data = json.loads(request.body.decode('utf-8'))
                
                # Convert added_count to integer if it exists
                if 'added_count' in data:
                    try:
                        data['added_count'] = int(data['added_count'])
                    except (ValueError, TypeError):
                        data['added_count'] = 0
                
                update_exercise(ex_id, data)
                return JsonResponse({"success": True})
            else:
                # Handle form data
                field = next(iter(request.POST))
                value = request.POST.get(field)
                
                # Convert added_count to integer if needed
                if field == 'added_count':
                    try:
                        value = int(value)
                    except (ValueError, TypeError):
                        value = 0
                
                update_exercise(ex_id, {field: value})
                return JsonResponse({"success": True})
        except Exception as e:
            print(f"Error updating field: {str(e)}")
            return JsonResponse({"success": False, "error": str(e)})
    
    return JsonResponse({"success": False, "error": "Invalid method"})

@csrf_exempt
def update_array(request, ex_id):
    """
    Updates an array field in the exercise document (muscles, instructions)
    """
    if request.method == "POST":
        try:
            import json
            data = json.loads(request.body.decode('utf-8'))
            update_exercise(ex_id, data)
            return JsonResponse({"success": True})
        except Exception as e:
            print(f"Error updating array field: {str(e)}")
            return JsonResponse({"success": False, "error": str(e)})
    
    return JsonResponse({"success": False, "error": "Invalid method"})