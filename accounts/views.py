from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.cache import never_cache
from .forms import LoginDNIForm

@never_cache
def login_view(request):
    if request.user.is_authenticated:
        return redirect("/admin/")  # panel base
    form = LoginDNIForm(request.POST or None)
    nxt = request.GET.get("next") or request.POST.get("next")
    if request.method == "POST" and form.is_valid():
        login(request, form.cleaned_data["user"])
        if nxt and url_has_allowed_host_and_scheme(nxt, {request.get_host()}):
            return redirect(nxt)
        return redirect("/admin/")
    # placeholder sin template
    if request.method != "POST":
        return render(request, "accounts/login.html", {"form": form, "next": nxt})
    return render(request, "accounts/login.html", {"form": form, "next": nxt})

def logout_view(request):
    logout(request)
    return redirect("login")
