from django.urls import path

from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("services/", views.services_list, name="services"),
    path("about/", views.about, name="about"),
    path("contacts/", views.contacts, name="contacts"),
    path("reviews/", views.reviews, name="reviews"),
    path("forms/callback/", views.create_lead_callback, name="lead_callback"),
    path("forms/consultation/", views.create_lead_consultation, name="lead_consultation"),
    path("forms/calculation/", views.create_lead_calculation, name="lead_calculation"),
    path("register/", views.register_view, name="register"),
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_confirm, name="logout"),
    path("profile/", views.profile, name="profile"),
    path("custom_404/", views.custom_404, name="custom_404"),
    path('services/sout/', views.service_sout, name='service_sout'),
    path('services/risk-assessment/', views.service_risk, name='service_risk'),
    path('services/production-control/', views.service_production, name='service_production'),
    path('services/distance-learning/', views.service_learning, name='service_learning'),
    path('services/printed-products/', views.service_printed, name='service_printed'),
    path('services/<slug:slug>/', views.service_detail, name='service_detail'),
]
