from django.shortcuts import render


def index(request):
    template_data = {"title": "Jobify - Home"}
    return render(request, "home/index.html", {"template_data": template_data})
