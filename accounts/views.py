# accounts/views.py
from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import (
    login_required,
    user_passes_test,
    permission_required,
)
from django.core.cache import cache
from django.core.paginator import Paginator
from django.core.exceptions import PermissionDenied
from django.db import transaction, IntegrityError
from django.db.models import Q
from django.shortcuts import render, redirect, get_object_or_404

from .forms import LoginDNIForm, PropiedadForm, PropiedadImagenFormSet
from propiedades.models import Propiedad


# =========================
# Helpers de acceso
# =========================
def staff_required(view):
    """Requiere usuario autenticado y is_staff=True."""
    return login_required(user_passes_test(lambda u: u.is_staff, login_url="login")(view))


def require_any_group(user, names=("AdministradorCliente",)):
    """
    Exige que el usuario pertenezca al menos a uno de los grupos en 'names'.
    Por defecto permite el grupo 'AdministradorCliente'.
    """
    if not user.groups.filter(name__in=names).exists():
        raise PermissionDenied


# =========================
# Login / Logout
# =========================
def login_view(request):
    """
    Login para STAFF.
    - Usuario o DNI + contraseña.
    - Rate-limit: 5 intentos / 15min por IP+identificador.
    - Si valida -> redirige al listado de propiedades.
    """
    form = LoginDNIForm(request.POST or None)
    if request.method == "POST":
        ident = (request.POST.get("usuario_o_dni") or "").strip()
        ip = request.META.get("REMOTE_ADDR", "")
        key = f"login_attempts:{ip}:{ident}"
        attempts = cache.get(key, 0)

        if attempts >= 5:
            messages.error(request, "Demasiados intentos. Probá en 15 minutos.")
        else:
            if form.is_valid():
                user = form.cleaned_data["user"]  # ya verifica is_active + is_staff
                login(request, user)
                cache.delete(key)
                nxt = request.GET.get("next")
                return redirect(nxt or "panel_propiedades_list")
            else:
                cache.set(key, attempts + 1, 15 * 60)  # 15 minutos
                messages.error(request, "Credenciales inválidas.")

    return render(request, "accounts/login.html", {"form": form})


def logout_view(request):
    logout(request)
    return redirect("login")


# =========================
# Panel (home, opcional)
# =========================
@staff_required
def panel_home(request):
    # Si querés, también podés exigir grupo acá:
    # require_any_group(request.user, ("AdministradorCliente",))
    return render(request, "accounts/panel/home_panel.html")


# =========================
# Gestión de Propiedades
# =========================
@staff_required
@permission_required("propiedades.view_propiedad", raise_exception=True)
def panel_propiedades_list(request):
    # Gate por grupo (cliente admin)
    require_any_group(request.user, ("AdministradorCliente",))

    qs = Propiedad.objects.all().order_by("-creado")

    q = request.GET.get("q") or ""
    estado = request.GET.get("estado") or ""
    localidad = request.GET.get("localidad") or ""

    if q:
        qs = qs.filter(
            Q(titulo__icontains=q)
            | Q(descripcion__icontains=q)
            | Q(direccion__icontains=q)
            | Q(localidad__icontains=q)
            | Q(provincia__icontains=q)
            | Q(pais__icontains=q)
            | Q(codigo__icontains=q)
        )
    if estado:
        qs = qs.filter(estado=estado)
    if localidad:
        qs = qs.filter(localidad__icontains=localidad)

    page_obj = Paginator(qs, 20).get_page(request.GET.get("page"))
    ctx = {"page_obj": page_obj, "q": q, "estado": estado, "localidad": localidad}
    return render(request, "accounts/panel/propiedades_list.html", ctx)


# -------------------------
# Utilidad: tope de imágenes
# -------------------------
def _validar_max_imagenes(formset, instancia_propiedad, max_total=20):
    existentes_no_borradas = 0
    for f in formset.forms:
        if f.instance.pk and not f.cleaned_data.get("DELETE"):
            existentes_no_borradas += 1

    nuevas = 0
    for f in formset.forms:
        if not f.instance.pk and f.cleaned_data.get("imagen"):
            nuevas += 1

    total = existentes_no_borradas + nuevas
    if total > max_total:
        return False, f"Máximo {max_total} imágenes en la galería. Intentaste guardar {total}."
    return True, None


@staff_required
@permission_required("propiedades.add_propiedad", raise_exception=True)
@transaction.atomic
def panel_propiedad_crear(request):
    require_any_group(request.user, ("AdministradorCliente",))

    prop = Propiedad()
    if request.method == "POST":
        form = PropiedadForm(request.POST, request.FILES, instance=prop)
        formset = PropiedadImagenFormSet(request.POST, request.FILES, instance=prop)
        if form.is_valid() and formset.is_valid():
            ok, err = _validar_max_imagenes(formset, prop, max_total=20)
            if not ok:
                messages.error(request, err)
            else:
                try:
                    form.save()
                    formset.save()
                    messages.success(request, "Propiedad creada correctamente.")
                    return redirect("panel_propiedades_list")
                except IntegrityError:
                    messages.error(request, "Error de integridad al guardar. Verificá los datos.")
        else:
            messages.error(request, "Revisá los errores del formulario.")
    else:
        form = PropiedadForm(instance=prop)
        formset = PropiedadImagenFormSet(instance=prop)

    return render(
        request,
        "accounts/panel/propiedad_form.html",
        {"form": form, "formset": formset, "modo": "crear"},
    )


@staff_required
@permission_required("propiedades.change_propiedad", raise_exception=True)
@transaction.atomic
def panel_propiedad_editar(request, pk):
    require_any_group(request.user, ("AdministradorCliente",))

    prop = get_object_or_404(Propiedad, pk=pk)
    if request.method == "POST":
        form = PropiedadForm(request.POST, request.FILES, instance=prop)
        formset = PropiedadImagenFormSet(request.POST, request.FILES, instance=prop)
        if form.is_valid() and formset.is_valid():
            ok, err = _validar_max_imagenes(formset, prop, max_total=20)
            if not ok:
                messages.error(request, err)
            else:
                try:
                    form.save()
                    formset.save()
                    messages.success(request, "Propiedad actualizada.")
                    return redirect("panel_propiedades_list")
                except IntegrityError:
                    messages.error(request, "Error de integridad al guardar. Verificá los datos.")
        else:
            messages.error(request, "Revisá los errores del formulario.")
    else:
        form = PropiedadForm(instance=prop)
        formset = PropiedadImagenFormSet(instance=prop)

    return render(
        request,
        "accounts/panel/propiedad_form.html",
        {"form": form, "formset": formset, "modo": "editar", "prop": prop},
    )


@staff_required
@permission_required("propiedades.change_propiedad", raise_exception=True)
def panel_propiedad_pausar(request, pk):
    require_any_group(request.user, ("AdministradorCliente",))
    prop = get_object_or_404(Propiedad, pk=pk)
    prop.estado = "pausada"
    prop.save(update_fields=["estado"])
    messages.info(request, f"{prop.codigo} pausada.")
    return redirect("panel_propiedades_list")


@staff_required
@permission_required("propiedades.change_propiedad", raise_exception=True)
def panel_propiedad_activar(request, pk):
    require_any_group(request.user, ("AdministradorCliente",))
    prop = get_object_or_404(Propiedad, pk=pk)
    prop.estado = "activa"
    prop.save(update_fields=["estado"])
    messages.success(request, f"{prop.codigo} activada.")
    return redirect("panel_propiedades_list")


@staff_required
@permission_required("propiedades.change_propiedad", raise_exception=True)
def panel_propiedad_finalizar(request, pk):
    require_any_group(request.user, ("AdministradorCliente","))
    prop = get_object_or_404(Propiedad, pk=pk)
    prop.estado = "finalizada"
    prop.save(update_fields=["estado"])
    messages.warning(request, f"{prop.codigo} finalizada.")
    return redirect("panel_propiedades_list")