from django.urls import path
from django.views.generic import RedirectView
from . import views

urlpatterns = [
    # Redirige el favicon directamente a la ruta estática compilada
    path('favicon.ico', RedirectView.as_view(url='/static/inicio/images/icono-pag.png')),

    path('', views.login_view, name='login'),
    path('homePage/', views.homePage, name='homePage'),
    path('agregar-usuario/', views.agregar_usuario_view, name='agregar_usuario'),
    path('exportar-auditoria/', views.exportar_auditoria_excel, name='exportar_auditoria'),
    # Ruta obligatoria para que el botón de cerrar sesión funcione
    path('logout/', views.logout_view, name='logout'),
]