from django.shortcuts import get_object_or_404, redirect
from django.db.models import Q
from django.http import Http404

from mezzanine.pages.views import page as page_view

from widgy.contrib.widgy_mezzanine.models import WidgyPage
from widgy.models import Node


def get_page_from_node(root_node):
    try:
        # try to find a page that uses this root node
        return get_object_or_404(
            WidgyPage.objects.distinct(),
            Q(root_node__commits__root_node=root_node) | Q(root_node__working_copy=root_node)
        ).page_ptr
    except Http404:
        # otherwise, use a fake page
        return WidgyPage(
            titles='restoring page',
            content_model='widgypage',
        )


def handle_form(request, node_pk):
    form_node = get_object_or_404(Node, pk=node_pk)
    root_node = form_node.get_root()
    page = get_page_from_node(root_node)

    if request.method == 'POST':
        # not really necessary to prefetch two trees here, but if we just
        # prefetched root_node we would have to find a prefetched instance of
        # form_node in its tree.
        Node.prefetch_trees(form_node, root_node)

        form_class = form_node.content.get_form()
        form = form_class(request.POST, request.FILES)

        if form.is_valid():
            resp = form_node.content.execute(request, form)
            return resp or redirect(page.get_absolute_url())
        return page_view(request, page.slug, extra_context={
            'page': page,
            'root_node_override': root_node,
            form_node.content.context_var: form,
        })
    else:
        return redirect(page.get_absolute_url())


def preview(request, node_pk, node=None):
    node = node or get_object_or_404(Node, pk=node_pk)

    page = get_page_from_node(node)

    context = {
        'page': page,
        'root_node_override': node,
        '_current_page': page,
    }

    return page_view(request, page.slug, extra_context=context)
