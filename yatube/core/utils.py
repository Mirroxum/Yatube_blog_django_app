from django.core.paginator import Paginator


def paginator(request, list, settings):
    paginator = Paginator(list, settings)
    page_number = request.GET.get('page')
    return paginator.get_page(page_number)
