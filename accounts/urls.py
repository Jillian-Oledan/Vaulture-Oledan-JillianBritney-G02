from django.urls import path
from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("register/", views.register_view, name="register"),
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),

    path("dashboard/", views.dashboard_redirect, name="dashboard"),
    path("dashboard/admin/", views.admin_dashboard, name="admin_dashboard"),
    path("dashboard/customer/", views.customer_dashboard, name="customer_dashboard"),
    path("dashboard/customer/add/", views.entry_form, name="entry_form"),
    path("dashboard/customer/entry/<int:pk>/", views.entry_detail, name="entry_detail"),
    path("dashboard/customer/delete/", views.entry_delete, name="entry_delete"),
    
    path("profile/", views.profile_view, name="profile"),
    path("profile/edit/", views.profile_edit, name="profile_edit"),
    path("profile/change-master-key/", views.change_master_key, name="change_master_key"),
    path("profile/change-email/", views.change_email, name="change_email"),
]   