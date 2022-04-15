from fastapi.encoders import jsonable_encoder

# 数据处理文件
__author__ = 'ren_mcc'


# TODO 递归获取树形结构数据
def get_tree_data(paren_list, child_list):
    for paren in paren_list:
        for child in child_list:
            if paren['id'] == child['parent_id']:
                if 'children' in paren and child not in paren['children']:
                    paren['children'].append(child)
                else:
                    paren['children'] = [child]
                get_tree_data(paren['children'], child_list)

    return paren_list


# TODO orm方式： 将一条查询的结果转化为对应字段的字典结果
def orm_one_to_dict(result):
    if not result or isinstance(result, list):
        return {}
    data = jsonable_encoder(dict(zip(result.keys(), result)))
    if "create_time" in data:
        data["create_time"] = data["create_time"].replace("T", " ")
    elif "last_change_time" in data:
        data["last_change_time"] = data["last_change_time"].replace("T", " ")
    elif "deleted_time" in data:
        data["deleted_time"] = data["deleted_time"].replace("T", " ")
    return data


# TODO orm方式： 将多条查询结果列表转化为对应字段的字典列表
def orm_all_to_dict(result_list):
    if not isinstance(result_list, list):
        return []
    data = jsonable_encoder([dict(zip(v.keys(), v)) for v in result_list])
    for d in data:
        if "create_time" in d:
            if d["create_time"]:
                d["create_time"] = d["create_time"].replace("T", " ")
        if "last_change_time" in d:
            if d["last_change_time"]:
                d["last_change_time"] = d["last_change_time"].replace("T", " ")
        if "deleted_time" in d:
            if d["deleted_time"]:
                d["deleted_time"] = d["deleted_time"].replace("T", " ")
        if "start_time" in d:
            if d["start_time"]:
                d["start_time"] = d["start_time"].replace("T", " ")
    return data


# TODO 原生SQL方式： 将一条查询结果转化为对应字段的字典
def sql_one_to_dict(result):
    if not result or isinstance(result, list):
        return {}
    return jsonable_encoder(dict(zip(result.keys(), result)))


# TODO 原生SQL方式： 将多条查询结果列表转化为对应的字段的字典列表
def sql_all_to_dict(result_list):
    if not isinstance(result_list, list):
        return []
    return jsonable_encoder([dict(zip(v.keys(), v)) for v in result_list])
