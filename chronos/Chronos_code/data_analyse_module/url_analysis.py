import json
import os
import re
from collections import defaultdict
from datetime import datetime
# import datetime
import numpy as np
import pandas as pd
from openpyxl import Workbook
from tqdm import tqdm
from sklearn.feature_extraction.text import CountVectorizer
from data_analyse_module.ipinfo_statistics.time_parser.parse_time import parse_time
from data_analyse_module.process_data_main import re_extract_lmt_in_url
from match_module.ert_cluster import get_file_paths
from match_module.tools.process_product_by_brand import process_brand_product, check_brand_similarity, wrong_data_index_record, process_url
from match_module.bishe_model import get_ert_list_from_model_ert_list, search_first_ert
from Levenshtein import distance as levenshtein_distance
from tools_global.statistic_global_parameters import time_dict
# import nltk
from nltk.util import ngrams
from collections import Counter
import difflib

def get_product_ERT(brand, sample_path):
    """
    Clustered ERT
    """
    data_dict = {}
    try:
        with open(sample_path, 'r', encoding='utf-8') as f:
            for line in f:
                json_line = json.loads(line)
                product = json_line['model']

                if len(product) < 3:
                    continue
                if product == '':
                    product = 'Unknown'
                if product.startswith('cisco'):
                    product = product[6:].strip()
                product, _ = process_brand_product(brand, product, '' , '')
                sample_ert = json_line['ert_list']
                version_list = []
                ert_list = []
                for item in sample_ert:
                    if item[0].startswith('build'):
                        continue
                    version_list.append(item[0])
                    ert_list.append(item[1].split(' ')[0])
                data_dict[product] = {"ert_version_list": version_list, "ert_list": ert_list, "lmt_list": [], "index_list": [], "sample_lmt_dict_list": [], "lmt_version_list": []}
    except FileNotFoundError:
        pass
    return data_dict


def preprocess_data(data_dict):
    version_dict = defaultdict(list)
    for product, data in data_dict.items():
        ert_version_list = data.get("ert_version_list", [])
        ert_dates = [datetime.strptime(date[:10], "%Y-%m-%d") for date in data.get("ert_list", [])]
        for version, ert in zip(ert_version_list, ert_dates):
            version_dict[version].append((product, ert))
    version_ert_product_dict = {}
    for version, data in version_dict.items():
        if version not in version_ert_product_dict.keys():
            version_ert_product_dict[version] = {}

        for product, ert in data:
            ert = str(ert).split(" ")[0]
            if ert not in version_ert_product_dict[version]:
                version_ert_product_dict[version][ert] = []
            version_ert_product_dict[version][ert].append(product)
    return version_dict, version_ert_product_dict


def merge_ert_versions(data_dict):
    version_time_dict = defaultdict(list)
    merged_data_dict = defaultdict(lambda: {"ert_list": [], "lmt_list": []})

    # Collect versions and their times
    for product, data in data_dict.items():
        ert_version_list = data.get("ert_version_list", [])
        ert_list = [datetime.strptime(date[:10], "%Y-%m-%d") for date in data.get("ert_list", [])]
        for version, ert in zip(ert_version_list, ert_list):
            version_time_dict[version].append((product, ert))

    # Merge versions
    for version, time_list in version_time_dict.items():
        time_list.sort(key=lambda x: x[1])  # Sort by date
        merged_products = set()

        # Check if versions can be merged
        for i in range(len(time_list) - 1):
            if is_nearby(time_list[i][1], time_list[i + 1][1], days=15):
                merged_products.add(time_list[i][0])
                merged_products.add(time_list[i + 1][0])

        # Merge data for products with same version and close release dates
        for product in merged_products:
            merged_data_dict[version]["ert_list"].extend(
                [datetime.strptime(date[:10], "%Y-%m-%d") for date in data_dict[product]["ert_list"]]
            )
            merged_data_dict[version]["lmt_list"].extend(
                [datetime.strptime(date[:10], "%Y-%m-%d") for date in data_dict[product]["lmt_list"]]
            )

    return merged_data_dict


def get_product_time_info(data_dict, LMT_sample_path, cisco_fofa_flag=False, no_version_flag=False):
    try:
        with open(LMT_sample_path, 'r', encoding='utf-8') as f:
            for line in f:
                json_line = json.loads(line)
                product = json_line['model']
                brand = json_line['brand']
                index = json_line['index']
                try:
                    version = json_line['version']
                except KeyError:
                    version = 'Unknown'
                if product == '':
                    product = 'Unknown'
                product, version = process_brand_product(brand, product, version, index)
                if 'hmnvr-td16o' in product:
                    continue
                if wrong_data_index_record(brand, index, product, version, no_version_flag=no_version_flag):
                    continue
                lmt = json_line['lmt'].split(' ')[0]
                # lmt = re_extract_lmt_in_url(json_line, brand)
                try:
                    sample_lmt = json_line['lmt_list']
                except KeyError:
                    sample_lmt = {}
                if product in data_dict.keys():
                    if lmt not in data_dict[product]["lmt_list"]:
                        data_dict[product]["lmt_list"].append(lmt)
                        data_dict[product]["index_list"].append(index)
                        data_dict[product]["sample_lmt_dict_list"].append(sample_lmt)
                        data_dict[product]["lmt_version_list"].append(version)
                else:
                    data_dict[product] = {"ert_version_list": [], "ert_list": [], "lmt_list": [lmt], "index_list": [index], "sample_lmt_dict_list": [sample_lmt], "lmt_version_list": [version]}
    except FileNotFoundError:
        pass
    return data_dict


def is_nearby(date1, date2, days=5):
    return abs((date1 - date2).days) <= days


def calculate_average_interval(dates):
    if len(dates) < 2:
        return 0
    intervals = [int(parse_time(dates[i + 1]) - parse_time(dates[i])) for i in range(len(dates) - 1)]
    return sum(intervals) / len(intervals)


def calculate_score(data_dict):
    score_dict = {}
    for product in data_dict.keys():
        ERT_list = data_dict[product]["ert_list"]
        if ERT_list == []:
            continue

        LMT_list = data_dict[product]["lmt_list"]
        if LMT_list == []:
            continue
        # Convert string dates to datetime objects
        ERT_list = [datetime.strptime(date[:10], "%Y-%m-%d") for date in ERT_list]
        LMT_list = [datetime.strptime(date[:10], "%Y-%m-%d") for date in LMT_list]

        # Sort the lists
        ERT_list.sort()
        LMT_list.sort()
        ert_time_interval = calculate_average_interval(ERT_list)
        negative_threshold_percent = 0.1
        positive_threshold_percent = 0.9
        total_match_count = 0
        match_count = 0
        for LMT in LMT_list:
            # Check if there's an ERT nearby within 30 days
            nearby_ERTs = [ERT for ERT in ERT_list if is_nearby(LMT, ERT)]
            if nearby_ERTs:
                total_match_count += 1
                match_count += 1
            else:
                # Check if this LMT is between two ERTs with a gap indicating possible missing data
                for i in range(len(ERT_list) - 1):
                    if ERT_list[i] < LMT < ERT_list[i + 1]:
                        if (ERT_list[i + 1] - ERT_list[i]).days >= 2 * ert_time_interval:
                            match_count += 1
                        break
        suitable_flag = True
        if total_match_count <= positive_threshold_percent * len(LMT_list):
            suitable_flag = False
        if (len(LMT_list) - match_count) >= negative_threshold_percent * len(LMT_list):
            suitable_flag = False
        score_dict[product] = {
            "LMT_num": len(LMT_list),
            "ERT_num": len(ERT_list),
            "total_match_count": total_match_count,
            "match_count": match_count,
            "is_suitable": suitable_flag,
            "ERT_interval": ert_time_interval
        }
    return score_dict


def url_analysis_for_no_version_sample(sample_path, url_dict_path):
    url_dict = {}
    with open(sample_path, 'r',
              encoding='utf-8') as f:  # , open(filter_path_matched, 'w', encoding='utf-8') as g, open(filter_path_unmatched, 'w', encoding='utf-8') as h
        for line in f:
            json_line = json.loads(line)
            sample_lmt = json_line["lmt"]
            newest_url = json_line["lmt_url"]
            value = json_line["lmt_list"]
            index = json_line["index"]
            model = json_line["model"]
            for lmt, data in value.items():
                lmt_day = lmt.split(' ')[0]
                # url_lmt = url + '@' + lmt_day

                for url in data:
                    if url in newest_url:
                        newest_flag = True
                    else:
                        newest_flag = False
                    if '=' in url:
                        url = url.split('=')[0]
                    url_lmt = url + '@' + lmt
                    if url not in url_dict.keys():
                        url_dict[url] = {"url_appear_time": 0, "appear_time_list": [], "url_lmt_dict": {}}
                        url_dict[url]["url_lmt_dict"][url_lmt] = {"appear_time": 1, "newest_time": 0, "data_info": [
                            {"newest_flag": newest_flag, "sample_lmt_dict": sample_lmt, "index": index}]}

                    else:
                        if url_lmt not in url_dict[url]["url_lmt_dict"].keys():
                            url_dict[url]["url_lmt_dict"][url_lmt] = {"appear_time": 1, "newest_time": 0, "data_info": [
                                {"newest_flag": newest_flag, "sample_lmt_dict": sample_lmt, "index": index}]}
                        else:
                            url_dict[url]["url_lmt_dict"][url_lmt]["appear_time"] += 1
                            url_dict[url]["url_lmt_dict"][url_lmt]["data_info"].append(
                                {"newest_flag": newest_flag, "sample_lmt_dict": sample_lmt, "index": index})
                    if newest_flag:
                        url_dict[url]["url_lmt_dict"][url_lmt]["newest_time"] += 1

        for url, ddict in url_dict.items():
            lmt_dict = ddict["url_lmt_dict"]
            sorted_lmt_dict = dict(sorted(lmt_dict.items(), key=lambda item: item[1]['appear_time']))
            url_dict[url]["url_lmt_dict"] = sorted_lmt_dict
            count = 0
            for lmt_url, value in url_dict[url]["url_lmt_dict"].items():
                count += value["appear_time"]
                url_dict[url]["appear_time_list"].append(value["appear_time"])
            url_dict[url]["url_appear_time"] = count

        sorted_url_dict = dict(sorted(url_dict.items(), key=lambda item: item[1]['url_appear_time'], reverse=True))
        with open(url_dict_path, 'w', encoding='utf-8') as f:
            f.write(json.dumps(sorted_url_dict, ensure_ascii=False, indent=4))


def url_match_analysis(lmt_sample_path, ert_folder, result_path, lmt_flag=False):
    count = 0
    brand = os.path.basename(lmt_sample_path)
    if brand == 'synology_path_info':
        brand = 'synology'
    excel_path = f'ert_lmt_data_excel/{brand}_ert_data.xlsx'
    data = pd.read_excel(excel_path)
    data["ert"] = data["ert"].apply(lambda x: x[:10])
    group_count = data['group'].nunique()

    with open(lmt_sample_path, 'r', encoding='utf-8') as f:
        total_lines = sum(1 for _ in f)
    with open(lmt_sample_path, 'r', encoding='utf-8') as f:
        url_dict = {}
        for line in tqdm(f, total=total_lines, desc="reading lmt sample"):
            j_line = json.loads(line)
            model = j_line["model"]

            brand = j_line["brand"]
            interval = time_dict[brand]
            index = j_line["index"]
            try:
                lmt_dict = j_line["lmt_list"]
            except KeyError:
                continue
            version = j_line['version']
            model, version = process_brand_product(brand, model, version)
            ert_list, match_ert_model_dict = get_ert_list_from_model_ert_list(brand, model, ert_folder)
            if len(ert_list) == 0:
                continue
            for lmt, data_info in lmt_dict.items():
                for url in data_info:

                    url = process_url(url)
                    if lmt_flag:
                        url = url + '@' + lmt
                    match_ert_list = match_version(lmt, ert_list, interval)
                    if len(match_ert_list) > 0:
                        match_flag = True
                    else:
                        match_flag = False
                    if url not in url_dict.keys():
                        url_dict[url] = {}
                        url_dict[url]['count'] = 1
                        url_dict[url]["match_list"] = [{"version": version, "match_flag": match_flag, "match_list": match_ert_list, "sample_index": index}]
                    else:
                        url_dict[url]['count'] += 1
                        url_dict[url]["match_list"].append({"version": version, "match_flag": match_flag, "match_list": match_ert_list, "sample_index": index})
            count += 1
    new_url_dict = {}
    for url, value in url_dict.items():
        url_dict[url]['count'] = [value["count"], count, value["count"] / count]
        match_count = 0
        for item in value["match_list"]:
            if item["match_flag"]:
                match_count += 1
        url_dict[url]['match_count'] = [match_count, len(value["match_list"]), match_count / len(value["match_list"])]
        if url_dict[url]['count'][2] >= 0.1 and url_dict[url]['match_count'][2] >= 0.75:
            new_url_dict[url] = url_dict[url]

    new_url_dict = dict(sorted(new_url_dict.items(), key=lambda item: item[1]['match_count'][2], reverse=True))
    url_dict = dict(sorted(url_dict.items(), key=lambda item: item[1]['match_count'][2], reverse=True))
    with open(result_path, 'w', encoding='utf-8') as g:
        g.write(json.dumps(url_dict, ensure_ascii=False, indent=4))
    with open(result_path + '_filtered', 'w', encoding='utf-8') as gg:
        gg.write(json.dumps(new_url_dict, ensure_ascii=False, indent=4))


def url_match_analysis_by_product(lmt_sample_path, ert_folder, result_path, lmt_flag=False):
    brand = os.path.basename(lmt_sample_path)
    group_sample_dict = get_group_dict(brand, lmt_sample_path, ert_folder)
    brand_time_interval = time_dict[brand]

    for group, value in tqdm(group_sample_dict.items(), desc='processing_group'):
        if group == -1:
            continue
        url_dict = {}
        count = 0
        group_ert_interval = np.mean(value["ert_interval_list"])
        final_interval = min(brand_time_interval, 0.5*group_ert_interval)
        final_interval = max(final_interval, 2*24*60*60)
        for index, lmt_dict_list in enumerate(value["sample_url_dict_list"]):
            if lmt_dict_list == []:
                continue
            for lmt_dict in lmt_dict_list:
                if lmt_dict == {}:
                    continue
                for lmt, data_info in lmt_dict.items():
                    for url in data_info:
                        url = process_url(url)
                        if lmt_flag:
                            url = url + '@' + lmt
                        match_ert_list = match_version(lmt, value["ert_list_list"][index], final_interval)
                        if len(match_ert_list) > 0:
                            match_flag = True
                        else:
                            match_flag = False
                        if url not in url_dict.keys():
                            url_dict[url] = {}
                            url_dict[url]['count'] = 1
                            url_dict[url]["match_list"] = [
                                {"match_flag": match_flag, "match_list": match_ert_list,
                                 "sample_index": index}]
                        else:
                            url_dict[url]['count'] += 1
                            url_dict[url]["match_list"].append(
                                {"match_flag": match_flag, "match_list": match_ert_list,
                                 "sample_index": index})
                count += 1

        new_url_dict = {}
        for url, value in url_dict.items():
            url_dict[url]['count'] = [value["count"], count, value["count"] / count]
            match_count = 0
            for item in value["match_list"]:
                if item["match_flag"]:
                    match_count += 1
            url_dict[url]['match_count'] = [match_count, len(value["match_list"]),
                                            match_count / len(value["match_list"])]
            if url_dict[url]['count'][2] >= 0.1 and url_dict[url]['match_count'][2] >= 0.75:
                new_url_dict[url] = url_dict[url]
        # 排序

        new_url_dict = dict(sorted(new_url_dict.items(), key=lambda item: item[1]['match_count'][2], reverse=True))
        url_dict = dict(sorted(url_dict.items(), key=lambda item: item[1]['match_count'][2], reverse=True))
        with open(result_path + '_' + str(group), 'w', encoding='utf-8') as g:
            g.write(json.dumps(url_dict, ensure_ascii=False, indent=4))
        with open(result_path + '_' + str(group) + '_filtered', 'w', encoding='utf-8') as gg:
            gg.write(json.dumps(new_url_dict, ensure_ascii=False, indent=4))


def get_group_dict(brand, lmt_sample_path, ert_folder):
    ert_path = os.path.join(ert_folder, brand)
    excel_path = f'ert_lmt_data_excel/{brand}_ert_data.xlsx'
    data = pd.read_excel(excel_path)
    # data["ert"] = data["ert"].apply(lambda x: x[:10])
    group_count = data['group'].nunique()

    url_analysis_sample_path = f'F:/paper/paper_gu/firmware_version_identification/match_module/middle_data_restore/sample_for_url_analysis/{brand}'
    ert_data_dict = get_product_ERT(brand, ert_path)
    data_dict = get_product_time_info(ert_data_dict, lmt_sample_path)
    data_dict = get_product_time_info(data_dict, url_analysis_sample_path)

    group_sample_dict = {}
    # group_dict = {"ert_interval_list": [], "sample_url_dict_list": [], "ert_list_list": [], "model_list": []}
    for model in tqdm(data_dict.keys(), desc='generate_group_dict'):
        try:
            index = data[data['model'] == model].index[0]
            data_dict[model]["group"] = data.loc[index, "group"]
        except IndexError:
            data_dict[model]["group"] = -1
        # 获取对应的ert版本列表
        # ert_list, match_ert_model_dict = get_ert_list_from_model_ert_list(brand, model, ert_folder)
        # data_dict[model]["ert_list"] = [datetime.strptime(date[:10], "%Y-%m-%d") for date in data_dict[model]["ert_list"]]
        # LMT_list = [datetime.strptime(date[:10], "%Y-%m-%d") for date in LMT_list]
        # 计算ert的平均时间间隔
        interval = calculate_average_interval(data_dict[model]["ert_list"])
        data_dict[model]["ert_interval"] = interval

        if data_dict[model]["group"] not in group_sample_dict.keys():
            group_sample_dict[data_dict[model]["group"]] = {"ert_interval_list": [], "sample_url_dict_list": [],
                                                              "lmt_model_list": [], "ert_list_list": [],
                                                              "ert_model_list": []}
        # if data_dict["model"]["ert_list"] != []:
        group_sample_dict[data_dict[model]["group"]]["ert_interval_list"].append(interval)
        group_sample_dict[data_dict[model]["group"]]["ert_list_list"].append(data_dict[model]["ert_list"])
        group_sample_dict[data_dict[model]["group"]]["ert_model_list"].append(model)
        # if data_dict[model]["sample_lmt_dict_list"] != []:
        group_sample_dict[data_dict[model]["group"]]["sample_url_dict_list"].append(data_dict[model]["sample_lmt_dict_list"])
        group_sample_dict[data_dict[model]["group"]]["lmt_model_list"].append(model)

    return group_sample_dict


def match_version(lmt, ERT_list, interval, list_flag=False):
    match_list = []
    ert_index_max = len(ERT_list)
    flag_match = False
    current_ert_index = search_first_ert(lmt, ERT_list, list_flag=True)
    if current_ert_index != None:
        if list_flag:
            while parse_time(ERT_list[current_ert_index]) - parse_time(lmt) <= interval:
                ert = ERT_list[current_ert_index]
                flag_match = True
                match_list.append(ert)  ### 保存对应的ERT和版本
                current_ert_index += 1
                if current_ert_index == ert_index_max:
                    break
        else:
            while parse_time(ERT_list[current_ert_index][1]) - parse_time(lmt) <= interval:
                ert = ERT_list[current_ert_index][1]
                flag_match = True
                match_list.append([ert, ERT_list[current_ert_index][0]])
                current_ert_index += 1
                if current_ert_index == ert_index_max:
                    break
    return match_list


def post_process_url_analysis(url_result_path, sample_path, result_path):
    time_format = "%Y-%m-%d %H-%M-%S"
    new_url_dict = {}
    with open(url_result_path, 'r', encoding='utf-8') as f:
        url_dict = json.load(f)
        for url, value in url_dict.items():
            if value['match_count'][2] >= 0.95:
                new_url_dict[url] = value
            elif 0.95 > value['match_count'][2] >= 0.85 and value['count'][2] >= 0.1:
                new_url_dict[url] = value
    new_url_dict = dict(sorted(new_url_dict.items(), key=lambda item: item[1]['match_count'][2], reverse=True))

    for url, value in new_url_dict.items():
        new_url_dict[url]["newest_count"] = [0, 0, 0]
    no_newest_sample_count = 0
    sample_count = 0
    with open(sample_path, 'r', encoding='utf-8') as ff:
        for line in ff:
            sample_count += 1
            newest_time = datetime.strptime('1970-01-01 00-00-00', time_format)
            newest_url = ''
            j_line = json.loads(line)
            try:
                lmt_list = j_line["lmt_list"]
            except KeyError:
                continue

            for lmt, url_list in lmt_list.items():
                for url in url_list:
                    url = url.split('=')[0]
                    if url in new_url_dict.keys():
                        new_url_dict[url]['newest_count'][1] += 1
                        if datetime.strptime(lmt, time_format) > newest_time:
                            newest_time = datetime.strptime(lmt, time_format)
                            newest_url = url
            if newest_url != '':
                new_url_dict[newest_url]['newest_count'][0] += 1
            else:
                # print('no newest url')
                no_newest_sample_count += 1
    with open(result_path, 'w', encoding='utf-8') as g:
        g.write(json.dumps(new_url_dict, indent=4, ensure_ascii=False))
    print(f'no newest sample count: {no_newest_sample_count}')
    print(f'sample_count: {sample_count}')


def check_model_lmt(sample_path, result_path, model_name):
    with open(sample_path, 'r', encoding='utf-8') as f, open(result_path, 'w', encoding='utf-8') as g:
        for line in f:
            j_line = json.loads(line)
            brand = j_line['brand']
            model = j_line['model']
            index = j_line['index']
            lmt = j_line['lmt']
            model, v = process_brand_product(brand, model, '')
            if model == model_name:
                lmt_new = re_extract_lmt_in_url(j_line)
                j_line["lmt_new"] = lmt_new
                g.write(json.dumps(j_line, ensure_ascii=False) + '\n')
                if lmt == lmt_new:
                    print(index)


def calcul_model_sim_for_none_group_data(model_group, lmt_model, cutoff=0.5):

    model_list = model_group.keys()

    similar_models = [model for model in model_list if lmt_model in model or model in lmt_model]

    if similar_models:
        group_list = [model_group[model] for model in similar_models]
        return max(group_list, key=group_list.count)

    # best_model = None
    # best_score = 0
    # for model in model_list:
    #     score = ngram_similarity(lmt_model, model, n=3)
    #     if score > best_score:
    #         best_score = score
    #         best_model = model
    # if best_model:
    #     return model_group[best_model]
    # return -1

    #  difflib
    # close_matches = difflib.get_close_matches(lmt_model, model_list, n=3, cutoff=0.5)
    # if close_matches:
    #     group_list = [model_group[model] for model in close_matches]
    #     return max(group_list, key=group_list.count)
    # return -1

    similarity_scores = []
    for model in model_list:
        if len(lmt_model.split(' ') ) == 1:
            # difflib.SequenceMatcher
            ratio = difflib.SequenceMatcher(None, lmt_model, model.split(' ')[0].split('@')[0]).ratio()
        else:
            ratio = difflib.SequenceMatcher(None, lmt_model, model).ratio()
        if ratio >= cutoff:
            similarity_scores.append((model, ratio))
        # similarity_scores.append((model, ratio))
    if not similarity_scores:
        return '-1'
    similarity_scores.sort(key=lambda x: x[1], reverse=True)
    top_models = [model_group[model] for model, score in similarity_scores[:5]]
    group_counts = Counter(top_models)
    most_common_groups = group_counts.most_common()
    return most_common_groups[0][0]


def find_most_similar_model(lmt_model, ERT_list):
    distances = [(model, levenshtein_distance(lmt_model, model)) for model in ERT_list]
    return min(distances, key=lambda x: x[1])

# n-gram
def ngram_similarity(str1, str2, n=3):
    ngrams1 = list(ngrams(str1, n))
    ngrams2 = list(ngrams(str2, n))
    intersection = len(set(ngrams1) & set(ngrams2))
    union = len(set(ngrams1) | set(ngrams2))
    return intersection / union if union != 0 else 0


def suitable_analysis_by_cluster(lmt_list, ert_list, interval):

    for lmt in lmt_list:
        match_list = match_version(lmt, ert_list, interval, list_flag=True)
        if len(match_list) != 0:
            return True
    return False


def false_ratio_count(bool_list):
    false_count = bool_list.count(False)
    total_count = len(bool_list)
    false_ratio = false_count / total_count
    return false_ratio

def url_match_analysis_by_group(group_lmt_sample_path, group_ert_path, result_path):
    result_dict = {}
    brand = os.path.basename(group_lmt_sample_path)
    if '_temp' in brand:
        brand = brand.split('_temp')[0]
    with open(group_lmt_sample_path, 'r', encoding='utf-8') as f:
        group_lmt_dict = json.load(f)
    with open(group_ert_path, 'r', encoding='utf-8') as f:
        group_ert_dict = json.load(f)
    brand_time_interval = time_dict[brand]
    unsuitable_model_list = []
    for group, value in tqdm(group_lmt_dict.items(), desc='processing_group'):
        if group == '-1':
            continue
        url_dict = {}
        count = 0
        group_ert_interval = calculate_average_interval(list(group_ert_dict[group].keys()))
        final_interval = min(brand_time_interval, group_ert_interval)
        final_interval = max(final_interval, 2*24*60*60)
        print("group:", group)
        print(f"group_ert_interval:{group_ert_interval/24/60/60}, brand_time_interval:{brand_time_interval/24/60/60}, final_interval:{final_interval/24/60/60}")
        group_suit_dict = {}
        for model, value_ in value.items():
            group_suit_dict[model] = []
            lmt_info = value_['sample']
            ert_list = list(value_['ERT_list'].keys())
            if ert_list == []:
                ert_list = list(group_ert_dict[group].keys())
            for item in lmt_info:
                lmt_dict = item['lmt_dict']
                lmt_list = list(lmt_dict.keys())
                group_suit_dict[model].append(suitable_analysis_by_cluster(lmt_list, ert_list, final_interval))
        group_result_record = {"model_list":[], "flag":[]}
        for model, suit_list in group_suit_dict.items():
            if model in ['go-rt-n150']:
                unsuitable_model_list.append(model)
            else:
                if len(suit_list) > 8:
                    if false_ratio_count(suit_list) > 0.8:
                        unsuitable_model_list.append(model)
                    else:
                        pass
                else:
                    if false_ratio_count(suit_list) != 0:
                        group_result_record["model_list"].append(model)
                        group_result_record["flag"] += suit_list

        if len(group_result_record["model_list"]) >= 6 and false_ratio_count(group_result_record["flag"]) > 0.8:
            unsuitable_model_list += group_result_record["model_list"]

        # url analysis
        for model, value_ in value.items():
            # if model in unsuitable_model_list:
            #     continue

            lmt_info = value_['sample']
            ert_list = list(value_['ERT_list'].keys())
            if ert_list == []:
                ert_list = list(group_ert_dict[group].keys())
            for item in lmt_info:

                lmt_newest = item['lmt']
                lmt_dict = item['lmt_dict']
                if lmt_dict!={}:
                    count += 1
                lmt_list = list(lmt_dict.keys())
                index = item['index']
                inter = calculate_average_interval(lmt_list)
                # if inter < 3*24*60*60:
                #     continue
                for lmt, data_info in lmt_dict.items():
                    for url in data_info:
                        url_init = process_url(url)
                        # if lmt_flag:
                        url = url_init + '@' + lmt
                        match_ert_list = match_version(lmt, ert_list, final_interval, list_flag=True)
                        if len(match_ert_list) > 0:
                            match_flag = True
                        else:
                            match_flag = False
                        if lmt == lmt_newest:
                            newest_flag = True
                        else:
                            newest_flag = False
                        if url_init not in url_dict.keys():
                            url_dict[url_init] = {"count": 0, "match_count": 0, "newest_count": 0, "with_lmt": {}}
                        url_dict[url_init]['count'] += 1
                        if url not in url_dict[url_init]['with_lmt'].keys():
                            url_dict[url_init]['with_lmt'][url] = {"count": 0, "match_count": 0, "newest_count": 0, "sample": []}
                        url_dict[url_init]['with_lmt'][url]['count'] += 1
                        if match_flag:
                            url_dict[url_init]['with_lmt'][url]['match_count'] += 1
                            url_dict[url_init]['match_count'] += 1
                        if newest_flag:
                            url_dict[url_init]["with_lmt"][url]["newest_count"] += 1
                            url_dict[url_init]["newest_count"] += 1
                        url_dict[url_init]["with_lmt"][url]["sample"].append({"match_flag": match_flag, "newest_flag": newest_flag,  "match_list": match_ert_list, "sample_index": index, "model": model})

        new_url_dict = {}
        for url, value in url_dict.items():
            for lmt_url, sample_info in value["with_lmt"].items():
                url_dict[url]["with_lmt"][lmt_url]['newest_count'] = [sample_info["newest_count"], sample_info["match_count"],
                                                                      sample_info["newest_count"] / (sample_info[
                                                                          "match_count"]+0.0000001)]
                url_dict[url]["with_lmt"][lmt_url]['match_count'] = [sample_info["match_count"], sample_info["count"], sample_info["match_count"] / sample_info["count"]]
                url_dict[url]["with_lmt"][lmt_url]['count'] = [sample_info["count"], value["count"],
                                                               sample_info["count"] / value["count"]]

            url_dict[url]['newest_count'] = [value["newest_count"], value["match_count"], value["newest_count"] / (value["match_count"]+0.0000001)]
            url_dict[url]['match_count'] = [value["match_count"], value["count"], value["match_count"] / value["count"]]
            url_dict[url]['count'] = [value["count"], count, value["count"] / count]
            # if url_dict[url]['count'][2] >= 0.1 and url_dict[url]['match_count'][2] >= 0.75:
            #     new_url_dict[url] = url_dict[url]

        # new_url_dict = dict(sorted(new_url_dict.items(), key=lambda item: item[1]['match_count'][2], reverse=True))
        url_dict = dict(sorted(url_dict.items(), key=lambda item: item[1]['match_count'][2], reverse=True))
        result_dict[group] = {"interval": {"final_interval": final_interval/24/60/60, "brand_interval": brand_time_interval/24/60/60, "ert_interval": group_ert_interval/24/60/60}, "url_info": url_dict}
    print("unsuitable models: ", unsuitable_model_list)
    with open(result_path.replace(brand, f'unsuitable_model_record/{brand}'), 'w', encoding='utf-8') as f:
        f.write(json.dumps(unsuitable_model_list, ensure_ascii=False, indent=4))
    with open(result_path, 'w', encoding='utf-8') as g:
        g.write(json.dumps(result_dict, ensure_ascii=False, indent=4))
        # with open(result_path + '_' + str(group) + '_filtered', 'w', encoding='utf-8') as gg:
        #     gg.write(json.dumps(new_url_dict, ensure_ascii=False, indent=4))



if __name__ == "__main__":

    brand = 'cisco'
    group_lmt_sample_path = f'sample_for_url_analysis/grouped_lmt_sample/{brand}'
    group_ert_path = f'sample_for_url_analysis/grouped_ert_sample/{brand}'
    result_path = f'url_analysis_result_by_group_0925/{brand}'
    url_match_analysis_by_group(group_lmt_sample_path, group_ert_path, result_path)

    brand = 'zyxel'
    url_analysis_path = f'sample_for_url_analysis/{brand}'
    url_dict_path = f'url_analysis/url_analysis_sample_url_dict_{brand}_0506'
    # url_analysis_for_no_version_sample(url_analysis_path, url_dict_path)

    # brand_list = ['avm', 'synology_path_info', 'hikvision', "d-link", 'cisco', 'dahua', 'zyxel', 'mikrotik', 'reolink',
    #               'tp-link', 'hp', 'huawei']
    # for brand in tqdm(brand_list, desc='processing brand list....\n'):
    #     print(brand)
    #     ert_folder = 'cluster_source/model_ert_list_cluster_new_0506/'
    #     lmt_path = f'final_match_sample/yangben_for_model_match_0909/{brand}'
    #     if brand in ['cisco']:
    #         lmt_path = f'sample_for_url_analysis/{brand}'
    #     result_path = f'url_analysis/all_url_match_case_{brand}'
    #     # url_match_analysis(lmt_path, ert_folder, result_path, True)
    #     url_match_analysis_by_product(lmt_path, ert_folder, result_path, lmt_flag=False)

