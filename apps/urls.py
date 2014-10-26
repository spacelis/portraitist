from django.conf.urls import patterns, url
from django.views.generic import RedirectView
from django.views.generic import TemplateView

# Uncomment the next two lines to enable the admin:
# from django.contrib import admin
# admin.autodiscover()


urlpatterns = patterns(
    # Default
    '',
    url(r'^favicon\.ico$', RedirectView.as_view(
        url='/static/profileviewer/images/socialmining.ico')),
    url(r'^$', RedirectView.as_view(url='/instructions')),

    # Task related pages
    url(r'^pagerouter$', 'apps.profileviewer.views.pagerouter'),
    url(r'^confirm_code/(.*)$', 'apps.profileviewer.views.confirm_code_view'),
    url(r'^task/(.*)$', 'apps.profileviewer.views.annotation_view'),
    url(r'^submit_annotation$', 'apps.profileviewer.views.submit_annotation'),
    url(r'^survey$', 'apps.profileviewer.views.survey'),

    # Data endpoint
    url(r'^api/user/([a-zA-Z_]+).*$',
        'apps.profileviewer.api.user.call_endpoint'),
    url(r'^api/data/([a-zA-Z_]+).*$',
        'apps.profileviewer.api.data.call_endpoint'),
    url(r'^api/taskworker/([a-zA-Z_]+).*$',
        'apps.profileviewer.api.taskworker.call_endpoint'),

    # Static pages
    url(r'^terms$', TemplateView.as_view(template_name="terms.html")),
    url(r'^survey_form$', TemplateView.as_view(template_name="survey_form.html")),
    url(r'^about$', TemplateView.as_view(template_name="about.html")),
    url(r'^instructions$',
        TemplateView.as_view(template_name="instructions.html")),
)
