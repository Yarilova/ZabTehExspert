import csv
import json
from datetime import datetime, time, timedelta
from io import BytesIO

from django.contrib import admin
from django.db.models import Count
from django.db.models.functions import TruncDate
from django.http import HttpResponse
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from .models import *

try:
    from openpyxl import Workbook
except ImportError:
    Workbook = None


@admin.action(description="Экспорт в CSV")
def export_leads_csv(modeladmin, request, queryset):
    response = HttpResponse(content_type="text/csv; charset=utf-8-sig")
    response["Content-Disposition"] = 'attachment; filename="leads.csv"'
    writer = csv.writer(response)
    writer.writerow(
        [
            "id",
            "created_at",
            "lead_type",
            "status",
            "full_name",
            "phone",
            "email",
            "message",
            "employees_count",
            "workplaces_count",
            "enterprise_type",
            "admin_comment",
            "user",
            "service",
        ]
    )
    for obj in queryset.iterator():
        writer.writerow(
            [
                obj.pk,
                obj.created_at.isoformat(),
                obj.lead_type,
                obj.status,
                obj.full_name,
                obj.phone,
                obj.email,
                obj.message,
                obj.employees_count or "",
                obj.workplaces_count or "",
                obj.enterprise_type,
                obj.admin_comment,
                obj.user_id or "",
                obj.service_id or "",
            ]
        )
    return response


@admin.action(description="Экспорт в Excel (.xlsx)")
def export_leads_xlsx(modeladmin, request, queryset):
    if Workbook is None:
        modeladmin.message_user(request, "Для Excel установите пакет openpyxl.", level="error")
        return None
    wb = Workbook()
    ws = wb.active
    ws.title = "Leads"
    headers = [
        "id",
        "created_at",
        "lead_type",
        "status",
        "full_name",
        "phone",
        "email",
        "message",
        "employees_count",
        "workplaces_count",
        "enterprise_type",
        "admin_comment",
        "user_id",
        "service_id",
    ]
    ws.append(headers)
    for obj in queryset.iterator():
        ws.append(
            [
                obj.pk,
                obj.created_at.isoformat(),
                obj.lead_type,
                obj.status,
                obj.full_name,
                obj.phone,
                obj.email,
                obj.message,
                obj.employees_count,
                obj.workplaces_count,
                obj.enterprise_type,
                obj.admin_comment,
                obj.user_id,
                obj.service_id,
            ]
        )
    buf = BytesIO()
    wb.save(buf)
    buf.seek(0)
    response = HttpResponse(
        buf.getvalue(),
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
    response["Content-Disposition"] = 'attachment; filename="leads.xlsx"'
    return response


@admin.register(Lead)
class LeadAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "created_at",
        "lead_type",
        "status",
        "full_name",
        "phone",
        "email",
        "user",
    )
    list_display_links = ("id",)
    list_filter = ("lead_type", "status", "created_at")
    search_fields = ("full_name", "phone", "email", "message", "admin_comment")
    readonly_fields = ("created_at",)
    date_hierarchy = "created_at"
    list_editable = ("status",)
    actions = (export_leads_csv, export_leads_xlsx)
    fieldsets = (
        (None, {"fields": ("lead_type", "status", "user", "service", "created_at")}),
        ("Клиент", {"fields": ("full_name", "phone", "email", "message", "call_time")}),
        ("СОУТ", {"fields": ("employees_count", "workplaces_count", "enterprise_type")}),
        ("Администратор", {"fields": ("admin_comment",)}),
    )


@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ["title", "slug", "order", "is_active", "photo"]
    list_editable = ["order", "is_active"]
    prepopulated_fields = {"slug": ("title",)}
    search_fields = ["title", "short_description", "full_description"]


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "phone", "company")
    search_fields = ("user__username", "user__email", "phone", "company")


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ["name", "slug", "order", "is_active"]
    list_editable = ["order", "is_active"]
    prepopulated_fields = {"slug": ("name",)}
    search_fields = ["name"]

@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ["title", "category", "duration_hours", "is_active"]
    list_editable = ["is_active"]
    list_filter = ["category", "is_active"]
    prepopulated_fields = {"slug": ("title",)}
    search_fields = ["title", "description"]


def _build_lead_dashboard_extra_context():
    today = timezone.localdate()
    start = today - timedelta(days=13)
    labels = [(start + timedelta(days=i)).isoformat() for i in range(14)]
    counts_map = {k: 0 for k in labels}

    from django.conf import settings

    naive = datetime.combine(start, time.min)
    if settings.USE_TZ:
        start_dt = timezone.make_aware(naive)
    else:
        start_dt = naive
    for row in (
        Lead.objects.filter(created_at__gte=start_dt)
        .annotate(d=TruncDate("created_at"))
        .values("d")
        .annotate(c=Count("id"))
    ):
        if row["d"]:
            key = row["d"].isoformat()
            if key in counts_map:
                counts_map[key] = row["c"]

    by_type = {k: 0 for k, _ in Lead.LEAD_TYPE_CHOICES}
    for row in Lead.objects.values("lead_type").annotate(c=Count("id")):
        by_type[row["lead_type"]] = row["c"]

    day_vals = [counts_map[k] for k in labels]
    type_lbl = [x[1] for x in Lead.LEAD_TYPE_CHOICES]
    type_vals = [by_type.get(x[0], 0) for x in Lead.LEAD_TYPE_CHOICES]
    return {
        "lead_chart_by_day_labels_json": json.dumps(labels, ensure_ascii=False),
        "lead_chart_by_day_values_json": json.dumps(day_vals),
        "lead_chart_types_labels_json": json.dumps(type_lbl, ensure_ascii=False),
        "lead_chart_types_values_json": json.dumps(type_vals),
        "lead_stat_new": Lead.objects.filter(status="new").count(),
        "lead_stat_in_progress": Lead.objects.filter(status="in_progress").count(),
        "lead_stat_done": Lead.objects.filter(status="done").count(),
        "lead_stat_total": Lead.objects.count(),
        "recent_leads": Lead.objects.order_by("-created_at")[:10],
    }


def _patch_admin_index():
    from django.contrib import admin as dj_admin

    if getattr(dj_admin.site, "_lead_stats_patched", False):
        return
    _orig = dj_admin.site.index

    def index(request, extra_context=None):
        extra_context = extra_context or {}
        try:
            extra_context.update(_build_lead_dashboard_extra_context())
        except Exception:
            pass
        return _orig(request, extra_context)

    dj_admin.site.index = index
    dj_admin.site._lead_stats_patched = True


_patch_admin_index()
