from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404, redirect, render
from django.conf import settings

from .forms import (
    EmailOrUsernameAuthenticationForm,
    LeadCalculationForm,
    LeadCallbackForm,
    LeadConsultationForm,
    LeadContactForm,
    LeadServiceForm,
    RegisterForm,
    UserProfileForm,
)
from .models import *
from .utils import redirect_same_page


def home(request):
    services = Service.objects.filter(is_active=True)[:5]
    callback_form = LeadCallbackForm()
    calc_form = LeadCalculationForm()
    return render(
        request,
        "home.html",
        {
            "services": services,
            "callback_form": callback_form,
            "calc_form": calc_form,
        },
    )


def services_list(request):
    services = Service.objects.filter(is_active=True).order_by("order")
    return render(request, "services/list.html", {"services": services})


def service_detail(request, slug):
    service = get_object_or_404(Service, slug=slug, is_active=True)
    
    # Перенаправляем на конкретные страницы для известных услуг
    if slug == "sout":
        return redirect("service_sout")
    elif slug == "risk-assessment":
        return redirect("service_risk")
    elif slug == "production-control":
        return redirect("service_production")
    elif slug == "distance-learning":
        return redirect("service_learning")
    elif slug == "printed-products":
        return redirect("service_printed")
    
    # Для остальных услуг (если будут) — общий шаблон
    form = LeadServiceForm()
    courses = None
    selected_category = request.GET.get("category", "")
    categories = Course.CATEGORY_CHOICES if hasattr(Course, 'CATEGORY_CHOICES') else []
    
    if service.slug == "labor-training":
        courses = Course.objects.filter(is_active=True)
        if selected_category:
            courses = courses.filter(category=selected_category)
    
    if request.method == "POST":
        form = LeadServiceForm(request.POST)
        if form.is_valid():
            item = form.save(commit=False)
            item.lead_type = "service"
            item.service = service
            item.status = "new"
            if request.user.is_authenticated:
                item.user = request.user
            item.save()
            messages.success(request, "Заявка отправлена")
            return redirect_same_page(request, "service_detail", slug=slug)
    
    other_services = Service.objects.filter(is_active=True).exclude(pk=service.pk)[:4]
    
    return render(
        request,
        "services/detail.html",
        {
            "service": service,
            "form": form,
            "other_services": other_services,
            "courses": courses,
            "categories": categories,
            "selected_category": selected_category,
        },
    )

def about(request):
    services = Service.objects.filter(is_active=True).order_by('order')
    return render(request, 'about.html', {'services': services})


def contacts(request):
    services = Service.objects.filter(is_active=True).order_by('order')
    form = LeadContactForm()
    
    if request.method == "POST":
        form = LeadContactForm(request.POST)
        if form.is_valid():
            Lead.objects.create(
                lead_type="contact_form",
                full_name=form.cleaned_data["full_name"],
                phone=form.cleaned_data["phone"],
                email=form.cleaned_data["email"],
                message=form.cleaned_data.get("message") or "",
                user=request.user if request.user.is_authenticated else None,
            )
            messages.success(request, "Заявка отправлена")
            return redirect_same_page(request, "contacts")
    
    # context должен быть здесь, после обработки POST, но до render
    context = {
        'form': form,
        'services': services,
        'yandex_maps_api_key': settings.YANDEX_MAPS_API_KEY,  # если используете карту
    }
    
    return render(request, "contacts.html", context)


def reviews(request):
    return render(request, "reviews.html")


def create_lead_consultation(request):
    if request.method != "POST":
        return redirect("home")
    form = LeadConsultationForm(request.POST)
    if form.is_valid():
        Lead.objects.create(
            lead_type="consultation",
            full_name=form.cleaned_data["name"],
            phone=form.cleaned_data["phone"],
            user=request.user if request.user.is_authenticated else None,
        )
        messages.success(request, "Заявка отправлена")
    else:
        messages.error(request, "Проверьте корректность полей.")
    return redirect_same_page(request, "home")


def create_lead_callback(request):
    if request.method != "POST":
        return redirect("home")
    form = LeadCallbackForm(request.POST)
    if form.is_valid():
        Lead.objects.create(
            lead_type="callback",
            phone=form.cleaned_data["phone"],
            full_name="",
            user=request.user if request.user.is_authenticated else None,
        )
        messages.success(request, "Заявка отправлена")
    else:
        messages.error(request, "Проверьте корректность полей.")
    return redirect_same_page(request, "home")


def create_lead_calculation(request):
    if request.method != "POST":
        return redirect("home")
    form = LeadCalculationForm(request.POST)
    if form.is_valid():
        Lead.objects.create(
            lead_type="calculation",
            employees_count=form.cleaned_data["employees_count"],
            workplaces_count=form.cleaned_data["workplaces_count"],
            enterprise_type=form.cleaned_data["enterprise_type"],
            message="Заявка на расчёт стоимости СОУТ",
            user=request.user if request.user.is_authenticated else None,
        )
        messages.success(request, "Заявка отправлена")
    else:
        messages.error(request, "Проверьте корректность полей.")
    return redirect_same_page(request, "home")


def login_view(request):
    form = EmailOrUsernameAuthenticationForm(request, data=request.POST or None)
    if request.method == "POST":
        login_value = request.POST.get("username", "").strip()
        password = request.POST.get("password", "")
        user_qs = User.objects.filter(email__iexact=login_value)
        username = user_qs.first().username if user_qs.exists() else login_value
        auth_form = EmailOrUsernameAuthenticationForm(
            request, data={"username": username, "password": password}
        )
        if auth_form.is_valid():
            login(request, auth_form.get_user())
            messages.success(request, "Вы успешно вошли в систему.")
            return redirect("profile")
        form = auth_form
    return render(request, "accounts/login.html", {
        "form": form, 
        "hide_global_sections": True,
        "hide_footer": True  # добавить
    })

def register_view(request):
    form = RegisterForm()
    if request.method == "POST":
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.email = form.cleaned_data["email"]
            user.first_name = form.cleaned_data["first_name"]
            user.save()
            UserProfile.objects.create(
                user=user,
                phone=form.cleaned_data.get("phone") or "",
            )
            login(request, user)
            messages.success(request, "Регистрация завершена.")
            return redirect("profile")
    return render(request, "accounts/register.html", {
        "form": form, 
        "hide_global_sections": True,
        "hide_footer": True  # добавить
    })


@login_required
def logout_confirm(request):
    if request.method == "POST":
        logout(request)
        messages.info(request, "Вы вышли из аккаунта.")
        return redirect("home")
    return render(request, "accounts/logout_confirm.html", {"hide_global_sections": True})


def is_admin(user):
    return user.is_staff or user.is_superuser

@login_required
def profile(request):
    profile_obj, _ = UserProfile.objects.get_or_create(user=request.user)
    form = UserProfileForm(instance=profile_obj, user=request.user)
    
    if request.method == "POST" and not request.POST.get("logout"):
        form = UserProfileForm(request.POST, instance=profile_obj, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Профиль обновлён.")
            return redirect("profile")
    
    # Обычные заявки пользователя
    calculations = Lead.objects.filter(user=request.user, lead_type="calculation").order_by("-created_at")
    consultations = Lead.objects.filter(
        user=request.user, lead_type__in=("consultation", "callback", "contact_form")
    ).order_by("-created_at")
    
    context = {
        'form': form,
        'calculations': calculations,
        'consultations': consultations,
        'hide_global_sections': True,
    }
    
    # Если админ — добавляем статистику и все заявки
    if request.user.is_staff or request.user.is_superuser:
        from django.db.models import Count
        from datetime import timedelta
        from django.utils import timezone
        
        today = timezone.now()
        week_ago = today - timedelta(days=7)
        
        all_leads = Lead.objects.all().order_by('-created_at')
        
        context.update({
            'is_admin': True,
            'all_leads': all_leads[:50],  # последние 50 заявок
            'total_leads': Lead.objects.count(),
            'new_leads': Lead.objects.filter(status='new').count(),
            'in_progress_leads': Lead.objects.filter(status='in_progress').count(),
            'done_leads': Lead.objects.filter(status='done').count(),
            'leads_this_week': Lead.objects.filter(created_at__gte=week_ago).count(),
            'leads_by_type': Lead.objects.values('lead_type').annotate(count=Count('id')),
        })
    
    return render(request, "accounts/profile.html", context)


def custom_404(request, exception):
    return render(request, "404.html", status=404)


from .models import Course
from .forms import SoutForm

def service_sout(request):
    form = SoutForm()  # используем новую форму
    other_services = Service.objects.filter(is_active=True).exclude(slug="sout")[:4]
    
    if request.method == "POST":
        form = SoutForm(request.POST)
        if form.is_valid():
            Lead.objects.create(
                lead_type="service",
                status="new",
                full_name=form.cleaned_data["full_name"],
                phone=form.cleaned_data["phone"],
                email=form.cleaned_data["email"],
                workplaces_count=form.cleaned_data["workplaces_count"],
                message=f"Местонахождение организации: {form.cleaned_data['location']}",
                user=request.user if request.user.is_authenticated else None,
            )
            messages.success(request, "Заявка на СОУТ отправлена")
            return redirect("service_sout")
    
    context = {
        "form": form,
        "other_services": other_services,
    }
    return render(request, "services/sout.html", context)

def service_risk(request):
    form = LeadServiceForm()
    other_services = Service.objects.filter(is_active=True).exclude(slug="risk-assessment")[:4]
    
    if request.method == "POST":
        form = LeadServiceForm(request.POST)
        if form.is_valid():
            item = form.save(commit=False)
            item.lead_type = "service"
            item.status = "new"
            if request.user.is_authenticated:
                item.user = request.user
            item.save()
            messages.success(request, "Заявка на оценку рисков отправлена")
            return redirect("service_risk")
    
    context = {
        "form": form,
        "other_services": other_services,
    }
    return render(request, "services/risk.html", context)

def service_production(request):
    form = LeadServiceForm()
    other_services = Service.objects.filter(is_active=True).exclude(slug="production-control")[:4]
    
    if request.method == "POST":
        form = LeadServiceForm(request.POST)
        if form.is_valid():
            item = form.save(commit=False)
            item.lead_type = "service"
            item.status = "new"
            if request.user.is_authenticated:
                item.user = request.user
            item.save()
            messages.success(request, "Заявка на производственный контроль отправлена")
            return redirect("service_production")
    
    context = {
        "form": form,
        "other_services": other_services,
    }
    return render(request, "services/production.html", context)

def service_learning(request):
    categories = Category.objects.filter(is_active=True).order_by('order')
    selected_category_slug = request.GET.get("category", "")
    
    courses = Course.objects.filter(is_active=True)
    if selected_category_slug:
        courses = courses.filter(category__slug=selected_category_slug)
    
    other_services = Service.objects.filter(is_active=True).exclude(slug="distance-learning")[:4]
    
    if request.method == "POST":
        full_name = request.POST.get('full_name', '')
        phone = request.POST.get('phone', '')
        email = request.POST.get('email', '')
        course_title = request.POST.get('course_title', '')
        
        Lead.objects.create(
            lead_type="service",
            full_name=full_name,
            phone=phone,
            email=email,
            message=f"Заявка на курс: {course_title}",
            status="new",
            user=request.user if request.user.is_authenticated else None,
        )
        messages.success(request, f"Заявка на курс '{course_title}' отправлена")
        return redirect("service_learning")
    
    context = {
        "courses": courses,
        "categories": categories,
        "selected_category_slug": selected_category_slug,
        "other_services": other_services,
    }
    return render(request, "services/learning.html", context)
    

def service_printed(request):
    form = LeadServiceForm()
    other_services = Service.objects.filter(is_active=True).exclude(slug="printed-products")[:4]
    
    if request.method == "POST":
        form = LeadServiceForm(request.POST)
        if form.is_valid():
            item = form.save(commit=False)
            item.lead_type = "service"
            item.status = "new"
            if request.user.is_authenticated:
                item.user = request.user
            item.save()
            messages.success(request, "Заявка на печатную продукцию отправлена")
            return redirect("service_printed")
    
    context = {
        "form": form,
        "other_services": other_services,
    }
    return render(request, "services/printed.html", context)