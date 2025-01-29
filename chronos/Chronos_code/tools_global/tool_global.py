import os

def get_file_paths(file_path):
    """
    Return all files in the folder.
    The return value is the combination of the input folder path and the file path.
    This is only applicable to cases without subfolders; otherwise, the path will be incorrect.
    """
    files_paths = list()
    for i, j, files_names in os.walk(file_path):
        for file_name in files_names:
            files_paths.append(os.path.join(file_path, file_name))
    return files_paths

def get_file_path_form_folder(file_path):
    """
    Retrieve all files in the folder and return a list of paths,
    which is the combination of the folder path and file name.
    This is applicable to cases with subfolders.
    """
    path_list = []
    for i, j, files_names in os.walk(file_path):
        for file_name in files_names:
            path_list.append(os.path.join(i, file_name))
    return path_list

def get_subdirectories(folder_path):
    """
    Retrieve all subfolders in the folder and return a list of subfolder names.
    """
    subdirectories = [d for d in os.listdir(folder_path) if os.path.isdir(os.path.join(folder_path, d))]

    return subdirectories



if __name__=='__main__':
    fold_path = 'analysis_data_restore/KEY_WORDS0'
    i = get_subdirectories(fold_path)
    j = get_file_paths(fold_path)
    k = get_file_path_form_folder(fold_path)