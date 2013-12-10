from google.appengine.ext import ndb
from django.http import HttpResponse


class TestModel(ndb.Model):

    name = ndb.StringProperty(indexed=True)
    data = ndb.JsonProperty(compressed=True)


def debug_view(request):
    """List the content of dir

    :request: @todo
    :returns: @todo

    """
    data = TestModel.query().fetch()[0]
    return HttpResponse(data, mimetype="application/json")
