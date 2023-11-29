
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
    contenttype_f3 = ContentType.objects.get_for_model(model=F3_Manifestation_Product_Type)
    contenttype_chapter = ContentType.objects.get_for_model(model=Chapter)
    contenttype_f31 = ContentType.objects.get_for_model(model=F31_Performance)
    for ent in E1_Crm_Entity.objects_inheritance.select_subclasses("f1_work", "f3_manifestation_product_type", "honour", "f31_performance").all():
        count += 1
        print("Processing entity {} of {}".format(count, total))
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
        related_work = [ent]
        if ent.self_contenttype in [contenttype_f31, contenttype_f3]:
            related_work = F1_Work.objects.filter(Q(triple_set_from_subj__obj=ent) | Q(triple_set_from_subj__obj__triple_set_from_subj__obj=ent, triple_set_from_subj__obj__triple_set_from_subj__prop__name="has host")).distinct()
        # Chapters
        is_in_chapters = [triple.obj for work in related_work for triple in work.triple_set_from_subj.filter(prop__name="is in chapter")]
        # is_about_chapters = [triple.obj for work in related_work for triple in work.triple_set_from_subj.filter(prop__name="is about")]
        # is_in_chapters = Chapter.objects.filter(triple_set_from_obj__subj__in=related_work, triple_set_from_obj__prop__name="is in chapter")
        # is_about_chapters = Chapter.objects.filter(triple_set_from_obj__subj__in=related_work, triple_set_from_obj__prop__name="is about")
        for chapter in is_in_chapters:
            txt_search_speedup += "isinchapter{} ".format(chapter.chapter_number)
        # for chapter in is_about_chapters:
        #     txt_search_speedup += "isaboutchapter{} ".format(chapter.chapter_number)
        # Work
        is_about_work = [triple.obj for work in related_work for triple in work.triple_set_from_subj.filter(prop__name="is about")]
        # is_about_work = E1_Crm_Entity.objects.filter(triple_set_from_obj__subj__in=related_work, triple_set_from_obj__prop__name="is about")
        for work in is_about_work:
            if work.self_contenttype == contenttype_chapter:
                txt_search_speedup += "isaboutchapter{} ".format(work.chapter_number)
            else:
                txt_search_speedup += "isaboutentity{} ".format(work.entity_id)
        # Keyword
        has_keyword = [triple.obj for work in related_work for triple in work.triple_set_from_subj.filter(prop__name="has keyword")]
        # has_keyword = Keyword.objects.filter(triple_set_from_obj__subj__in=related_work, triple_set_from_obj__prop__name="has keyword")
        for kw in has_keyword:
            txt_search_speedup += "haskeyword{} ".format(kw.entity_id)
        print(datetime.now() - t)
        if len(txt_search_speedup) > 0:
            check = True
            ent.vector_search_speedup_set = SearchVector(Value(txt_search_speedup))

        if check:
            ent.save()

# def populate_f3_indexes():
#     count=0
#     total=F3_Manifestation_Product_Type.objects.count()
#     for ent in F3_Manifestation_Product_Type.objects.all():
#         check = False
#         count += 1
#         print("Processing F3 {}/{}".format(count, total))
#         txt_search_speedup = ""
#         related_work = F1_Work.objects.filter(Q(triple_set_from_subj__obj=ent) | Q(triple_set_from_subj__obj__triple_set_from_subj__obj=ent, triple_set_from_subj__obj__triple_set_from_subj__prop__name="has host")).distinct()
#         # Chapters
#         is_in_chapters = Chapter.objects.filter(triple_set_from_obj__subj__in=related_work, triple_set_from_obj__prop__name="is in chapter")
#         is_about_chapters = Chapter.objects.filter(triple_set_from_obj__subj__in=related_work, triple_set_from_obj__prop__name="is about")
#         for chapter in is_in_chapters:
#             txt_search_speedup += "isinchapter{} ".format(chapter.chapter_number)
#         for chapter in is_about_chapters:
#             txt_search_speedup += "isaboutchapter{} ".format(chapter.chapter_number)
#         # Work
#         is_about_work = E1_Crm_Entity.objects.filter(triple_set_from_obj__subj__in=related_work, triple_set_from_obj__prop__name="is about")
#         for work in is_about_work:
#             txt_search_speedup += "isaboutentity{} ".format(work.entity_id)
#         # Keyword
#         has_keyword = Keyword.objects.filter(triple_set_from_obj__subj__in=related_work, triple_set_from_obj__prop__name="has keyword")
#         for kw in has_keyword:
#             txt_search_speedup += "haskeyword{} ".format(kw.entity_id)

#         if len(txt_search_speedup) > 0:
#             check = True
#             ent.vector_search_speedup_set = SearchVector(Value(txt_search_speedup))
#         if check:
#             ent.save()



def run(*args, **options):
    def main_run():
        populate_indexes()
        # populate_f3_indexes()
    main_run()