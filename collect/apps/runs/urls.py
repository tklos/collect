from django.contrib.auth.decorators import login_required
from django.urls import path

from . import views


app_name = 'runs'
urlpatterns = [
    path('<int:r_id>/', login_required(views.RunView.as_view()), name='run'),
    path('<int:r_id>/download/', login_required(views.RunDownloadDataView.as_view()), name='download'),
    path('<int:r_id>/delete-run/', login_required(views.RunDeleteRunView.as_view()), name='delete-run'),

    path('<int:r_id>/pagination-measurements/<int:page>/', login_required(views.PaginationMeasurementsView.as_view()), name='pagination-measurements'),
]

