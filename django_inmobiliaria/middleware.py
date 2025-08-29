# django_inmobiliaria/middleware.py
from django.http import HttpResponseForbidden
from django.conf import settings
import ipaddress

class IPAllowlistMiddleware:
    """
    Restringe por IP SOLO las rutas protegidas (p.ej. tu admin oculto).
    El resto del sitio (incluido /accounts/panel) queda libre.

    Env:
      IP_ALLOWLIST_ENABLED=1|0
      IP_ALLOWLIST_SCOPE=admin   # usar 'admin' para proteger solo prefijos configurados
      ALLOWED_IPS=186.57.154.224,2802:8010:6131:fe00:3dcf:c065:29ce:cce8

    Ajustá PROTECTED_PREFIXES para tu ruta real de admin.
    Detrás de Cloudflare toma la IP real de HTTP_CF_CONNECTING_IP.
    """
    # Cambiá el prefijo por el que uses realmente para tu admin oculto:
    PROTECTED_PREFIXES = ("/constructordemisitio/",)

    def __init__(self, get_response):
        self.get_response = get_response
        self.enabled = getattr(settings, "IP_ALLOWLIST_ENABLED", False)
        self.scope   = getattr(settings, "IP_ALLOWLIST_SCOPE", "admin")
        # parsea ALLOWED_IPS (IPv4/IPv6, coma separada)
        ips = getattr(settings, "ALLOWED_IPS", "") or ""
        self.allowed = []
        for raw in [x.strip() for x in ips.split(",") if x.strip()]:
            try:
                self.allowed.append(ipaddress.ip_network(raw, strict=False))
            except ValueError:
                # si no es red, intentá como IP individual
                try:
                    self.allowed.append(ipaddress.ip_network(raw + "/32", strict=False))
                except Exception:
                    pass

    def _client_ip(self, request):
        # Si estás detrás de Cloudflare:
        cf_ip = request.META.get("HTTP_CF_CONNECTING_IP")
        if cf_ip:
            return cf_ip.strip()
        # Si hay un proxy que setea X-Forwarded-For:
        xff = request.META.get("HTTP_X_FORWARDED_FOR")
        if xff:
            return xff.split(",")[0].strip()
        return (request.META.get("REMOTE_ADDR") or "").strip()

    def _is_allowed(self, ip_str):
        if not ip_str:
            return False
        try:
            ip_obj = ipaddress.ip_address(ip_str)
        except ValueError:
            return False
        if not self.allowed:
            return False
        return any(ip_obj in net for net in self.allowed)

    def __call__(self, request):
        if not self.enabled:
            return self.get_response(request)

        # Solo proteger admin oculto cuando scope == 'admin'
        if self.scope == "admin":
            if not request.path.startswith(self.PROTECTED_PREFIXES):
                # Todo lo que no sea admin-oculto queda libre
                return self.get_response(request)
        # Si quisieras bloquear TODO el sitio, pondrías scope != 'admin'

        ip = self._client_ip(request)
        if not self._is_allowed(ip):
            return HttpResponseForbidden("Forbidden (IP not allowed)")

        return self.get_response(request)
