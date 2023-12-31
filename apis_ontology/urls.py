from apis_acdhch_default_settings.urls import urlpatterns
from rest_framework import routers
from django.urls import include, path
from .jelinek_api_views import *
from django.contrib.auth.decorators import login_required

app_name = "jelinek"


router = routers.DefaultRouter()

router.register(r'f3_manifestation', F3ManifestationProductType, basename='F3ManifestationProductType')
router.register(r'f31_performance', F31Performance, basename='F31Performance')
router.register(r'f1_work', F1Work, basename='F1Work')
router.register(r'honour', Honour, basename='Honour')
router.register(r'work_for_chapter', WorkForChapter, basename='WorkForChapter')
router.register(r'search', Search, basename="Search")
router.register(r'entities_without_relations', EntitiesWithoutRelations, basename='EntitiesWithoutRelations')

# rebuild additional serializers
router.register(r'triples', Triples, basename='Triples')
router.register(r'person_triples', PersonTriples, basename='PersonTriples')
# router.register(r'manifestation_details', ManifestationDetails, basename='ManifestationDetails')
router.register(r'notes', Notes, basename='Notes')
router.register(r'work_chapters', WorkChapters, basename='WorkChapters')
router.register(r'original_work', OriginalWorkOnly, basename='OriginalWorkOnly')


customurlpatterns = [
    path('custom-api/', include(router.urls)),
    path("accounts/", include("django.contrib.auth.urls")),
]
urlpatterns = customurlpatterns + urlpatterns
