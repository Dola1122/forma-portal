from django.shortcuts import render
from .firebase_utils import get_users_with_subcollections
from .firebase_utils import get_exercises, update_exercise, delete_exercise
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from firebase_admin import storage

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
            blob = storage.bucket().blob(blob_path)

            # Upload file
            blob.upload_from_file(image_file, content_type=image_file.content_type)

            # Make public (or use signed URL if you want restricted access)
            blob.make_public()
            public_url = blob.public_url

            # Update Firestore with new image URL
            db.collection("exerciseData").document(exercise_name).update({
                f"image_{image_type}": public_url
            })

            return JsonResponse({"success": True, "newImageUrl": public_url})
        except Exception as e:
            return JsonResponse({"success": False, "error": str(e)})
    return JsonResponse({"success": False, "error": "Invalid method"})