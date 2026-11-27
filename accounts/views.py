import base64

from django.contrib import messages
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required   
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.http import require_POST, require_http_methods

from .forms import RegisterForm
from .forms import ProfileForm

from .decorators import role_required

from .models import User
from .models import User, VaultEntry

import json


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
        messages.error(request, "Please input the necessary details.")

    return render(request, "accounts/register.html", {"form": form})



def login_view(request):
    if request.user.is_authenticated:
        return redirect("dashboard")

    if request.method == "POST":
        identifier = request.POST.get("identifier", "").strip()
        password = request.POST.get("password", "")

        user = User.objects.filter(username=identifier).first()
        if user is None:
            user = User.objects.filter(email=identifier.lower()).first()

        if user:
            if user.role == User.ADMIN:
                if user.username != identifier:
                    user = None
            else:
                if user.email.lower() != identifier.lower():
                    user = None

        if user and user.check_password(password) and user.is_active:
            login(request, user)
            messages.success(request, f"Welcome back, {user.first_name or user.username}!")
            return redirect(request.GET.get("next") or "dashboard")

        messages.error(request, "Invalid credentials.")

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
    user = request.user
    meta = {
        "kdf_salt": user.kdf_salt,
        "key_check": base64.b64encode(user.master_key_check).decode() if user.master_key_check else None,
    }
    return render(request, "dashboards/customer.html", {"meta": meta})



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



def _body(request):
    try:
        return json.loads(request.body)
    except ValueError:
        return {}



def _clean(d):
    title = str(d.get("title", "")).strip()[:100]
    etype, blob = d.get("entry_type"), d.get("encrypted_data")

    if not title or etype not in ("login", "note") or not isinstance(blob, str) or not blob:
        return None
    return title, etype, base64.b64decode(blob)



def _ser(e):
    return {
        "id": e.id,
        "title": e.title,
        "entry_type": e.entry_type,
        "encrypted_data": base64.b64encode(e.encrypted_data).decode(),  # ← was raw memoryview
    }



@role_required("customer")
@require_POST
def vault_setup(request):
    if request.user.kdf_salt:
        return JsonResponse({"error": "Master key is already set."}, status=400)
    
    d = _body(request)
    salt, check = d.get("kdf_salt"), d.get("master_key_check")

    if not isinstance(salt, str) or not isinstance(check, str) or not salt or not check:
        return JsonResponse({"error": "Invalid data."}, status=400)
    
    request.user.kdf_salt = salt[:64]
    request.user.master_key_check = base64.b64decode(check)  # ← decode before storing
    request.user.save(update_fields=["kdf_salt", "master_key_check"])
    return JsonResponse({"ok": True})



@role_required("customer")
@require_http_methods(["GET", "POST"])
def vault_entries(request):
    if request.method == "GET":
        return JsonResponse([_ser(e) for e in request.user.vault_entries.all()], safe=False)
    
    c = _clean(_body(request))
    if not c:
        return JsonResponse({"error": "Invalid entry."}, status=400)
    e = VaultEntry.objects.create(user=request.user, title=c[0], entry_type=c[1], encrypted_data=c[2])
    return JsonResponse(_ser(e), status=201)



@role_required("customer")
@require_http_methods(["PUT", "DELETE"])
def vault_entry_detail(request, pk):
    e = get_object_or_404(VaultEntry, pk=pk, user=request.user)
    if request.method == "DELETE":
        e.delete()
        return JsonResponse({"ok": True})

    c = _clean(_body(request))
    if not c:
        return JsonResponse({"error": "Invalid entry."}, status=400)
    e.title, e.entry_type, e.encrypted_data = c
    e.save()
    return JsonResponse(_ser(e))