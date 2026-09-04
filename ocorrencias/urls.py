from django.urls import path
from .views import home_view, api_ocorrencias_mapa

urlpatterns = [
    path("", home_view, name="home"),
    path("api/mapa/", api_ocorrencias_mapa, name="api_mapa"),
]