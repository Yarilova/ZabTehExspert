from django.conf import settings


def site_extras(request):
    return {
        "reviews_2gis_url": getattr(
            settings,
            "REVIEWS_2GIS_URL",
            "https://2gis.ru/chita/search/%D0%97%D0%B0%D0%B1%D0%A2%D0%B5%D1%85%D0%AD%D0%BA%D1%81%D0%BF%D0%B5%D1%80%D1%82",
        ),
    }
