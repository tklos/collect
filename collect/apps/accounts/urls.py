from django.contrib.auth.decorators import login_required
from django.urls import path

from . import views


app_name = 'account'
urlpatterns = [
    path('login/', views.LoginView.as_view(), name='login'),
    path('logout/', login_required(views.LogoutView.as_view()), name='logout'),
    path('register/', views.RegisterView.as_view(), name='register'),
]

