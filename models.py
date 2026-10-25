from django.db import models


class Visitor(models.Model):
    """Таблица с именами пользователей. По заданию в модели одно поле - name."""

    name = models.CharField("имя", max_length=100)

    class Meta:
        verbose_name = "посетитель"
        verbose_name_plural = "посетители"

    def __str__(self):
        return self.name
