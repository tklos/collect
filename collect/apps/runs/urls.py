from django.contrib.auth.decorators import login_required
from django.urls import path

from . import views


app_name = 'runs'
urlpatterns = [
    path('<int:r_id>/', login_required(views.RunView.as_view()), name='run'),
    path('<int:r_id>/finalise/', login_required(views.RunFinaliseView.as_view()), name='finalise'),
    path('<int:r_id>/trim/', login_required(views.RunTrimView.as_view()), name='trim'),
    path('<int:r_id>/download/', login_required(views.RunDownloadDataView.as_view()), name='download'),
    path('<int:r_id>/delete-run-detach-data/', login_required(views.RunDeleteRunDetachDataView.as_view()), name='delete-run-detach-data'),
    path('<int:r_id>/delete-run-and-data/', login_required(views.RunDeleteRunAndDataView.as_view()), name='delete-run-and-data'),
    path('<int:r_id>/get-newest-data/', login_required(views.RunNewestDataView.as_view()), name='get-newest-data'),
    path('<int:r_id>/get-new-xticks/', login_required(views.RunNewXticksView.as_view()), name='get-new-xticks'),

    path('<int:r_id>/pagination-measurements/<int:page>/', login_required(views.PaginationMeasurementsView.as_view()), name='pagination-measurements'),
]

