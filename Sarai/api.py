"""django-ninja API root.

Routers from local apps are registered here, e.g.:

    from myapp.api import router as myapp_router
    api.add_router("/myapp/", myapp_router)
"""

from ninja import NinjaAPI

api = NinjaAPI(title="Sarai API", version="0.1.0", urls_namespace="ninja")


@api.get("/health", auth=None)
def health(request):
    return {"status": "ok"}
