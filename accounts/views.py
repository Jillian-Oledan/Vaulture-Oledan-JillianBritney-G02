from django.contrib import messages
from django.shortcuts import render, redirect
from .forms import RegisterForm

from django.http import HttpResponse

def register_view(request):
    if request.user.is_authenticated:
        return redirect("dashboard_view")
    
    form = RegisterForm(request.POST or None)

    if request.method == "POST":
        if form.is_valid():
            form.save()
            messages.success(request, "Account created! Please log in.")
            return redirect("login_view")
        messages.error(request, "Please fix the errors below.")

    return render(request, "accounts/register.html", {"form": form})


def login_view(request):
    return HttpResponse("Login page")


def logout_view(request):
    return HttpResponse("Logout page")


def dashboard_view(request):
    return HttpResponse("Dashboard page")