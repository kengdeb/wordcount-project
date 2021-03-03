from django.urls import path
from . import views

urlpatterns = [
    path('', views.keng, name = 'kengFirstPage' ),
    path('countPage/',views.count, name = 'count'),
    path('about/',views.about, name = 'about')
]
