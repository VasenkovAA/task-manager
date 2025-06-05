from django.db import models


class Link(models.Model):
    url = models.URLField(max_length=500, unique=True, help_text="Уникальный URL-адрес")
    created_at = models.DateTimeField(
        auto_now_add=True, help_text="Дата создания ссылки"
    )

    def __str__(self):
        return self.url

    class Meta:
        verbose_name = "Ссылка"
        verbose_name_plural = "Ссылки"
