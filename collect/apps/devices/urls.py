from django.contrib.auth.decorators import login_required
from django.urls import path

from . import views


app_name = 'devices'
urlpatterns = [
    path('add/', login_required(views.DeviceAddView.as_view()), name='add'),
    path('<int:d_sid>/', login_required(views.DeviceView.as_view()), name='device'),
    path('<int:d_sid>/get-initial-plot-data/', login_required(views.DevicePlotInitialDataView.as_view()), name='get-initial-plot-data'),
    path('<int:d_sid>/get-plot-data/', login_required(views.DevicePlotDataView.as_view()), name='get-plot-data'),
    path('<int:d_sid>/get-newest-plot-data/', login_required(views.DeviceNewestPlotDataView.as_view()), name='get-newest-plot-data'),

    path('<int:d_sid>/pagination-measurements/<int:page>/', login_required(views.PaginationMeasurementsView.as_view()), name='pagination-measurements'),
]

