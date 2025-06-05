from django.db import models


class Link(models.Model):
    """
    Модель для представления URL-ссылок.
    
    Attributes:
        url (URLField): Уникальный URL-адрес
        created_at (DateTimeField): Дата создания ссылки (автозаполнение)
    """
    url = models.URLField(max_length=500, unique=True, help_text="Уникальный URL-адрес")
    created_at = models.DateTimeField(
        auto_now_add=True, help_text="Дата создания ссылки"
    )

    def __str__(self):
        return self.url

    class Meta:
        """
        Метаданные модели Link.
        
        Attributes:
            verbose_name (str): Человекочитаемое имя в единственном числе
            verbose_name_plural (str): Человекочитаемое имя во множественном числе
        """
        verbose_name = "Ссылка"
        verbose_name_plural = "Ссылки"
