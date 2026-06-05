import re

from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError

from .models import Lead, UserProfile

RU_PHONE_RE = re.compile(r"^\+7 \(\d{3}\) \d{3}-\d{2}-\d{2}$")


def normalize_phone(value: str) -> str:
    digits = re.sub(r"\D", "", value or "")
    if digits.startswith("8") and len(digits) == 11:
        digits = "7" + digits[1:]
    if digits.startswith("7") and len(digits) == 11:
        rest = digits[1:]
        return f"+7 ({rest[0:3]}) {rest[3:6]}-{rest[6:8]}-{rest[8:10]}"
    return (value or "").strip()


def validate_ru_phone(value: str):
    v = normalize_phone(value)
    if not RU_PHONE_RE.match(v):
        raise ValidationError("Телефон должен быть в формате +7 (XXX) XXX-XX-XX")
    return v


class RegisterForm(UserCreationForm):
    first_name = forms.CharField(max_length=150, label="Имя")
    email = forms.EmailField(label="Email")
    phone = forms.CharField(max_length=32, required=False, label="Телефон")

    class Meta:
        model = User
        fields = ("username", "first_name", "email", "password1", "password2")
        labels = {"username": "Логин"}

    def clean_email(self):
        email = self.cleaned_data["email"].lower()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("Пользователь с таким email уже существует.")
        return email

    def clean_phone(self):
        p = self.cleaned_data.get("phone")
        if not p:
            return ""
        return validate_ru_phone(p)


class EmailOrUsernameAuthenticationForm(AuthenticationForm):
    username = forms.CharField(label="Email или логин")


class UserProfileForm(forms.ModelForm):
    first_name = forms.CharField(max_length=150, label="Имя")
    email = forms.EmailField(label="Email")

    class Meta:
        model = UserProfile
        fields = ("phone", "company")
        labels = {"phone": "Телефон", "company": "Компания"}

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user")
        super().__init__(*args, **kwargs)
        self.fields["first_name"].initial = self.user.first_name
        self.fields["email"].initial = self.user.email
        
        # Создаём новый упорядоченный словарь с правильным порядком полей
        from collections import OrderedDict
        ordered_fields = OrderedDict()
        
        # Сначала first_name и email
        ordered_fields["first_name"] = self.fields["first_name"]
        ordered_fields["email"] = self.fields["email"]
        
        # Потом остальные поля (phone, company)
        for name, field in self.fields.items():
            if name not in ["first_name", "email"]:
                ordered_fields[name] = field
        
        self.fields = ordered_fields

    def clean_email(self):
        email = self.cleaned_data["email"].lower()
        if User.objects.exclude(pk=self.user.pk).filter(email__iexact=email).exists():
            raise forms.ValidationError("Этот email уже используется другим пользователем.")
        return email

    def clean_phone(self):
        p = self.cleaned_data.get("phone") or ""
        if not p.strip():
            return ""
        return validate_ru_phone(p)

    def save(self, commit=True):
        profile = super().save(commit=False)
        self.user.first_name = self.cleaned_data["first_name"]
        self.user.email = self.cleaned_data["email"]
        if commit:
            self.user.save()
            profile.save()
        return profile
class LeadConsultationForm(forms.Form):
    """Блок consultation-global → lead_type consultation."""

    name = forms.CharField(max_length=255, label="Имя")
    phone = forms.CharField(
        max_length=32,
        label="Телефон",
        widget=forms.TextInput(attrs={"type": "tel", "placeholder": "+7 (XXX) XXX-XX-XX", "autocomplete": "tel"}),
    )

    def clean_phone(self):
        return validate_ru_phone(self.cleaned_data["phone"])


class LeadCallbackForm(forms.Form):
    """Карточка на главной → lead_type callback."""

    phone = forms.CharField(
        max_length=32,
        label="Телефон",
        widget=forms.TextInput(attrs={"type": "tel", "placeholder": "+7 (XXX) XXX-XX-XX", "autocomplete": "tel"}),
    )

    def clean_phone(self):
        return validate_ru_phone(self.cleaned_data["phone"])


class LeadCalculationForm(forms.Form):
    ENTERPRISE_CHOICES = [
        ("Производственные места", "Производственные места"),
        ("Офис", "Офис"),
        ("Смешанный", "Смешанный"),
    ]

    employees_count = forms.IntegerField(
        min_value=1,
        initial=100,
        label="Количество сотрудников",
        widget=forms.NumberInput(attrs={"min": 1}),
    )
    workplaces_count = forms.IntegerField(
        min_value=1,
        initial=100,
        label="Количество рабочих мест",
        widget=forms.NumberInput(attrs={"min": 1}),
    )
    enterprise_type = forms.ChoiceField(choices=ENTERPRISE_CHOICES, label="Тип предприятия")

    def clean_phone(self):
        return validate_ru_phone(self.cleaned_data["phone"])


class LeadContactForm(forms.Form):
    full_name = forms.CharField(max_length=255, label="ФИО")
    phone = forms.CharField(
        max_length=32,
        label="Телефон",
        widget=forms.TextInput(attrs={"type": "tel", "placeholder": "+7 (XXX) XXX-XX-XX", "autocomplete": "tel"}),
    )
    email = forms.EmailField(label="Email")
    message = forms.CharField(widget=forms.Textarea(attrs={"rows": 4}), required=False, label="Сообщение")

    def clean_phone(self):
        return validate_ru_phone(self.cleaned_data["phone"])


class LeadServiceForm(forms.ModelForm):
    class Meta:
        model = Lead
        fields = ("full_name", "phone", "email", "message")
        labels = {
            "full_name": "ФИО",
            "phone": "Телефон",
            "email": "Email",
            "message": "Сообщение",
        }
        widgets = {
            "message": forms.Textarea(attrs={"rows": 4}),
            "phone": forms.TextInput(attrs={"type": "tel", "placeholder": "+7 (XXX) XXX-XX-XX", "autocomplete": "tel"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["full_name"].required = True
        self.fields["phone"].required = True
        self.fields["email"].required = True

    def clean_phone(self):
        return validate_ru_phone(self.cleaned_data["phone"])

    def save(self, commit=True):
        obj = super().save(commit=False)
        obj.phone = validate_ru_phone(self.cleaned_data["phone"])
        if commit:
            obj.save()
        return obj

class SoutForm(forms.Form):
    workplaces_count = forms.IntegerField(
        label="Количество рабочих мест",
        min_value=1,
        required=True,
        widget=forms.NumberInput(attrs={'placeholder': '0'})
    )
    location = forms.CharField(
        label="Местонахождение организации",
        max_length=255,
        required=True,
        widget=forms.TextInput(attrs={'placeholder': 'Введите адрес организации'})
    )
    full_name = forms.CharField(
        label="Имя",
        max_length=255,
        required=True,
        widget=forms.TextInput(attrs={'placeholder': 'Иван Иванов'})
    )
    phone = forms.CharField(
        label="Телефон",
        max_length=32,
        required=True,
        widget=forms.TextInput(attrs={'type': 'tel', 'placeholder': '+7 (XXX) XXX-XX-XX'})
    )
    email = forms.EmailField(
        label="Электронная почта",
        required=True,
        widget=forms.EmailInput(attrs={'placeholder': 'mail@example.com'})
    )
    
    def clean_phone(self):
        phone = self.cleaned_data.get('phone')
        from .forms import validate_ru_phone
        return validate_ru_phone(phone)