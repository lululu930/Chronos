import os

def get_file_paths(file_path):  # file_path是想要获取的文件夹的路径
    """
    返回文件夹下所有文件，返回值是输入文件夹路径+文件的组合路径。只适用于无子文件夹的情况，否则路径会出错
    """
    files_paths = list()
    for i, j, files_names in os.walk(file_path):
        for file_name in files_names:
            files_paths.append(os.path.join(file_path, file_name))
    return files_paths

def get_file_path_form_folder(file_path):
    """
    获取文件夹下的所有文件，返回文件夹路径+文件名的路径列表，适用于有子文件夹的情况
    """
    path_list = []
    for i, j, files_names in os.walk(file_path):
        for file_name in files_names:
            path_list.append(os.path.join(i, file_name))
    return path_list

def get_subdirectories(folder_path):
    """
    获取文件夹下的所有子文件夹，返回的是子文件夹名列表
    """
    subdirectories = [d for d in os.listdir(folder_path) if os.path.isdir(os.path.join(folder_path, d))]

    return subdirectories



if __name__=='__main__':
    fold_path = 'analysis_data_restore/KEY_WORDS0'
    i = get_subdirectories(fold_path)
    j = get_file_paths(fold_path)
    k = get_file_path_form_folder(fold_path)