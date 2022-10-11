from django.contrib.auth.decorators import login_required
from django.urls import path

from . import views


app_name = 'profile'
urlpatterns = [
    path('', login_required(views.ProfileView.as_view()), name='home'),
]

