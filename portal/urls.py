from django.urls import path
from . import views

urlpatterns = [
    path("users/", views.users_view, name="users"),
    path("exercises/", views.exercises_view, name="exercises_list"),
    path("exercises/<str:ex_id>/update_type/", views.update_exercise_type, name="update_exercise_type"),
    path("exercises/<str:ex_id>/update_video_url/", views.update_video_url, name="update_video_url"),
    path("exercises/<str:ex_id>/delete/", views.delete_exercise_view, name="delete_exercise"),

]
