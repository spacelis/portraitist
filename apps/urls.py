from django.conf.urls import patterns, url
from django.views.generic import RedirectView
from django.views.generic import TemplateView

# Uncomment the next two lines to enable the admin:
# from django.contrib import admin
# admin.autodiscover()


urlpatterns = patterns(
    '',
    url(r'^favicon\.ico$', RedirectView.as_view(
        url='/static/profileviewer/images/socialmining.ico')),

    url(r'^goto_taskpack/(.*)$', 'apps.profileviewer.views.goto_taskpack'),
    url(r'^task_router$', 'apps.profileviewer.views.task_router'),
    url(r'^task/(.*)$', 'apps.profileviewer.views.annotation_view'),
    url(r'^api/([a-zA-Z_]+).*$', 'apps.profileviewer.api.call_endpoint'),

    url(r'^terms$', TemplateView.as_view(template_name="terms.html")),
    url(r'^about$', TemplateView.as_view(template_name="about.html")),
)
