from django.urls import path
from .views import profile, profile_edit, signup

app_name = "users"
urlpatterns = [
    path("registro/", signup, name="signup"),
    path("perfil/", profile, name="profile"),
    path("perfil/personalizar/", profile_edit, name="profile-edit"),
]
