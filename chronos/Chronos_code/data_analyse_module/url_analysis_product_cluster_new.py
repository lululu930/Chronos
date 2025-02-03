import os.path
import pickle

import numpy as np
import pandas as pd
from scipy.cluster.hierarchy import dendrogram, linkage, fcluster
from scipy.spatial.distance import pdist, squareform
from fastdtw import fastdtw
from scipy.spatial.distance import euclidean
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import matplotlib.pyplot as plt
import seaborn as sns
from tqdm import tqdm
from sklearn.metrics import silhouette_score

from data_analyse_module.url_analysis_cluster_and_plot import cluster_result_visiable_seaborn


def model_name_similarity(models):
    vectorizer = TfidfVectorizer(analyzer='char_wb', ngram_range=(2, 3))  # n-gram
    tfidf_matrix = vectorizer.fit_transform(models)
    cosine_sim = cosine_similarity(tfidf_matrix)
    return cosine_sim


def time_series_similarity(data, load_file):

    # load results
    time_series_dist, unique_models = load_results(load_file)

    if time_series_dist is not None and unique_models is not None:
        return time_series_dist, unique_models
    unique_models = data['model'].unique()
    model_time_series = {}

    for model in tqdm(unique_models, desc='Extracting time series'):
        model_data = data[data['model'] == model]
        # print(model_data['ert'])
        dates = pd.to_datetime(model_data['ert']).sort_values().view('int64').tolist()
        model_time_series[model] = dates

    n = len(unique_models)
    time_series_dist = np.zeros((n, n))

    for i in tqdm(range(n), desc='Calculating DTW distances'):
        for j in range(i + 1, n):
            ts1 = model_time_series[unique_models[i]]
            ts2 = model_time_series[unique_models[j]]

            # DTW
            dist, _ = fastdtw(ts1, ts2, dist=euclidean)

            time_series_dist[i, j] = dist
            time_series_dist[j, i] = dist
    save_results(time_series_dist, unique_models, load_file)
    return time_series_dist, unique_models


def save_results(time_series_dist, unique_models, filename='dtw_results.pkl'):
    with open(filename, 'wb') as f:
        pickle.dump((time_series_dist, unique_models), f)
    print(f'Results saved to {filename}')

def combined_similarity(name_sim, time_series_dist, alpha=0.5):
    time_series_sim = 1 / (1 + time_series_dist)
    combined_sim = alpha * name_sim + (1 - alpha) * time_series_sim
    return combined_sim


def hierarchical_clustering(brand, similarity_matrix, models, dendrogram_file, plot_flag=True):
    np.fill_diagonal(similarity_matrix, 1)
    distance_matrix = 1 - similarity_matrix
    condensed_dist_matrix = squareform(distance_matrix)

    Z = linkage(condensed_dist_matrix, method='average')

    if plot_flag:
        if len(models) > 100:
            plt.figure(figsize=(50, 40))
        else:
            plt.figure(figsize=(30, 20))
        dendrogram(Z, labels=models, orientation='top')
        plt.title(f"Hierarchical Clustering Dendrogram of {brand}", fontsize=60)
        plt.xlabel("Model",  fontsize=60)
        plt.ylabel("Distance", fontsize=60)

        ax = plt.gca()
        ax.set_xticks(ax.get_xticks()[::15])
        ax.set_xticklabels(models[::15], fontsize=40, rotation=90)

        plt.yticks(fontsize=60)
        plt.savefig(dendrogram_file, dpi=300)
        plt.show()

    return Z


def select_optimal_threshold(Z, combined_sim, unique_models, min_d=0.3, max_d=0.9, step=0.1):
    """
    Choose the best threshold -- Silhouette Score。
    """
    best_threshold = min_d
    best_score = -1
    best_clusters = None
    score_list = []
    cluster_info = []
    thre_list = []
    for d in np.arange(min_d, max_d, step):
        clusters = fcluster(Z, d, criterion='distance')
        if len(set(clusters)) > 1:
            score = silhouette_score(combined_sim, clusters)
            thre_list.append(d)
            score_list.append(score)
            cluster_info.append(clusters)
            print(f'Threshold: {d}, Silhouette Score: {score}')
            # if score > best_score:
            #     best_score = score
            #     best_threshold = d
            #     best_clusters = clusters

    # print(f'Best Threshold: {best_threshold}, Best Silhouette Score: {best_score}')
    return thre_list, score_list, cluster_info

def load_results(filename='dtw_results.pkl'):
    try:
        with open(filename, 'rb') as f:
            time_series_dist, unique_models = pickle.load(f)
        print(f'Results loaded from {filename}')
        return time_series_dist, unique_models
    except FileNotFoundError:
        print(f'{filename} not found. Recalculating...')
        return None, None


def cluster_ert_model_main(brand, sample_path, dtw_result, dendrogram_result, cluster_result_fold, best_threshold=None, plot_flag=True, cluster_performance_flag=False):

    # result_path = f'./product_cluster_result/{brand}_ert_data.xlsx'
    if cluster_performance_flag:
        best_threshold = None
    data = pd.read_excel(sample_path)
    data = data.sort_values(by='model')
    models = data['model'].unique()

    # model name feature
    name_sim = model_name_similarity(models)

    # time series feature
    time_series_dist, unique_models = time_series_similarity(data, dtw_result)

    combined_sim = combined_similarity(name_sim, time_series_dist, alpha=0.6)

    # cluster_result_visiable_seaborn(combined_sim, unique_models, 'Synology cluster result visualization', data_df=None, annote_flag=False, label_interval=1)
    # cluster
    Z = hierarchical_clustering(brand, combined_sim, unique_models, dendrogram_result, plot_flag)

    # # cutting
    # best_threshold = 0.8  # change threshold by hand
    if best_threshold is not None:
        best_clusters = fcluster(Z, best_threshold, criterion='distance')
    else:
        # choose the best threshold
        thre_list, score_list , clusters_info_list = select_optimal_threshold(Z, combined_sim, unique_models)
        best_threshold = thre_list[score_list.index(max(score_list))]
        best_clusters = clusters_info_list[score_list.index(max(score_list))]
    if not cluster_performance_flag:
        cluster_df = pd.DataFrame({'Model': unique_models, 'Cluster': best_clusters})
        print(cluster_df)
        th = str(best_threshold).replace('.', '')
        result_path = os.path.join(cluster_result_fold, f'{brand}_ert_data_{th}.xlsx')
        cluster_df.to_excel(result_path, index=False)  # index=False 不保存行索引
        return th
    else:
        return thre_list, score_list , clusters_info_list, unique_models


if __name__ == '__main__':
    brand = 'cisco'
    sample_path = f'./ert_lmt_data_excel/{brand}_ert_data.xlsx'
    dtw_result = f'./product_cluster_result/time_series_dtw_store/{brand}_dtw_results.pkl'
    dendrogram_result = f'./product_cluster_result/dendrogram_file_save/{brand}_dendrogram_result.png'
    cluster_ert_model_main()
