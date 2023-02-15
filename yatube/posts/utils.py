from django.core.paginator import Paginator

POSTS_PER_PAGE = 10


def paginate(request, posts):
    paginator = Paginator(posts, POSTS_PER_PAGE)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)
    return page_obj
