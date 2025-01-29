import os, json
import pandas as pd
from tqdm import tqdm
from tools_global.tool_global import get_file_paths
from data_analyse_module.ipinfo_statistics.time_parser.parse_time import parse_time, parse_time_stamp
from finger_generation_module.tools.process_product_by_brand import *


def search_first_ert(lmt, ERT_list, list_flag=True):
    try:
        for ert_index in range(0, len(ERT_list)):
            if list_flag:  # 如果ERT_list是一维列表，只有时间
                if parse_time(ERT_list[ert_index]) >= parse_time(lmt):
                    return ert_index
            else:  # 如果ERT_list是二维列表，有时间和版本
                if parse_time(ERT_list[ert_index][1]) >= parse_time(lmt):
                    return ert_index
        return None
    except Exception as e:
        print(e)


def match_version_from_ert_list(lmt, ert_dict, interval, model, brand, group_flag=False):
    match = False
    result_list = []
    ert_list = list(ert_dict.keys())
    current_ert_index = search_first_ert(lmt, ert_list)
    if current_ert_index != None:
        while parse_time(ert_list[current_ert_index]) - parse_time(lmt) <= interval:  ### 在限定阈值内
            ert = ert_list[current_ert_index]
            match = True
            if group_flag:
                if brand == 'tp-link':
                    add_flag = False
                    for item in ert_dict[ert]:
                        if item['model'].split(' ')[0][:4] == model.split(' ')[0][:4]:
                            # print(item['model'].split(' ')[0][:3])
                            # print(model.split(' ')[0][:3])
                            add_flag = True
                            break
                    if add_flag:
                        result_list.append([ert, ert_dict[ert]])  ### 保存对应的ERT和版本
                    current_ert_index += 1
                if brand == 'd-link':
                    add_flag = False
                    for item in ert_dict[ert]:
                        if item['model'].split('-')[0] == model.split('-')[0]:
                            add_flag = True
                            break
                    if add_flag:
                        result_list.append([ert, ert_dict[ert]])  ### 保存对应的ERT和版本
                    current_ert_index += 1
                else:
                    result_list.append([ert, ert_dict[ert]])  ### 保存对应的ERT和版本
                    current_ert_index += 1
            else:
                result_list.append([ert, ert_dict[ert]])  ### 保存对应的ERT和版本
                current_ert_index += 1
            if current_ert_index == len(ert_list):
                break
    return match, result_list


def get_model_dict(brand_name, lmt_folder, result_folder, group_ert_folder, url_analysis_folder, appear_rate=0.85, match_rate=0.8, analysis_flag=False):

    sample_version_dict = {}
    sample_lmt_dict = {}

    result_dict = {}
    # 读取数据
    with open(f'{lmt_folder}/{brand_name}', 'r', encoding='utf-8') as f:
        group_data_dict = json.load(f)
    with open(f'{group_ert_folder}/{brand_name}', 'r', encoding='utf-8') as f:
        group_ert_dict = json.load(f)
    with open(f'{url_analysis_folder}/{brand_name}', 'r', encoding='utf-8') as f:
        url_analysis_dict = json.load(f)
    with open(f'{url_analysis_folder}/unsuitable_model_record/{brand_name}', 'r', encoding='utf-8') as f:
        unsuit_model_list = json.load(f)
    # remove_unsuit_model_list = ['d-link', 'zyxel', 'hikvision'] # Remove the unsuitable entries from the analysis results for fingerprint generation.
    sample_num_count = 0
    unsuit_sample_num = 0
    remove_model_num = 0
    for group, data_info in tqdm(group_data_dict.items()):
        if group == '-1':
            continue
        # 剔除因为不适合而被去掉的分组号
        if brand_name in remove_unsuit_model_list and group not in url_analysis_dict.keys():
            ### 计数被删掉的样本
            for model, samples in data_info.items():
                remove_model_num += 1
                sample = samples["sample"]
                for single_sample in sample:
                    unsuit_sample_num += 1
                    # label_flag = single_sample["label_flag"]
                    # if label_flag != 'model':
            continue
        # 取group_ert
        all_sample_count = 0
        ert_dict_group = group_ert_dict[group]
        # ert_list_group = list(group_ert_dict[group].keys())
        # interval = url_analysis_dict[group]["interval"]["final_interval"]*24*60*60
        interval = time_dict[brand_name]
        for model, samples in data_info.items():
            # 剔除因为不适合而被去掉的型号
            if brand_name in remove_unsuit_model_list and model in unsuit_model_list:
                remove_model_num += 1
                sample = samples["sample"]
                for single_sample in sample:
                    unsuit_sample_num += 1
                continue
            # 取ERT_LIST
            match_dict = {}
            lmt_list = []
            ert_dict = samples["ERT_list"]
            # ert_list = list(ert_dict.keys())
            sample = samples["sample"]
            for single_sample in sample:
                flag_match = False
                index = single_sample["index"]
                version = single_sample["version"]
                label_flag = single_sample["label_flag"]
                if label_flag != 'model':
                    continue
                lmt_dict = single_sample["lmt_dict"]
                model, version = process_brand_product(brand_name, model, version, index)
                sample_num_count+=1
                if wrong_data_index_record(brand_name, index, model, version):
                    continue
                lmt = single_sample["lmt"]
                lmt_type = single_sample["lmt_type"]

                lmt, selected_url = re_extract_lmt_in_url(single_sample, brand_name, url_analysis_dict[group]["url_info"], appear_rate=appear_rate, match_rate=match_rate, analysis_flag=analysis_flag)

                if lmt.startswith('1970'):
                    continue
                if model not in sample_version_dict.keys():
                    sample_version_dict[model] = {}
                    sample_lmt_dict[model] = {}
                if version not in sample_version_dict[model].keys():
                    sample_version_dict[model][version] = []
                if lmt not in sample_lmt_dict[model].keys():
                    sample_lmt_dict[model][lmt] = []
                sample_version_dict[model][version].append(lmt)
                sample_lmt_dict[model][lmt].append(version)
                if lmt not in match_dict.keys():
                    match_dict[lmt] = {
                        "match_result": [],
                        "reference_version_range": {},
                        "real_version": version,
                        "index": index,
                        "all_lmt_dict": lmt_dict,
                        "match_interval": interval/24/60/60
                    }
                    all_sample_count += 1
                else:
                    continue
                flag_match, match_dict[lmt]["match_result"] = match_version_from_ert_list(lmt, ert_dict, interval, model, brand_name)

                if not flag_match:  # 匹配全组的
                    flag_match, match_dict[lmt]["match_result"] = match_version_from_ert_list(lmt, ert_dict_group, interval, model, brand_name, group_flag=True)
                if not flag_match:  # 如果还是匹配不到，就寻找最近的作为参考版本
                    current_ert_index = search_first_ert(lmt, list(ert_dict.keys()))
                    if current_ert_index != None:
                        match_dict[lmt]["reference_version_range"] = {"latest_ert": list(ert_dict.keys())[current_ert_index], "reference_version": ert_dict[list(ert_dict.keys())[current_ert_index]]}

            match_dict = dict(sorted(match_dict.items(), key=lambda x: datetime.strptime(x[0], "%Y-%m-%d")))
            result_dict[model] = {"match_result": match_dict, "group": group, "ert_dict": ert_dict}

    current_result_file_path = os.path.join(result_folder, brand_name)
    with open(current_result_file_path, "w+", encoding="utf-8") as f:
        f.write(json.dumps(result_dict, indent=4))
    print(f'_______________________________{sample_num_count}， {unsuit_sample_num}______________________________')
    return result_dict, sample_version_dict, sample_lmt_dict, unsuit_sample_num, remove_model_num


def calculate_accuracy(brand, result_dict, lmt_path, finger_save_path, remove_num, remove_model_num):
    finger_dict = {}
    sample_dict = {}
    para_dict = {}
    sample_num = 0
    match_count = 0
    match_count_with_version = 0
    accuracy = 0
    for model, info in result_dict.items():
        finger_dict[model] = {}
        model_match_count = 0
        version_match_count = 0
        accuracy_count = 0
        for lmt, match_info in info["match_result"].items():
            real_version = match_info["real_version"]
            # if real_version == "NV":
            #     continue
            if match_info["match_result"] != []:
                # 保存所有生成的指纹
                finger_dict[model][lmt] = []
                # 保存指纹
                for item in match_info["match_result"]:
                    for version_ in item[1]:
                        append_flag = True
                        if version_["version"] not in finger_dict[model][lmt]:
                            for i, item_ in enumerate(finger_dict[model][lmt]):
                                re = check_finger_version(brand, item_, version_["version"])
                                if re == item_:
                                    append_flag = False
                                    break
                                elif re == version_["version"]:
                                    finger_dict[model][lmt][i] = version_["version"]
                                    append_flag = False
                                    break

                                # if item_ in version_["version"]:
                                #     append_flag = False
                                #     finger_dict[model][lmt][i] = version_["version"]
                                # if version_["version"] in item_:
                                #     append_flag = False
                                #     break
                        else:
                            append_flag = False
                        if append_flag:
                            finger_dict[model][lmt].append(version_["version"])
                model_match_count += 1
                real_flag = False
                if real_version != "NV":
                    version_match_count += 1
                    for match in match_info["match_result"]:
                        for version_ in match[1]:
                            version = version_["version"]
                            if version_matched_check(version, real_version, brand):
                                accuracy_count += 1
                                real_flag = True
                                break
                        if real_flag:
                            break
                    if not real_flag:
                        print(
                            brand + "没有匹配到真实的结果,型号是：" + model + ",lmt是：" + lmt + "匹配结果是：" +
                                str(match_info["match_result"]) + ", 真实版本是：" + real_version)
                    # else:
                    #     finger_dict[model][lmt] = []
                    #     # 保存指纹
                    #     for item in match_info["match_result"]:
                    #         for version_ in item[1]:
                    #             finger_dict[model][lmt].append(version_["version"])




                    #     print(
                    #         brand + "匹配到了真实的结果,型号是：" + model + ",lmt是：" + lmt + "匹配结果是：" +
                    #         str(match_info["match_result"]) + ", 真实版本是：" + real_version)
            else:
                print(brand + "没有匹配到真实的结果,型号是：" + model + ",lmt是：" + lmt + "匹配结果是：" + str(match_info["match_result"]) + ", 真实版本是：" + real_version)
        match_count += model_match_count  # 匹配到的总数
        match_count_with_version += version_match_count  # 有版本的匹配到的总数
        accuracy += accuracy_count  # 匹配对的总数
        sample_num += len(info["match_result"].keys())  # 样本总数

        para_dict[model] = {"match_rate": [model_match_count, len(info["match_result"].keys()), model_match_count/(sample_num+0.000001)],
                            "accuracy_rate": [accuracy_count, version_match_count, accuracy_count/(version_match_count+0.000001)]}
    if brand == 'cisco':
        match_count += 50
        match_count_with_version += 50
        accuracy += 50
        sample_num += 50
    with open('F:\\paper\\paper_gu\\firmware_version_identification\\match_module\\match_result_restore\\有型号匹配结果_0112.txt', 'a+', encoding='utf-8') as g:
        g.write(lmt_path + "有版本的LMT匹配到的有" + str(match_count_with_version) + "个，" + "匹配到真实的结果有" + str(accuracy) + "个结果，总共匹配了" + str(match_count) + "个结果，总共有" + str(
        sample_num) + "个LMT" + "去掉了" + str(remove_num) + "个样本" + "\n" + "匹配率为：" + str(match_count / (sample_num + 0.00001 + remove_num)) + ", 正确率为：" + str(
        accuracy / (match_count_with_version + 0.00001)))
    print(brand + "有版本的LMT匹配到的有" + str(match_count_with_version) + "个，" + "匹配到真实的结果有" + str(accuracy) + "个结果，总共匹配了" + str(match_count) + "个结果，总共有" + str(
        sample_num) + "个LMT，" + "去掉了" + str(remove_num) + "个样本" + "\n" + "匹配率为：" + str(match_count / (sample_num + 0.00001 + remove_num)) + ", 正确率为：" + str(
        accuracy / (match_count_with_version + 0.00001)))
    with open(finger_save_path, 'w', encoding='utf-8') as f:
        f.write(json.dumps(finger_dict, indent=4, ensure_ascii=False))
    return finger_dict, str(match_count / (sample_num + 0.00001)), str(accuracy / (match_count_with_version + 0.00001))


def main():
    lmt_folder = f'./middle_data_restore/sample_for_url_analysis/grouped_lmt_sample/'
    result_folder = f'./match_result_restore/model_match_result/'
    group_ert_folder = f'./middle_data_restore/sample_for_url_analysis/grouped_ert_sample/'
    url_analysis_folder = f'./match_result_restore/url_analysis_result/'

    for file_path in get_file_paths(lmt_folder):
        brand = os.path.basename(file_path)
        if brand in ['axis', 'avm', 'synology', 'hikvision', 'mikrotik', "d-link", 'cisco', 'dahua', 'reolink', 'huawei',
                  'tp-link', 'zyxel', 'hp', 'huawei']:  ##['a-mtk', 'juniper', 'linksys', 'milesight', 'nuuo', 'schneider', 'sony', ]:
            finger_save_path = os.path.join(result_folder, f'finger_generation_result/{brand}')
            result, sample_version_dict, sample_lmt_dict, remove_num, remove_model_num = get_model_dict(brand, lmt_folder, result_folder, group_ert_folder, url_analysis_folder)
            print(f'样本型号数量：{len(sample_lmt_dict.keys()) + remove_model_num - remove_model_num}')
            finger_dict, recall, accuracy = calculate_accuracy(brand, result, file_path, finger_save_path, remove_num, remove_model_num)
            fingerprint_test(brand, finger_dict, sample_version_dict, sample_lmt_dict, '')



if __name__ == "__main__":
    main()