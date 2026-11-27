import json
import os
from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from .crypto import derive_kek, unwrap_dek, encrypt_entry, decrypt_entry, generate_dek, wrap_dek
from .decorators import role_required
from .forms import RegisterForm, ProfileForm
from .models import User, VaultEntry

#--- Helpers ---

def _unlock(request):
    u, pw = request.user, request.session.get("master_password", "")
    if not pw:
        return None
    if not u.kdf_salt:
        salt = os.urandom(16)
        kek = derive_kek(pw, salt)
        dek = generate_dek()
        u.kdf_salt = salt.hex()
        u.master_key_check = wrap_dek(kek, dek)
        u.save(update_fields=["kdf_salt", "master_key_check"])
        return dek
    try:
        return unwrap_dek(derive_kek(pw, bytes.fromhex(u.kdf_salt)), u.master_key_check)
    except Exception:
        return None


def _decrypt(dek, entry):
    try:
        return json.loads(decrypt_entry(dek, entry.encrypted_data))
    except Exception:
        return None


def _user_meta(user):
    return {"kdf_salt": user.kdf_salt,
            "key_check": user.master_key_check.hex() if user.master_key_check else ""}


# --- Auth ---

def home(request):
    return redirect("dashboard" if request.user.is_authenticated else "login")


def register_view(request):
    if request.user.is_authenticated:
        return redirect("dashboard")
    form = RegisterForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Account created! Please log in.")
        return redirect("login")
    return render(request, "accounts/register.html", {"form": form})


def login_view(request):
    if request.user.is_authenticated:
        return redirect("dashboard")
    if request.method == "POST":
        ident = request.POST.get("identifier", "").strip()
        pw = request.POST.get("password", "")
        user = User.objects.filter(username=ident, role=User.ADMIN).first() \
            or User.objects.filter(email__iexact=ident, role=User.CUSTOMER).first()
        if user and user.is_active and user.check_password(pw):
            login(request, user)
            request.session["master_password"] = pw
            messages.success(request, f"Welcome, {user.username}!")
            return redirect(request.GET.get("next") or "dashboard")
        messages.error(request, "Invalid credentials.")
    return render(request, "accounts/login.html")


def logout_view(request):
    if request.method == "POST":
        request.session.pop("master_password", None)
        logout(request)
        messages.success(request, "You have been logged out.")
    return redirect("login")


# --- Dashboards ---

@login_required
def dashboard_redirect(request):
    return redirect("admin_dashboard" if request.user.role == User.ADMIN else "customer_dashboard")


@role_required("admin")
def admin_dashboard(request):
    users = User.objects.all()
    return render(request, "dashboards/admin.html", {
        "users": users,
        "total": users.count(),
        "admins": users.filter(role=User.ADMIN).count(),
        "customers": users.filter(role=User.CUSTOMER).count(),
    })


@role_required("customer")
def customer_dashboard(request):
    dek = _unlock(request)
    if dek is None:
        messages.error(request, "Session expired. Please log in again.")
        return redirect("login")

    entries = [{"entry": e, "data": d} for e in request.user.vault_entries.all()
               if (d := _decrypt(dek, e)) is not None]
    return render(request, "dashboards/customer.html", {"entries": entries})


# --- Entries ---

@role_required("customer")
def entry_form(request):
    dek = _unlock(request)
    if dek is None:
        return redirect("login")

    editing = None
    if request.GET.get("edit"):
        e = get_object_or_404(VaultEntry, pk=request.GET["edit"], user=request.user)
        if (data := _decrypt(dek, e)) is not None:
            editing = {"entry": e, "data": data}

    if request.method == "POST":
        p = request.POST
        blob = encrypt_entry(dek, json.dumps({k: p.get(k, "") for k in ("username", "password", "url", "notes")}))
        title = p.get("title", "").strip()[:100]
        etype = p.get("entry_type", "login")

        if editing:
            editing["entry"].title = title
            editing["entry"].entry_type = etype
            editing["entry"].encrypted_data = blob
            editing["entry"].save()
            messages.success(request, "Entry updated.")   
        else:
            VaultEntry.objects.create(user=request.user, title=title, entry_type=etype, encrypted_data=blob)
            messages.success(request, "Entry added.")
        return redirect("customer_dashboard")

    return render(request, "dashboards/entry_form.html", {"editing": editing})


@role_required("customer")
def entry_delete(request):
    if request.method == "POST":
        get_object_or_404(VaultEntry, pk=request.POST.get("id"), user=request.user).delete()
        messages.success(request, "Entry deleted.")
    return redirect("customer_dashboard")


@role_required("customer")
def entry_detail(request, pk):
    dek = _unlock(request)
    if dek is None:
        return redirect("login")

    e = get_object_or_404(VaultEntry, pk=pk, user=request.user)
    if (data := _decrypt(dek, e)) is None:
        messages.error(request, "Could not decrypt entry.")
        return redirect("customer_dashboard")
    return render(request, "dashboards/entry_detail.html", {"entry": e, "data": data})


# --- Profile ---

@login_required
def profile_view(request):
    return render(request, "accounts/profile.html", {"meta": _user_meta(request.user)})


@login_required
def profile_edit(request):
    form = ProfileForm(request.POST or None, request.FILES or None, instance=request.user)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Profile updated.")
        return redirect("profile")
    return render(request, "accounts/profile_edit.html", {"form": form})


# --- Change credentials ---

@role_required("customer")
def change_master_key(request):
    if request.method == "POST":
        old, new, new2 = (request.POST.get(k, "") for k in ("old_password", "new_password", "new_password2"))
        if len(new) < 10:
            messages.error(request, "New password must be at least 10 characters.")
        elif new != new2:
            messages.error(request, "New passwords don't match.")
        else:
            try:
                request.user.change_master_key(old, new)
                request.user.set_password(new)
                request.user.save()
                request.session["master_password"] = new
                messages.success(request, "Password changed.")
            except Exception:
                messages.error(request, "Current password is incorrect.")
    return redirect("profile")


@role_required("customer")
def change_email(request):
    if request.method == "POST":
        email = request.POST.get("new_email", "").strip().lower()
        if not email or "@" not in email:
            messages.error(request, "Invalid email address.")
        elif User.objects.filter(email=email).exclude(pk=request.user.pk).exists():
            messages.error(request, "That email is already in use.")
        elif not request.user.verify_master_key(request.POST.get("password", "")):
            messages.error(request, "Incorrect password.")
        else:
            request.user.email = email
            request.user.save(update_fields=["email"])
            logout(request)
            messages.success(request, "Email changed. Please log in with your new email.")
    return redirect("login")   