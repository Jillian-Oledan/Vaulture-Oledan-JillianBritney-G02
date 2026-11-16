from django.urls import path
from . import views
urlpatterns = [
    path("register/", views.register_view, name="register"),
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("dashboard/", views.dashboard_redirect, name="dashboard"),
    path("dashboard/admin/", views.admin_dashboard, name="admin_dashboard"),
    path("dashboard/customer/", views.customer_dashboard, name="customer_dashboard"),
    path("profile/", views.profile_view, name="profile"),
    path("profile/edit/", views.profile_edit, name="profile_edit"), 
    path("", views.home, name="home"),

    path("vault/setup/", views.vault_setup, name="vault_setup"),
    path("vault/entries/", views.vault_entries, name="vault_entries"),
    path("vault/entries/<int:pk>/", views.vault_entry_detail, name="vault_entry_detail"),
]