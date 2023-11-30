from rest_framework.response import Response
from rest_framework import viewsets
from .models import *
from .jelinek_api_serializers import *
from .jelinek_api_filters import *
from apis_core.apis_relations.models import Triple
from django.db.models import Q, Count, Sum, Case, When, IntegerField,Exists
from datetime import datetime
from django.db.models import Q, OuterRef
from django.db.models.functions import JSONObject
from django.contrib.postgres.aggregates import ArrayAgg
from django.contrib.postgres.expressions import ArraySubquery
from apis_core.apis_relations.models import Triple, Property
from django.contrib.contenttypes.models import ContentType


class F3ManifestationProductType(viewsets.ReadOnlyModelViewSet):
    serializer_class = F3ManifestationProductTypeSerializer
    filter_class = F3ManifestationProductTypeFilter
    queryset = F3_Manifestation_Product_Type.objects.all().prefetch_related('triple_set_from_obj', 'triple_set_from_subj')

class F31Performance(viewsets.ReadOnlyModelViewSet):
    serializer_class = F31PerformanceSerializer
    filter_class = F31PerformanceFilter
    queryset = F31_Performance.objects.all().prefetch_related('triple_set_from_obj', 'triple_set_from_subj')

class F1Work(viewsets.ReadOnlyModelViewSet):
    serializer_class = F1WorkSerializer
    filter_class = F1WorkFilter
    queryset = F1_Work.objects.all().prefetch_related('triple_set_from_subj')

class Honour(viewsets.ReadOnlyModelViewSet):
    serializer_class = HonourSerializer
    filter_class = HonourFilter
    queryset = Honour.objects.all().prefetch_related('triple_set_from_subj')

class WorkForChapter(viewsets.ReadOnlyModelViewSet):
    filter_class = ChapterFilter
    queryset = Chapter.objects.all().prefetch_related('triple_set_from_subj')
    serializer_class = WorkForChapterSerializer


class Search(viewsets.ReadOnlyModelViewSet):
    filter_class = SearchFilter
    serializer_class = SearchSerializer
    pagination_class = None

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())

        # apply facet filter 
        facet_filtered_queryset = FacetFilter(self.request.GET, queryset=queryset).qs

        serializer = self.get_serializer(facet_filtered_queryset, many=False)
        return Response(serializer.data)
    
    def get_queryset(self):
        f31_only = self.request.GET.get("return_type", "") == "f31"
        work_only_fields = ["title", "work_id", "honour_id", "genre", "genreFilter", "chapter_id", "keyword", "keyword_id", "workRole", 
                            "honourRole", "chapterRole", "limit", "filter_genre", "filter_keywords", "filter_startDate", 
                            "filter_endDate", "filter_persons", "filter_institutions", "filter_personRoles", "filter_institutionRoles"]
        work_only = set(i[0] for i in self.request.GET.items() if i[1] is not None and i[1] != "").issubset(work_only_fields)
        
        person_contenttype = ContentType.objects.get_for_model(model=F10_Person)
        institution_contenttype = ContentType.objects.get_for_model(model=E40_Legal_Body)
        person_subquery = F10_Person.objects.filter(triple_set_from_subj__obj_id=OuterRef("pk")).values(json=JSONObject(name="name", entity_id="entity_id"))
        person_property_subquery = Property.objects.filter(triple_set_from_prop__obj_id=OuterRef("pk"), triple_set_from_prop__subj__self_contenttype_id=person_contenttype).values_list('name', flat=True)
        institution_subquery = E40_Legal_Body.objects.filter(triple_set_from_subj__obj_id=OuterRef("pk")).values(json=JSONObject(name="name", entity_id="entity_id", type="institution_type"))
        institution_property_subquery = Property.objects.filter(triple_set_from_prop__obj_id=OuterRef("pk"), triple_set_from_prop__subj__self_contenttype_id=institution_contenttype).values_list('name', flat=True)
        keyword_subquery = Keyword.objects.filter(triple_set_from_obj__subj_id=OuterRef("pk")).values_list('name', flat=True)
        place_subquery = F9_Place.objects.filter(triple_set_from_obj__subj_id=OuterRef("pk")).values(json=JSONObject(name="name", entity_id="entity_id"))
        country_subquery = F9_Place.objects.filter(triple_set_from_obj__subj_id=OuterRef("pk")).values_list("country", flat=True)

        # include host type if type is "analyticPublication"
        mediatype_host_subquery = Q(triple_set_from_obj__subj__triple_set_from_obj__subj_id=OuterRef("pk"), triple_set_from_obj__subj__triple_set_from_obj__subj__triple_set_from_subj__obj__name="analyticPublication")
        mediatype_subquery = E55_Type.objects.filter(triple_set_from_obj__subj_id=OuterRef("pk")).union(E55_Type.objects.filter(mediatype_host_subquery)).values_list('name', flat=True)
        work_subquery = F1_Work.objects.filter(triple_set_from_subj__obj_id=OuterRef("pk"), triple_set_from_subj__prop__name__in=["is expressed in", "is reported in", "is original for translation", "has been performed in"]).distinct().values(json=JSONObject(pk="pk", name="name", genre="genre", entity_id="entity_id"))
        work_host_subquery = F1_Work.objects.filter(triple_set_from_subj__obj__triple_set_from_subj__obj_id=OuterRef("pk"), triple_set_from_subj__prop__name__in=["is expressed in", "is reported in", "is original for translation", "has been performed in"]).distinct().values(json=JSONObject(pk="pk", name="name", genre="genre", entity_id="entity_id"))
        subclass_filter = Q(f1_work__isnull=False) | Q(honour__isnull=False) | Q(f3_manifestation_product_type__isnull=False) | Q(f31_performance__isnull=False)
        if work_only:
            subclass_filter = Q(f1_work__isnull=False) | Q(honour__isnull=False)
        elif f31_only:
            subclass_filter = Q(f31_performance__isnull=False)
        qs = E1_Crm_Entity.objects_inheritance.select_subclasses("f1_work", "f3_manifestation_product_type", "honour", "f31_performance").filter(subclass_filter).annotate(
            related_persons=ArraySubquery(person_subquery),
            related_person_roles=ArraySubquery(person_property_subquery), 
            related_institutions=ArraySubquery(institution_subquery),
            related_institution_roles=ArraySubquery(institution_property_subquery), 
            related_keywords=ArraySubquery(keyword_subquery), 
            related_places=ArraySubquery(place_subquery), 
            related_countries=ArraySubquery(country_subquery), 
            related_mediatypes=ArraySubquery(mediatype_subquery),
            related_work= Case(
                When(
                    Exists(work_subquery), then=ArraySubquery(work_subquery)
                    ),
                default=ArraySubquery(work_host_subquery)
            )
            )
        return qs
    
class EntitiesWithoutRelations(viewsets.ReadOnlyModelViewSet):
    queryset = E1_Crm_Entity.objects.annotate(relation_count=Count("triple_set_from_obj")+Count("triple_set_from_subj", filter=Q(triple_set_from_subj__obj__name__regex=r'^(?!.*_index\.xml$).*$'))).filter(relation_count=0)
    serializer_class = LonelyE1CrmEntitySerializer
    filter_class=EntitiesWithoutRelationsFilter
