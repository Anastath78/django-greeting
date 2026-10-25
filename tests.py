from django.test import Client, TestCase
from django.urls import reverse

from .forms import NameForm
from .models import Visitor


class VisitorModelTest(TestCase):
    def test_only_name_field(self):
        # кроме служебного первичного ключа id в модели одно поле - name
        fields = [f.name for f in Visitor._meta.get_fields() if not f.primary_key]
        self.assertEqual(fields, ["name"])

    def test_str(self):
        self.assertEqual(str(Visitor(name="Анна")), "Анна")


class NameFormTest(TestCase):
    def test_valid_name(self):
        form = NameForm(data={"name": "Анна"})
        self.assertTrue(form.is_valid())

    def test_spaces_are_normalized(self):
        form = NameForm(data={"name": "   Анна    Мария  "})
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data["name"], "Анна Мария")

    def test_empty_name(self):
        form = NameForm(data={"name": ""})
        self.assertFalse(form.is_valid())
        self.assertIn("не может быть пустым", form.errors["name"][0])

    def test_only_spaces(self):
        form = NameForm(data={"name": "     "})
        self.assertFalse(form.is_valid())

    def test_no_letters(self):
        form = NameForm(data={"name": "12345"})
        self.assertFalse(form.is_valid())
        self.assertIn("хотя бы одну букву", form.errors["name"][0])

    def test_too_long(self):
        form = NameForm(data={"name": "а" * 101})
        self.assertFalse(form.is_valid())


class IndexViewTest(TestCase):
    url = reverse("greetings:index")

    def test_get_shows_form(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Submit")
        self.assertContains(response, "csrfmiddlewaretoken")
        self.assertContains(response, "Здравствуйте!")

    def test_post_saves_name_and_greets(self):
        response = self.client.post(self.url, {"name": "Анна"})
        self.assertRedirects(response, self.url)
        self.assertEqual(Visitor.objects.count(), 1)
        self.assertEqual(Visitor.objects.get().name, "Анна")

        response = self.client.get(self.url)
        self.assertContains(response, "Привет, Анна!")

    def test_post_empty_name_shows_error(self):
        response = self.client.post(self.url, {"name": ""})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "не может быть пустым")
        self.assertEqual(Visitor.objects.count(), 0)

    def test_post_without_field(self):
        response = self.client.post(self.url, {})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Visitor.objects.count(), 0)

    def test_html_is_escaped(self):
        # защита от XSS: тег не должен попасть на страницу как разметка
        self.client.post(self.url, {"name": "<script>alert(1)</script>"})
        response = self.client.get(self.url)
        self.assertNotContains(response, "<script>alert(1)</script>")
        self.assertContains(response, "&lt;script&gt;")

    def test_greeting_is_personal(self):
        # второй пользователь (другая сессия) не видит чужое имя
        self.client.post(self.url, {"name": "Анна"})
        other = Client()
        response = other.get(self.url)
        self.assertNotContains(response, "Привет, Анна!")
        self.assertContains(response, "Здравствуйте!")

    def test_deleted_visitor(self):
        self.client.post(self.url, {"name": "Анна"})
        Visitor.objects.all().delete()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Здравствуйте!")

    def test_method_not_allowed(self):
        response = self.client.put(self.url)
        self.assertEqual(response.status_code, 405)


class CsrfProtectionTest(TestCase):
    url = reverse("greetings:index")

    def setUp(self):
        # обычный тестовый клиент Django CSRF не проверяет, поэтому включаем проверку явно
        self.client = Client(enforce_csrf_checks=True)

    def test_post_without_token_is_rejected(self):
        response = self.client.post(self.url, {"name": "Анна"})
        self.assertEqual(response.status_code, 403)
        self.assertContains(response, "Запрос отклонён", status_code=403)
        self.assertEqual(Visitor.objects.count(), 0)

    def test_post_with_token_is_accepted(self):
        self.client.get(self.url)
        token = self.client.cookies["csrftoken"].value
        response = self.client.post(
            self.url, {"name": "Анна", "csrfmiddlewaretoken": token}
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Visitor.objects.count(), 1)

    def test_security_headers(self):
        response = self.client.get(self.url)
        self.assertEqual(response["X-Frame-Options"], "DENY")
        self.assertEqual(response["X-Content-Type-Options"], "nosniff")
