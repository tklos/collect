from django.contrib import admin
from django.urls import include, path
from django.views.generic import RedirectView


urlpatterns = [
    path('', RedirectView.as_view(pattern_name='profile:home'), name='index'),

    path('account/', include('accounts.urls')),
    path('profile/', include('profiles.urls')),
    path('devices/', include('devices.urls')),
    path('runs/', include('runs.urls')),
    path('measurements/', include('measurements.urls')),

    path('api/measurements/', include('measurements.api.urls')),

    path('django-admin/', admin.site.urls),
]

