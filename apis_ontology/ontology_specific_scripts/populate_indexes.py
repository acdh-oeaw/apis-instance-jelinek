
from datetime import datetime
from apis_ontology.models import Chapter, E1_Crm_Entity, E40_Legal_Body, F10_Person, F1_Work, F31_Performance, F3_Manifestation_Product_Type, Honour, Keyword, XMLNote, Xml_Content_Dump
from django.contrib.postgres.search import SearchVector
from django.contrib.contenttypes.models import ContentType
from django.db.models import Value, Q


def populate_indexes():
    count = 0
    total = E1_Crm_Entity.objects.all().count()
    contenttype_f10 = ContentType.objects.get_for_model(model=F10_Person)
    contenttype_e40 = ContentType.objects.get_for_model(model=E40_Legal_Body)
    contenttype_content_dump = ContentType.objects.get_for_model(model=Xml_Content_Dump)
    contenttype_note = ContentType.objects.get_for_model(model=XMLNote)
    contenttype_f1 = ContentType.objects.get_for_model(model=F1_Work)
    contenttype_honour = ContentType.objects.get_for_model(model=Honour)
    contenttype_f3 = ContentType.objects.get_for_model(model=F3_Manifestation_Product_Type)
    contenttype_chapter = ContentType.objects.get_for_model(model=Chapter)
    contenttype_f31 = ContentType.objects.get_for_model(model=F31_Performance)
    for ent in E1_Crm_Entity.objects_inheritance.select_subclasses("f1_work", "f3_manifestation_product_type", "honour", "f31_performance").order_by('self_contenttype').all():
        count += 1
        print("Processing entity {} of {}: {}".format(count, total, ent.self_contenttype.name))
        txt_e1 = ""
        txt_pers = ""
        txt_e40 = ""
        txt_xml_content = ""
        txt_xml_note = ""
        check = False
        for attr in ["name", "content", "file_content"]:
            if hasattr(ent, attr):
                if getattr(ent, attr) is not None:
                    txt_e1 += getattr(ent, attr) + " "
                    check = True
        if len(txt_e1) > 0:
            ent.vector_column_e1_set = SearchVector(Value(txt_e1), config='german')
        for triple in ent.triple_set_from_subj.filter(obj__self_contenttype_id=contenttype_f10):
            txt_pers += triple.obj.name + " "
            if triple.obj.entity_id is not None:
                txt_pers += triple.obj.entity_id + " "
        for triple in ent.triple_set_from_obj.filter(subj__self_contenttype_id=contenttype_f10):
            txt_pers += triple.subj.name + " "
            if triple.subj.entity_id is not None:
                txt_pers += triple.subj.entity_id + " "
        if len(txt_pers) > 0:
            check = True
            ent.vector_related_f10_set = SearchVector(Value(txt_pers))
        for triple in ent.triple_set_from_subj.filter(obj__self_contenttype_id=contenttype_e40):
            txt_e40 += triple.obj.name + " "
            if triple.obj.entity_id is not None:
                txt_e40 += format(triple.obj.entity_id.replace("_", "")) + " "
        for triple in ent.triple_set_from_obj.filter(subj__self_contenttype_id=contenttype_e40):
            txt_e40 += triple.subj.name + " "
            if triple.subj.entity_id is not None:
                txt_e40 += format(triple.subj.entity_id.replace("_", "")) + " "
        if len(txt_e40) > 0:
            check = True
            ent.vector_related_E40_set = SearchVector(Value(txt_e40))
        for triple in ent.triple_set_from_subj.filter(obj__self_contenttype_id=contenttype_content_dump):
            txt_xml_content += triple.obj.file_content + " "
        if len(txt_xml_content) > 0:
            check = True
            ent.vector_related_xml_content_dump_set = SearchVector(Value(txt_xml_content), config='german')
        for triple in ent.triple_set_from_subj.filter(obj__self_contenttype_id=contenttype_note):
            txt_xml_note += triple.obj.content + " "
        for triple in ent.triple_set_from_obj.filter(subj__self_contenttype_id=contenttype_note):
            txt_xml_note += triple.subj.content + " "
        if len(txt_xml_note) > 0:
            check = True
            ent.vector_related_xml_note_set = SearchVector(Value(txt_xml_note), config='german')
        t = datetime.now()
        txt_search_speedup = ""


        if ent.self_contenttype in [contenttype_f1, contenttype_honour]:
            is_in_chapters = ent.triple_set_from_subj.filter(prop__name="is in chapter")
            for chapter_triple in is_in_chapters:
                txt_search_speedup += "isinchapter{} ".format(chapter_triple.obj.chapter_number)
            is_about_work = ent.triple_set_from_subj.filter(prop__name="is about")
            for work_triple in is_about_work:
                if work_triple.obj.self_contenttype == contenttype_chapter:
                    txt_search_speedup += "isaboutchapter{} ".format(work_triple.obj.chapter_number)
                else:
                    txt_search_speedup += "isaboutentity{} ".format(work_triple.obj.entity_id)
            has_keyword = ent.triple_set_from_subj.filter(prop__name="has keyword")
            for kw_triple in has_keyword:
                txt_search_speedup += "haskeyword{} ".format(kw_triple.obj.entity_id)
        
        elif ent.self_contenttype in [contenttype_f31, contenttype_f3]:
            related_work = F1_Work.objects.filter(Q(triple_set_from_subj__obj=ent)).distinct()
            for w in related_work:
                if w.vector_search_speedup_set is not None:
                    txt_search_speedup += w.vector_search_speedup_set

        if len(txt_search_speedup) > 0:
            check = True
            ent.vector_search_speedup_set = SearchVector(Value(txt_search_speedup))

        if check:
            ent.save()


def run(*args, **options):
    def main_run():
        populate_indexes()
        # populate_f3_indexes()
    main_run()