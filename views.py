from django.shortcuts import redirect, render
from django.views.decorators.http import require_http_methods

from .forms import NameForm
from .models import Visitor

SESSION_KEY = "visitor_id"


@require_http_methods(["GET", "POST"])
def index(request):
    """
    Главная страница: форма ввода имени и персональное приветствие.

    POST - проверяем форму, сохраняем имя в базу, запоминаем id записи
    в сессии и делаем редирект (шаблон Post/Redirect/Get, чтобы при
    обновлении страницы форма не отправлялась повторно).
    GET - показываем форму и приветствие для имени из сессии.
    """
    if request.method == "POST":
        form = NameForm(request.POST)
        if form.is_valid():
            visitor = form.save()
            request.session[SESSION_KEY] = visitor.pk
            return redirect("greetings:index")
    else:
        form = NameForm()

    visitor = None
    visitor_id = request.session.get(SESSION_KEY)
    if visitor_id is not None:
        visitor = Visitor.objects.filter(pk=visitor_id).first()

    return render(request, "greetings/index.html", {"form": form, "visitor": visitor})
