from django.contrib.auth.models import User
from django.core.validators import RegexValidator
from django.db import models
from django.urls import reverse

RU_PHONE_VALIDATOR = RegexValidator(
    regex=r"^\+7 \(\d{3}\) \d{3}-\d{2}-\d{2}$",
    message="Телефон должен быть в формате +7 (XXX) XXX-XX-XX",
)


class Service(models.Model):
    title = models.CharField(max_length=255, verbose_name="Название")
    slug = models.SlugField(unique=True, verbose_name="Slug")
    short_description = models.TextField(
        verbose_name="Краткое описание", blank=True, default=""
    )
    full_description = models.TextField(verbose_name="Полное описание", blank=True, default="")
    photo = models.CharField(max_length=128, blank=True, default="", verbose_name="Фото")
    svg_icon = models.TextField(blank=True, default="", verbose_name="SVG иконка")
    order = models.PositiveIntegerField(default=0, verbose_name="Порядок")
    is_active = models.BooleanField(default=True, verbose_name="Активна")
    banner_title = models.CharField(max_length=255, blank=True, default="", verbose_name="Заголовок на баннере")
    banner_subtitle = models.CharField(max_length=255, blank=True, default="", verbose_name="Подзаголовок на баннере")
    banner_bg = models.CharField(max_length=255, blank=True, default="", verbose_name="Фон баннера (url или цвет)")
    content_blocks = models.JSONField(default=dict, blank=True, verbose_name="Блоки контента")

    class Meta:
        ordering = ["order", "title"]
        verbose_name = "Услуга"
        verbose_name_plural = "Услуги"

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse("service_detail", kwargs={"slug": self.slug})


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    phone = models.CharField(max_length=30, blank=True, verbose_name="Телефон")
    company = models.CharField(max_length=255, blank=True, verbose_name="Компания")

    class Meta:
        verbose_name = "Профиль пользователя"
        verbose_name_plural = "Профили пользователей"

    def __str__(self):
        return f"Профиль {self.user.username}"


class Lead(models.Model):
    LEAD_TYPE_CHOICES = [
        ("consultation", "Консультация / обратный звонок"),
        ("callback", "Обратный звонок"),
        ("calculation", "Расчёт стоимости СОУТ"),
        ("contact_form", "Форма контактов"),
        ("service", "Заявка с страницы услуги"),
    ]
    STATUS_CHOICES = [
        ("new", "Новая"),
        ("in_progress", "В работе"),
        ("done", "Обработана"),
    ]

    user = models.ForeignKey(
        User,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="leads",
        verbose_name="Пользователь",
    )
    service = models.ForeignKey(
        Service,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="leads",
        verbose_name="Услуга",
    )
    lead_type = models.CharField(
        max_length=32,
        choices=LEAD_TYPE_CHOICES,
        default="contact_form",
        verbose_name="Тип заявки",
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="new",
        verbose_name="Статус",
    )
    full_name = models.CharField(max_length=255, blank=True, default="", verbose_name="ФИО / имя")
    phone = models.CharField(
        max_length=32,
        verbose_name="Телефон",
        validators=[RU_PHONE_VALIDATOR],
    )
    email = models.EmailField(blank=True, default="", verbose_name="Email")
    message = models.TextField(blank=True, default="", verbose_name="Сообщение / комментарий")
    call_time = models.CharField(
        max_length=120,
        blank=True,
        default="",
        verbose_name="Удобное время звонка",
    )
    employees_count = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name="Количество сотрудников (СОУТ)",
    )
    workplaces_count = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name="Количество рабочих мест (СОУТ)",
    )
    enterprise_type = models.CharField(
        max_length=120,
        blank=True,
        default="",
        verbose_name="Тип предприятия (СОУТ)",
    )
    admin_comment = models.TextField(blank=True, default="", verbose_name="Комментарий администратора")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Создана")

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Лид (заявка)"
        verbose_name_plural = "Лиды (заявки)"

    def __str__(self):
        return f"{self.get_lead_type_display()}: {self.phone}"


class Category(models.Model):
    """Категория курсов (Охрана труда, Пожарная безопасность и т.д.)"""
    name = models.CharField(max_length=200, verbose_name="Название категории")
    slug = models.SlugField(unique=True, verbose_name="Slug", null=True)
    order = models.PositiveIntegerField(default=0, verbose_name="Порядок")
    is_active = models.BooleanField(default=True, verbose_name="Активна")
    
    class Meta:
        ordering = ["order", "name"]
        verbose_name = "Категория"
        verbose_name_plural = "Категории"
    
    def __str__(self):
        return self.name


class Course(models.Model):
    """Курс обучения"""
    category = models.ForeignKey(
        Category, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name="courses",
        verbose_name="Категория"
    )
    title = models.CharField(max_length=255, verbose_name="Название курса")
    slug = models.SlugField(unique=True, null=True, verbose_name="Slug")
    duration_hours = models.PositiveIntegerField(default=0, verbose_name="Длительность (часы)")
    description = models.TextField(verbose_name="Описание", blank=True, default="")
    short_description = models.CharField(max_length=500, verbose_name="Краткое описание", blank=True, default="")
    price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, verbose_name="Цена")
    is_active = models.BooleanField(default=True, verbose_name="Активен")
    order = models.PositiveIntegerField(default=0, verbose_name="Порядок")
    
    class Meta:
        ordering = ["order", "title"]
        verbose_name = "Курс"
        verbose_name_plural = "Курсы"
    
    def __str__(self):
        return self.title
    
    def get_absolute_url(self):
        return reverse("course_detail", kwargs={"slug": self.slug})