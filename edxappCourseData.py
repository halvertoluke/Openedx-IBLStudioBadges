#!/usr/bin/env python
# -*- coding: utf-8 -*-
from pymongo import Connection


# Convert unicode2utf8 dicts
def convertUnicode2Utf8Dict(data):
    import collections
    if isinstance(data, basestring):
        return data.encode('utf8')
    elif isinstance(data, collections.Mapping):
        return dict(map(convertUnicode2Utf8Dict, data.iteritems()))
    elif isinstance(data, collections.Iterable):
        return type(data)(map(convertUnicode2Utf8Dict, data))
    else:
        return data

#
# Mongo DB Connect
#
xmoduledb = "edxapp"
connection = Connection()
db = connection[xmoduledb]
mongo_modulestore = db['modulestore']

# course -> id.category : course
#   section -> id.category : chapter
#       subsection -> _id.category : sequential
#           problem -> _id.category : vertical

#
# Get Chapters : sections
#


def getCourseChapters(dict_course, xblock_category):
    res_list = []
    if len(dict_course) > 0:
        for i, v in enumerate(dict_course):
            _id = v.get('_id')
            definition = v.get('definition')
            metadata = v.get('metadata')
            if v.get('_id')['category'] == 'course':
                chapters = definition['children']
                if len(chapters) > 0:
                    for k in chapters:
                        sequentials = getCourseSequentials(dict_course, k.split('/')[::-1][0], xblock_category)
                        res_list.append({'category': 'chapter', 'module_id': k, 'name': k.split('/')[::-1][0], 'chapters': sequentials})
    return res_list

#
# Get Sequentials : subsections
#


def getCourseSequentials(dict_course, cname, xblock_category):
    res_list = []
    if len(dict_course) > 0:
        for i, v in enumerate(dict_course):
            if v.get('_id')['name'] == cname and v.get('_id')['category'] == 'chapter':
                childs = v.get('definition')['children']
                if len(childs) > 0:
                    for k in childs:
                        verticals = getCourseVerticals(dict_course, k.split('/')[::-1][0], xblock_category)
                        res_list.append({'category': 'sequential', 'module_id': k, 'name': k.split('/')[::-1][0], 'verticals': verticals})
    return res_list

#
# Get Verticals : for group problems in subsection
#


def getCourseVerticals(dict_course, cname, xblock_category):
    res_list = []
    if len(dict_course) > 0:
        for i, v in enumerate(dict_course):
            if v.get('_id')['name'] == cname and v.get('_id')['category'] == 'sequential':
                childs = v.get('definition')['children']
                items = []
                if len(childs) > 0:
                    for k in childs:
                        items = getCourseItems(dict_course, k.split('/')[::-1][0], xblock_category)
                        total_score = getCourseVerticalsScore(dict_course, cname, xblock_category)
                        res_list.append({'category': 'vertical', 'module_id': k, 'name': k.split('/')[::-1][0], 'items': items, 'total_score': total_score})
    return res_list

#
# Get Items : last level
# filter: problems and category_badges
#


def getCourseItems(dict_course, cname, xblock_category):
    res_list = []
    badge_id = 0
    item_score = 0
    total_score = 0
    if len(dict_course) > 0:
        for i, v in enumerate(dict_course):
            if v.get('_id')['name'] == cname and v.get('_id')['category'] == 'vertical':
                childs = v.get('definition')['children']
                if len(childs) > 0:
                    for k in childs:
                        item_name = k.split('/')[::-1][0]
                        for item, val in enumerate(dict_course):
                            if val.get('_id')['name'] == item_name and (val.get('_id')['category'] == 'problem' or val.get('_id')['category'] == 'openassessment' or val.get('_id')['category'] == '' + xblock_category + ''):
                                category = val.get('_id')['category']
                                revision = val.get('_id')['revision']
                                metadata = val.get('metadata')
                                definition = val.get('definition')
                                if category == '' + xblock_category + '' and revision != 'draft':
                                    if 'bg_id' in definition['data']:
                                        badge_id = val.get('definition')['data']['bg_id']
                                    else:
                                        badge_id = 0
                                    res_list.append({'category': category, 'module_id': k, 'name': item_name, 'badge_id': badge_id, 'item_score': item_score})
                                else:
                                    if category == 'problem' and revision != 'draft':
                                        item_score = 0  # init
                                        if 'weight' in metadata:
                                            item_score = metadata['weight']
                                        if item_score == 0: item_score = 1
                                        res_list.append({'category': category, 'module_id': k, 'name': item_name, 'badge_id': badge_id, 'item_score': item_score})
    return res_list

#
# Get Verticals Score : total subsections
#


def getCourseVerticalsScore(dict_course, cname, xblock_category):
    res_list = []
    total_score = 0
    if len(dict_course) > 0:
        for i, v in enumerate(dict_course):
            if v.get('_id')['name'] == cname and v.get('_id')['category'] == 'sequential':
                childs = v.get('definition')['children']
                items = []
                if len(childs) > 0:
                    for k in childs:
                        items = getCourseItems(dict_course, k.split('/')[::-1][0], xblock_category)
                        for item in items:
                            item_score = item['item_score']
                            total_score += int(item_score)
    return total_score


def getDictCompleteCourseData(conn, course_id, xblock_category):
    course = setParseCourseId(course_id)
    dict_course = []
    if course != '':
        corg = course[0]
        ccourse = course[1]
        cname = course[2]
        res_query = conn.find({'_id.org': '' + corg + '', '_id.course': '' + ccourse + '', '_id.category': {"$in": ['course', 'chapter', 'sequential', 'vertical', 'problem', '' + xblock_category + '']}}, {'definition.children': 1, 'definition.data.bg_id': 1, 'metadata.weight': 1})
        if res_query:
            for item in res_query:
                dict_course.append(convertUnicode2Utf8Dict(item))
    return dict_course


def getDictCompleteCourseDataDogwood(conn, course_id, xblock_category):
    # Get all (course, chapter, iblstudiosbadges, sequential, vertical and problem types)
    # blocks for the badges component's course
    course = setParseCourseId(course_id)
    dict_course = []
    if course != '':
        corg = course[0]
        ccourse = course[1]
        cname = course[2]
        res_query = conn.find({'run': cname, 'course': ccourse, 'org': corg})
        if res_query:
            for item in res_query:
                id_elements_course = item.get('versions').get('published-branch')
                structure = db['modulestore.structures']
                structures = structure.find({"_id": id_elements_course})
                for blocks in structures:
                    all_blocks = blocks.get('blocks')
                    for dictionary in all_blocks:
                        if dictionary.get('block_type') in ['course', 'chapter', xblock_category, 'sequential', 'vertical', 'problem']:
                            dict_course.append(convertUnicode2Utf8Dict(dictionary))
    return dict_course


def setParseCourseId(course_id):
    if course_id != '' and course_id != 'None':
        course = course_id.split('/')
        if len(course) == 1:
            course = course_id.split(':')[1].split('+')
        corg = course[0]
        ccourse = course[1]
        cname = course[2]
        if corg != '' and ccourse != '' and cname != '':
            return course
        else:
            return ''


def getCompleteListProblems(conn, course_id, xblock_category):
    result_dict = []
    dict_course = getDictCompleteCourseData(conn, course_id, xblock_category)
    if len(dict_course) > 0:
        res_complete = getCourseChapters(dict_course, xblock_category)
        for k1 in res_complete:
            chapters = k1['chapters']
            for k2 in chapters:
                chapter_module_id = k2['module_id']
                verticals = k2['verticals']
                for k3 in verticals:
                    vertical_module_id = k3['module_id']
                    vertical_total_score = k3['total_score']
                    items = k3['items']
                    for k4 in items:
                        data_list = {'chapter_module_id': chapter_module_id, 'vertical_module_id': vertical_module_id,
                                     'item_module_id': k4['module_id'], 'item_category': k4['category'],
                                     'item_badge_id': k4['badge_id'], 'item_score': k4['item_score'], 'chapter_max_score': vertical_total_score}
                        result_dict.append(data_list)
    return result_dict


def getCompleteListProblemsDogwood(conn, course_id, xblock_category, badge_id, scope_score):
    # consigo todos los elementos importantes del curso
    dict_course = getDictCompleteCourseDataDogwood(conn, course_id, xblock_category)
    course_splitted = setParseCourseId(course_id)

    # consigo el id del badge en cuestión
    my_id_badge = ''
    definitions = db['modulestore.definitions']
    if len(dict_course) > 0:
        for block in dict_course:
            if block.get('block_type') == xblock_category:
                objectid = block.get('definition')
                definition_badge = definitions.find({'_id': objectid})
                for simple_badge in definition_badge:
                    if simple_badge.get('fields').get('bg_id') == badge_id:
                        my_id_badge = block.get('block_id')

    # Unidad
    id_scope_score = get_parent_Dogwood(dict_course, my_id_badge)
    if scope_score != 'Unit':
        # Subseccion
        id_scope_score = get_parent_Dogwood(dict_course, id_scope_score)
        if scope_score != 'Subsection':
            # Seccion
            id_scope_score = get_parent_Dogwood(dict_course, id_scope_score)
            if scope_score != 'Section':
                # Curso
                id_scope_score = get_parent_Dogwood(dict_course, id_scope_score)

    # Guardo en una listas todos los problemas relacionados con badge y el alcance dado
    return get_problems_children_Dogwood(dict_course, id_scope_score, [], badge_id, course_splitted)


def get_parent_Dogwood(dict_course, current_id):
    id_parent = ''
    for block in dict_course:
        list_children = block.get('fields').get('children')
        if len(list_children) > 0:
            for child in list_children:
                if current_id in child:
                    id_parent = block.get('block_id')
    return id_parent


def get_problems_children_Dogwood(dict_course, id_elements, list_children, badge_id, course_splitted):
    for block in dict_course:
        if block.get('block_id') == id_elements:
            children = block.get('fields').get('children')
            if len(children) > 0:
                for child in children:
                    get_problems_children_Dogwood(dict_course, child[-1], list_children, badge_id, course_splitted)
            else:
                flag = False
                block_type = block.get('block_type')
                if block_type == 'problem':
                    item_score = block.get('fields').get('weight', 1)
                    element_id_badge = 0
                    id_block = 'block-v1:%s+%s+%s+type@%s+block@%s' % (course_splitted[0], course_splitted[1], course_splitted[2], block_type, block.get('block_id'))
                    flag = True
                if block_type == 'iblstudiosbadges':
                    item_score = 0
                    element_id_badge = badge_id
                    id_block = 'block-v1:%s+%s+%s+type@%s+block@%s' % (course_splitted[0], course_splitted[1], course_splitted[2], block_type, block.get('block_id'))
                    flag = True
                if flag:
                    problem_dictionary = {'item_badge_id': element_id_badge, 'item_category': block_type, 'item_module_id': id_block, 'item_score': item_score}
                    list_children.append(problem_dictionary)
                flag = False
    return list_children


# Main functions


def getListProblemsFromBadgeId(conn, badge_id, course_id, xblock_category):
    chapter_module_id = ''
    problems_list = []
    if course_id != '' and course_id != 'None' and badge_id != '' and badge_id != 'None':
        dict_course = getCompleteListProblems(conn, course_id, xblock_category)
        if len(dict_course) > 0:
            for k in dict_course:
                if k['item_badge_id'] == badge_id:
                    chapter_module_id = k['chapter_module_id']
        if chapter_module_id != '':
            for p in dict_course:
                if p['chapter_module_id'] == chapter_module_id:
                    # print ('%s : %s') % (p['item_module_id'],p['item_score'])
                    problems_list.append({'problem_id': p['item_module_id'], 'problem_score': p['item_score']})
    return problems_list

#
# Get Score from given badge_id
#


def getScoreFromBadgeId(conn, badge_id, course_id, xblock_category):
    score = '0'
    if course_id != '' and course_id != 'None' and badge_id != '' and badge_id != 'None':
        dict_course = getCompleteListProblems(conn, course_id, xblock_category)
        if len(dict_course) > 0:
            for k in dict_course:
                if k['item_badge_id'] == badge_id:
                    score = k['chapter_max_score']
    return score


def getListProblemsFromBadgeIdDogwood(conn, badge_id, course_id, xblock_category, scope_score):
    problems_list = []
    if course_id != '' and course_id != 'None' and badge_id != '' and badge_id != 'None':
        dict_course = getCompleteListProblemsDogwood(conn, course_id, xblock_category, badge_id, scope_score)
        for p in dict_course:
            problems_list.append({'problem_id': p['item_module_id'], 'problem_score': p['item_score']})
    return problems_list

#
# Get Score from given badge_id
#


def getScoreFromBadgeIdDogwood(conn, badge_id, course_id, xblock_category, scope_score):
    score = 0
    if course_id != '' and course_id != 'None' and badge_id != '' and badge_id != 'None':
        dict_course = getCompleteListProblemsDogwood(conn, course_id, xblock_category, badge_id, scope_score)
        if len(dict_course) > 0:
            for k in dict_course:
                score = score + k.get('item_score')
    return score

