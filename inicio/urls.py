from django.urls import path
from django.views.generic import RedirectView
from . import views

urlpatterns = [
    # Redirige el favicon directamente a la ruta estática compilada
    path('favicon.ico', RedirectView.as_view(url='/static/inicio/images/icono-pag.png')),

    path('', views.login_view, name='login'),
    path('homePage/', views.homePage, name='homePage'),
    path('sala-computo/', views.sala_computo_view, name='sala_computo'),
    path('sala-computo/buscar-docente/', views.buscar_docente_sala_view, name='buscar_docente_sala'),
    path('sala-computo/catalogos-clase/', views.catalogos_clase_docente_view, name='catalogos_clase_docente'),
    path('sala-computo/buscar-ponente/', views.buscar_ponente_sala_view, name='buscar_ponente_sala'),
    path('agregar-usuario/', views.agregar_usuario_view, name='agregar_usuario'),
    path('auditoria-reportes/', views.auditoria_reportes_view, name='auditoria_reportes'),
    path('respaldos-bd/', views.respaldos_bd_view, name='respaldos_bd'),
    path('logout/', views.logout_view, name='logout'),
]