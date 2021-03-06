from django.contrib.auth.decorators import login_required
from django.urls import path

from . import views


app_name = 'devices'
urlpatterns = [
    path('add/', login_required(views.DeviceAddView.as_view()), name='add'),
    path('<int:d_sid>/', login_required(views.DeviceView.as_view()), name='device'),
    path('<int:d_sid>/download/', login_required(views.DeviceDownloadDataView.as_view()), name='download'),
    path('<int:d_sid>/delete-data/', login_required(views.DeviceDeleteDataView.as_view()), name='delete-data'),
    path('<int:d_sid>/delete-all-data/', login_required(views.DeviceDeleteAllDataView.as_view()), name='delete-all-data'),
    path('<int:d_sid>/delete-device/', login_required(views.DeviceDeleteDeviceView.as_view()), name='delete-device'),
    path('<int:d_sid>/delete-measurement/<int:m_id>/', login_required(views.DeviceDeleteMeasurementView.as_view()), name='delete-measurement'),
    path('<int:d_sid>/get-initial-plot-data/', login_required(views.DevicePlotInitialDataView.as_view()), name='get-initial-plot-data'),
    path('<int:d_sid>/get-plot-data/', login_required(views.DevicePlotDataView.as_view()), name='get-plot-data'),
    path('<int:d_sid>/get-newest-plot-data/', login_required(views.DeviceNewestPlotDataView.as_view()), name='get-newest-plot-data'),

    path('<int:d_sid>/pagination-measurements/<int:page>/', login_required(views.PaginationMeasurementsView.as_view()), name='pagination-measurements'),
]

