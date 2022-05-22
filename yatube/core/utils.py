from django.core.paginator import Paginator
from django.conf import settings


def paginator(page_number, list):
    paginator = Paginator(list, settings.MAX_PAGE_AMOUNT)
    return paginator.get_page(page_number)
