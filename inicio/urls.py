from django.urls import path
from . import views

urlpatterns = [
    path('', views.login_view, name='login'),
    path('homePage/', views.homePage, name='homePage'),
    path('agregar-usuario/', views.agregar_usuario_view, name='agregar_usuario'),
    path('exportar-auditoria/', views.exportar_auditoria_excel, name='exportar_auditoria'),
    # Ruta obligatoria para que el botón de cerrar sesión funcione
    path('logout/', views.logout_view, name='logout'),
]