from django.shortcuts import render


def page_not_found(request, exception):
    return render(
        request, 'errors/404.html', {'path': request.path}, status=404
    )


def server_error(request):
    return render(request, 'errors/500.html', status=500)


def permission_denied(request, exception):
    return render(request, 'errors/403.html', status=403)


def csrf_error(request, reason=''):
    return render(request, 'errors/403csrf.html', status=403)
