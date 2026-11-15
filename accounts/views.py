from django.contrib import messages
from django.shortcuts import render, redirect
from .forms import RegisterForm
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required   
from django.http import HttpResponse

from .decorators import role_required
from .models import User


def register_view(request):
    if request.user.is_authenticated:
        return redirect("dashboard")
    
    form = RegisterForm(request.POST or None)

    if request.method == "POST":
        if form.is_valid():
            form.save()
            messages.success(request, "Account created! Please log in.")
            return redirect("login_view")
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
    ctx = {"users": User.objects.all().order_by("-date_joined"),
           "total": User.objects.count()}
    return render(request, "dashboards/admin.html", ctx)


@role_required("customer")
def customer_dashboard(request):
    return render(request, "dashboards/customer.html")


def profile_view(request):
    return HttpResponse("Profile Page")