from django.core.management.base import BaseCommand

from main.models import Course, Service


class Command(BaseCommand):
    help = "Seed initial services for ЗабТехЭксперт"

    def handle(self, *args, **options):
        services = [
            {
                "title": "Специальная оценка условий труда (СОУТ)",
                "slug": "sout",
                "photo": "img/placeholder14.png",
                "short_description": "Организация и сопровождение СОУТ, подготовка пакета документов и отчетности.",
                "full_description": (
                    "Проводим специальную оценку условий труда: подготовка исходных данных, взаимодействие с "
                    "подразделениями, контроль этапов и оформление результатов. Обеспечиваем корректность "
                    "документации и соблюдение требований законодательства."
                ),
                "order": 10,
            },
            {
                "title": "Оценка профессиональных рисков",
                "slug": "professional-risks",
                "photo": "img/placeholder15.png",
                "short_description": "Идентификация опасностей, оценка рисков и разработка мероприятий по снижению.",
                "full_description": (
                    "Выполняем оценку профессиональных рисков: обследование рабочих мест, анализ факторов, "
                    "формирование карты рисков и плана мероприятий. Помогаем интегрировать результаты в систему "
                    "управления охраной труда."
                ),
                "order": 20,
            },
            {
                "title": "Производственный контроль",
                "slug": "production-control",
                "photo": "img/placeholder16.png",
                "short_description": "Программы ПК, лабораторные и инструментальные измерения, отчеты и рекомендации.",
                "full_description": (
                    "Организуем производственный контроль: разработка программы, планирование измерений, "
                    "сопровождение отбора проб и оформление протоколов. Предоставляем рекомендации по устранению "
                    "несоответствий и снижению рисков."
                ),
                "order": 30,
            },
            {
                "title": "Дистанционное обучение",
                "slug": "labor-training",
                "photo": "img/placeholder17.png",
                "short_description": "Обучение и проверка знаний в удобном формате для сотрудников и руководителей.",
                "full_description": (
                    "Проводим дистанционное обучение по охране труда: актуальные программы, контроль прохождения "
                    "и оформление документов. Подберем формат под должности и специфику деятельности."
                ),
                "order": 40,
            },
            {
                "title": "Печатная продукция по охране труда",
                "slug": "printed-products",
                "photo": "img/consult.png",
                "short_description": "Журналы, инструкции, плакаты и комплекты документации для предприятий.",
                "full_description": (
                    "Изготавливаем печатные материалы по охране труда: журналы, инструкции, плакаты и "
                    "информационные стенды. Помогаем привести комплект документов к единому стандарту."
                ),
                "order": 50,
            },
        ]

        created = 0
        updated = 0
        keep_slugs = set()
        for item in services:
            keep_slugs.add(item["slug"])
            obj, was_created = Service.objects.update_or_create(
                slug=item["slug"],
                defaults=item,
            )
            if was_created:
                created += 1
            else:
                updated += 1

        # Deactivate any legacy services from previous versions
        Service.objects.exclude(slug__in=keep_slugs).update(is_active=False, order=999)

        courses = [
            ("Охрана труда для руководителей и специалистов", "labor", 40),
            ("Безопасные методы работ на высоте", "labor", 24),
            ("Пожарно-технический минимум", "fire", 16),
            ("Первая помощь пострадавшим", "first_aid", 16),
            ("Промышленная безопасность. Общие требования", "industrial", 40),
            ("Экологическая безопасность для ответственных лиц", "ecology", 24),
        ]
        for title, category, duration in courses:
            Course.objects.update_or_create(
                title=title,
                defaults={
                    "category": category,
                    "duration_hours": duration,
                    "description": f"Программа по направлению «{title}».",
                    "is_active": True,
                },
            )

        self.stdout.write(self.style.SUCCESS(f"Services created: {created}, updated: {updated}"))
