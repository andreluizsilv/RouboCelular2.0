# urls.py
from django.urls import path
from .views import (
    home_view,
    detalhe_ocorrencia_view,
    lista_ocorrencias,  # <--- Adicionado
    api_ocorrencias_mapa,
    api_kpis,
    api_graficos,
)

urlpatterns = [
    path("", home_view, name="home"),
    path("ocorrencias/", lista_ocorrencias, name="lista_ocorrencias"),
    path("ocorrencia/<int:pk>/", detalhe_ocorrencia_view, name="detalhe_ocorrencia"),  # <--- Removido o 's' final

    # API Endpoints
    path("api/mapa/", api_ocorrencias_mapa, name="api_mapa"),
    path("api/kpis/", api_kpis, name="api_kpis"),
    path("api/graficos/", api_graficos, name="api_graficos"),
]