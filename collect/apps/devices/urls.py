from django.contrib.auth.decorators import login_required
from django.urls import path

from . import views


app_name = 'devices'
urlpatterns = [
    path('<int:d_sid>/', login_required(views.DeviceView.as_view()), name='device'),
    path('<int:d_sid>/delete-device/', login_required(views.DeviceDeleteDeviceView.as_view()), name='delete-device'),
    path('<int:d_sid>/add-run/', login_required(views.RunAddView.as_view()), name='add-run'),

    path('<int:d_sid>/pagination-unassigned-measurements/<int:page>/', login_required(views.PaginationUnassignedMeasurementsView.as_view()), name='pagination-unassigned-measurements'),
]

