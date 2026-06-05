from django.http import HttpResponseRedirect
from django.shortcuts import redirect
from django.utils.http import url_has_allowed_host_and_scheme


def redirect_same_page(request, fallback_url_name="home", **fallback_kwargs):
    ref = request.META.get("HTTP_REFERER")
    if ref and url_has_allowed_host_and_scheme(
        url=ref,
        allowed_hosts={request.get_host()},
        require_https=request.is_secure(),
    ):
        return HttpResponseRedirect(ref)
    if fallback_kwargs:
        return redirect(fallback_url_name, **fallback_kwargs)
    return redirect(fallback_url_name)
