from django.contrib.auth.decorators import login_required
from django.urls import path

from . import views


app_name = 'measurements'
urlpatterns = [
    path('<int:m_id>/delete/', login_required(views.MeasurementDeleteView.as_view()), name='delete'),
]
