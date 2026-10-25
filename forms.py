from django import forms

from .models import Visitor


class NameForm(forms.ModelForm):
    """Форма ввода имени. Поле строится по модели Visitor."""

    class Meta:
        model = Visitor
        fields = ["name"]
        labels = {"name": "Ваше имя"}
        widgets = {
            "name": forms.TextInput(
                attrs={
                    "placeholder": "Например, Анна",
                    "autocomplete": "given-name",
                    "autofocus": True,
                }
            ),
        }
        error_messages = {
            "name": {
                "required": "Поле имени не может быть пустым - пожалуйста, введите имя.",
                "max_length": "Имя слишком длинное: не больше %(limit_value)d символов.",
            },
        }

    def clean_name(self):
        # пробелы по краям Django уже убрал; строка из одних пробелов
        # превратилась в пустую и не прошла проверку required
        name = self.cleaned_data["name"]
        if not any(char.isalpha() for char in name):
            raise forms.ValidationError("Имя должно содержать хотя бы одну букву.")
        # несколько пробелов подряд внутри имени заменяем одним
        return " ".join(name.split())
