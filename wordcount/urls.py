from django.urls import path
from . import views

urlpatterns = [
    path('', views.keng, name = 'kengFirstPage' ),
    path('countPage/',views.count, name = 'count'),
    path('about/',views.about, name = 'about'),
    path('table/',views.table, name = 'table'),
    path('table1/',views.table1, name = 'table1')
]
