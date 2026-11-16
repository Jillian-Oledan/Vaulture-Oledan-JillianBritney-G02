from django.contrib import messages
from django.shortcuts import render, redirect
from .forms import RegisterForm
from .forms import ProfileForm
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required   
from django.http import HttpResponse

from .decorators import role_required
from .models import User


def home(request):
    if request.user.is_authenticated:
        return redirect("dashboard")
    return redirect("login")


def register_view(request):
    if request.user.is_authenticated:
        return redirect("dashboard")
    
    form = RegisterForm(request.POST or None)

    if request.method == "POST":
        if form.is_valid():
            form.save()
            messages.success(request, "Account created! Please log in.")
            return redirect("login")
        messages.error(request, "Please fix the errors below.")

    return render(request, "accounts/register.html", {"form": form})


def login_view(request):
    if request.user.is_authenticated:
        return redirect("dashboard")
    if request.method == "POST":
        user = authenticate(request,
                            username=request.POST.get("username"),
                            password=request.POST.get("password"))
        if user:
            login(request, user)
            messages.success(request, f"Welcome back, {user.first_name or user.username}!")
            return redirect(request.GET.get("next") or "dashboard")
        messages.error(request, "Invalid username or password.")
    return render(request, "accounts/login.html")


def logout_view(request):
    if request.method == "POST":
        logout(request)
        messages.success(request, "You have been logged out.")
    return redirect("login")

@login_required
def dashboard_redirect(request):
    target = "admin_dashboard" if request.user.role == "admin" else "customer_dashboard"
    return redirect(target)


@role_required("admin")
def admin_dashboard(request):
    users = User.objects.all()
    total = users.count()
    admins = users.filter(role='admin').count()
    customers = users.filter(role='customer').count()
    return render(request, "dashboards/admin.html", {
        "users": users,
        "total": total,
        "admins": admins,
        "customers": customers,
    })


@role_required("customer")
def customer_dashboard(request):
    return render(request, "dashboards/customer.html")


@login_required
def profile_view(request):
    return render(request, "accounts/profile.html")


@login_required
def profile_edit(request):
    form = ProfileForm(request.POST or None, request.FILES or None,
                       instance=request.user)
    if request.method == "POST":
        if form.is_valid():
            form.save()
            messages.success(request, "Profile updated.")
            return redirect("profile")
        messages.error(request, "Could not update profile.")
    return render(request, "accounts/profile_edit.html", {"form": form})