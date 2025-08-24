# django_inmobiliaria/middleware.py
import os
import ipaddress
from django.http import HttpResponseForbidden
from django.urls import reverse
from django.conf import settings

def _parse_allowed(ips_raw: str):
    items = [i.strip() for i in ips_raw.split(",") if i.strip()]
    nets = []
    for item in items:
        try:
            # Soporta IP simple o CIDR (ej: 203.0.113.5 o 203.0.113.0/24)
            nets.append(ipaddress.ip_network(item, strict=False))
        except ValueError:
            pass
    return nets

def _client_ip(request):
    # Detrás de Cloudflare, éste es el real
    cf_ip = request.META.get("HTTP_CF_CONNECTING_IP")
    if cf_ip:
        return cf_ip
    # Proxy común
    xff = request.META.get("HTTP_X_FORWARDED_FOR")
    if xff:
        return xff.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR", "")

class IPAllowlistMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        self.enabled = getattr(settings, "IP_ALLOWLIST_ENABLED", False)
        self.scope = getattr(settings, "IP_ALLOWLIST_SCOPE", "admin")
        self.allowed_nets = _parse_allowed(getattr(settings, "ALLOWED_IPS", ""))

        # URL de admin (configurable por env), por si no está en /admin
        self.admin_prefix = "/" + (os.environ.get("DJANGO_ADMIN_URL", "admin/")).lstrip("/")

    def __call__(self, request):
        if not self.enabled:
            return self.get_response(request)

        path = request.path or "/"

        # Exceptuamos estáticos y media cuando el alcance es "all"
        if self.scope == "all" and (path.startswith("/static/") or path.startswith("/media/")):
            return self.get_response(request)

        # Determinar si debemos filtrar este path
        should_filter = (
            (self.scope == "admin" and path.startswith(self.admin_prefix))
            or (self.scope == "all")
        )
        if not should_filter:
            return self.get_response(request)

        ip = _client_ip(request)
        try:
            addr = ipaddress.ip_address(ip)
        except ValueError:
            # Si no se pudo parsear la IP, bloqueamos
            return HttpResponseForbidden("Forbidden (invalid IP)")

        for net in self.allowed_nets:
            if addr in net:
                return self.get_response(request)

        return HttpResponseForbidden("Forbidden (IP not allowed)")
