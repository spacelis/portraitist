from django.conf.urls import patterns, url
from django.views.generic import RedirectView
from django.views.generic import TemplateView

# Uncomment the next two lines to enable the admin:
# from django.contrib import admin
# admin.autodiscover()

urlpatterns = patterns(
    '',
    url(r'^$', RedirectView.as_view(url='/home', query_string=True)),
    url(r'^home$', 'apps.profileviewer.views.home'),
    url(r'^favicon\.ico$', RedirectView.as_view(
        url='/static/images/profileviewer/socialmining.ico')),
    url(r'^judgement_overview$',
        'apps.profileviewer.views.judgement_overview'),
    url(r'^import_judge/(.*)$', 'apps.profileviewer.views.import_judge'),

    url(r'^import_expert/(.*)$', 'apps.profileviewer.views.import_expert'),
    url(r'^expert_view/(.*)$', 'apps.profileviewer.views.expert_view'),
    url(r'^judge_expert$', 'apps.profileviewer.views.submit_expert_judgement'),

    url(r'^import_topic/(.*)$', 'apps.profileviewer.views.import_topic'),
    url(r'^topic_view/(.*)$', 'apps.profileviewer.views.topic_view'),
    url(r'^judge_topic$', 'apps.profileviewer.views.submit_topic_judgement'),
    url(r'^api/(.*)$', 'apps.profileviewer.api.call_endpoint'),
    url(r'^test_view$', 'apps.profileviewer.views.test_view'),
    url(r'^list_data_dir$', 'apps.profileviewer.views.list_data_dir'),
    url(r'^survey$', 'apps.profileviewer.views.survey'),

    url(r'^lgc_submit$', 'apps.profileviewer.views.lgc_submit'),
    url(r'^general_survey$', 'apps.profileviewer.views.general_survey'),


    url(r'^terms$', TemplateView.as_view(template_name="terms.html")),
    url(r'^about$', TemplateView.as_view(template_name="about.html")),
)
