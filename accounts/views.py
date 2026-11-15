from django.contrib import messages
from django.shortcuts import render, redirect
from .forms import RegisterForm

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