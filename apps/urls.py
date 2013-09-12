from django.conf.urls import patterns, include, url
from django.views.generic import RedirectView

# Uncomment the next two lines to enable the admin:
# from django.contrib import admin
# admin.autodiscover()

urlpatterns = patterns('',
    # Examples:
    url(r'^$', RedirectView.as_view(url='/home', query_string=True)),
    url(r'^home$', 'apps.profileviewer.views.home'),
    url(r'^favicon\.ico$', RedirectView.as_view(url='/static/images/profileviewer/socialmining.ico')),
    url(r'^judgement_overview$', 'apps.profileviewer.views.judgement_overview'),
    url(r'^import_judge/(.*)$', 'apps.profileviewer.views.import_judge'),

    url(r'^import_expert/(.*)$', 'apps.profileviewer.views.import_expert'),
    url(r'^expert_view/(.*)$', 'apps.profileviewer.views.expert_view'),
    url(r'^judge_expert$', 'apps.profileviewer.views.submit_expert_judgement'),

    url(r'^import_topic/(.*)$', 'apps.profileviewer.views.import_topic'),
    url(r'^topic_view/(.*)$', 'apps.profileviewer.views.topic_view'),
    url(r'^judge_topic$', 'apps.profileviewer.views.submit_topic_judgement'),
    url(r'^api/(.*)$', 'apps.profileviewer.api.endpoints'),
    url(r'^test_view$', 'apps.profileviewer.views.test_view'),
    url(r'^list_data_dir$', 'apps.profileviewer.views.list_data_dir'),
    # url(r'^profileviewer/', include('profileviewer.foo.urls')),

    # Uncomment the admin/doc line below to enable admin documentation:
    # url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    # url(r'^admin/', include(admin.site.urls)),
)
