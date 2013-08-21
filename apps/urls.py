from django.conf.urls import patterns, include, url
from django.views.generic import RedirectView

# Uncomment the next two lines to enable the admin:
# from django.contrib import admin
# admin.autodiscover()

urlpatterns = patterns('',
    # Examples:
    url(r'^$', 'apps.profileviewer.views.home', name='home'),
    url(r'^view_profile/(.*)$', 'apps.profileviewer.views.view_profile', name='view_profile'),
    url(r'^upload$', 'apps.profileviewer.views.upload', name='upload'),
    url(r'^import/(.*)$', 'apps.profileviewer.views.import_data', name='import'),
    url(r'^submit_judgment$', 'apps.profileviewer.views.submit_judgment', name='submit_judgment'),
    url(r'^favicon\.ico$', RedirectView.as_view(url='/static/images/profileviewer/socialmining.ico')),
    # url(r'^profileviewer/', include('profileviewer.foo.urls')),

    # Uncomment the admin/doc line below to enable admin documentation:
    # url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    # url(r'^admin/', include(admin.site.urls)),
)
