import numpy as np
import pandas as pd
from kaldiio import ReadHelper
from sklearn.cluster import KMeans
import pickle
from sklearn.discriminant_analysis import LinearDiscriminantAnalysis as LDA
import sys

def import_xv(dataroot):
    #print(dataroot)
    Lattack, Lid, Lrepr = [], [], []
    with ReadHelper("scp:"+dataroot+f"xvector.scp") as reader:
        for i, (key, numpy_array) in enumerate(reader):
            keys = key.split(' ')[0].split('-')
            Lid.append(int(keys[1]))
            Lattack.append(int(keys[0]))
            Lrepr.append(numpy_array)
    print(f'Data from {dataroot} imported, {len(Lid)} lines loaded.')
    return np.array(Lid), np.array(Lattack), np.array(Lrepr)

def print_stats(labels):
    print("%poison\t%clean\t%total\t#poison\t#clean\t#total")
    print("{:.2f}\t{:.2f}\t{:.2f}\t{:}\t{:}\t{:}".format(
        100*len(labels[labels==12])/len(labels),
        100*len(labels[labels!=12])/len(labels),
        100,
        len(labels[labels==12]),
        len(labels[labels!=12]),
        len(labels)))

def saveas(keep, Lid, filename, root='/export/b17/tthebau1/GARD_DINOrepr_train100/'):
    to_save = [x for _, x in sorted(zip(Lid, keep))]
    with open(f'{root}{filename}', 'wb') as f:
        pickle.dump(to_save, f)
    #print('List saved')

def get_clustering_perfs(clusters, labels, K=500):
    mat=np.zeros((13, K)).astype(int)
    for label, cluster in zip(labels, clusters):
        mat[int(label), int(cluster)]+=1
    mat_2 = mat[:12]
    mat_2[2]+=mat[12]
    #mat is oracle, mat_2 is seen labels
    from_attack, total, clean =0, 0, 0

    for k in range(K):
        arg = np.argmax(mat_2[:,k])
        #arg in [0,11]
        if arg!=2 : from_attack+= mat[12,k]
        total+= mat_2[:,k].sum()-mat_2[arg,k]
        clean+= mat_2[:,k].sum()-mat_2[arg,k] - mat[12,k]

    print("Clusters\t% poison\t% clean\t% removed\t# poison\t#clean\t# removed")
    print(f"{K}\t\t{100*from_attack/mat[12].sum()}\t\t{100*clean/(mat.sum()-mat[12].sum())}\t{100*total/mat.sum()}\t{from_attack}\t{clean}\t{total}")

def get_clustering_indices(clusters, labels, K=500):
    mat=np.zeros((12, K)).astype(int)
    for label, cluster in zip(labels, clusters):
        mat[int(label), int(cluster)]+=1
    to_remove = np.zeros_like(mat)
    for k in range(K):
        arg = np.argmax(mat[:,k])
        if mat[arg,k]>1: 
            to_remove[:,k]+=1 
            to_remove[arg,k]-=1
    
    keeping = np.zeros_like(labels)
    for i, (label, cluster) in enumerate(zip(labels, clusters)):
        if to_remove[int(label), int(cluster)]>0:
            keeping[i]+=1
    print(f"Removing {len(keeping[keeping==1])} out of {len(keeping)} lines")

    return (keeping==0).astype(int)

def project_data_for_second_turn(data, labels, to_keep):
    clean_data = data[to_keep==1]
    projection = LDA().fit(data[to_keep==1], labels[to_keep==1])
    return projection.transform(data)

def suppose_n_classes_attacked(to_keep, labels, n_classes_attacked=1, low_poisoning=False):
    classes = percent_removed_per_class(to_keep, labels)
    if np.max(classes)<0.4 and low_poisoning: return to_keep
    #print(classes)
    classes = [i[0] for i in sorted([(i,c) for (i,c) in enumerate(classes)], key=lambda x:x[1], reverse=True)[:n_classes_attacked]]
    print(f"Attacked classes detected : {str(classes)}")
    new_keep = np.zeros_like(to_keep)
    for i, label in enumerate(labels):
        if label not in classes: new_keep[i]=1
        else: new_keep[i]=to_keep[i]
    return new_keep

def percent_removed_per_class(to_keep, labels):
    classes = np.zeros((len(set(labels))))
    tots =    np.zeros((len(set(labels))))
    for (keep, label) in zip(to_keep, labels):
        classes[label]+= int(1-keep)
        tots[label]+= 1
    return [c/t for c,t in zip(classes, tots)]

def clustering_perf_from_keep(to_keep, oracle_labels):
    from_attack, total, clean =0, 0, 0
    for keep, lab in zip(to_keep, oracle_labels):
        if keep==0:
            total+=1
            if lab==12: from_attack+=1
            else: clean +=1
    print("%poison\t%clean\t%removed\t#poison\t#clean\t#removed")
    print("{:.2f}\t{:.2f}\t{:.2f}\t\t{:}\t{:}\t{:}".format(
        100*from_attack/len(oracle_labels[oracle_labels==12]),
        100*clean/len(oracle_labels[oracle_labels!=12]),
        100*total/len(oracle_labels),
        from_attack,
        clean,
        total))



if __name__=="__main__":
    K = 1000 if len(sys.argv)<2 else int(sys.argv[1])
    classes_attacked = -1 if len(sys.argv)<3 else int(sys.argv[2])
    dataroot = "/home/tthebau1/GARD/DINO_FILTERING/temp/hyperion/egs/poison/dinossl.v1/exp/xvectors/fbank80_stmn_lresnet34_e256_do0_b48_amp.dinossl.v1/poison_full/" if len(sys.argv)<4 else sys.argv[3]+'/'
    save_file = 'data_to_keep_11to5' if len(sys.argv)<5 else sys.argv[4]
    SAVEROOT = '/home/tthebau1/GARD/DINO_FILTERING/lists_to_keep_v2/'
    #print(f"the file will be saved as {save_file}.pkl")
    Lid, Lattack, Lrepr = import_xv(dataroot=dataroot)
    #print(f"total files imported : {Lid.shape}, {Lattack.shape}, {Lrepr.shape}")
    if len(Lid)==0:
        print(f"Error : no xvectors found in {dataroot}")
        exit()

    ### FIRST CLUSTERING ###
    clusters = KMeans(n_clusters=K, n_init='auto').fit_predict(Lrepr)
    print(f"Clustering done for {K} classes")

    ### SMART REMOVAL ###
    percent_removed = suppose_n_classes_attacked(to_keep, Lattack)
    if np.max(percent_removed)<0.4:
        print('Low poisoning detected, will remove all classes.')
        classes_attacked = -1

    #generating list
    to_keep = get_clustering_indices(clusters, Lattack, K=K)

    ### LDA + SECOND CLUSTERING ###
    #projection
    Lproj = project_data_for_second_turn(Lrepr, Lattack, to_keep)
    #Clustering
    clusters = KMeans(n_clusters=K, n_init='auto').fit_predict(Lproj)
    print(f"Second clustering done for {K} classes")
    #generating list
    to_keep_all = get_clustering_indices(clusters, Lattack, K=K)

    ### Saving Eval 6 ###
    saveas(to_keep_all, Lid, filename=f"{save_file}_Eval6.pkl", root=SAVEROOT)

    ### Saving Eval 7 ###
    to_keep_n = suppose_n_classes_attacked(to_keep_all, Lattack, classes_attacked)
    saveas(to_keep_n, Lid, filename=f"{save_file}_Eval7.pkl", root=SAVEROOT)

    ### Saving Eval 8 ###
    if classes_attacked<0: to_keep = to_keep_all
    else: to_keep = to_keep_n
    saveas(to_keep, Lid, filename=f"{save_file}_Eval8v1.pkl", root=SAVEROOT)

    if np.max(percent_removed)>0.7:
        print('High poisoning detected, re-running with K=200.')
        K=200
        ### FIRST CLUSTERING ###
        clusters = KMeans(n_clusters=K, n_init='auto').fit_predict(Lrepr)
        print(f"Clustering done for {K} classes")
        to_keep = get_clustering_indices(clusters, Lattack, K=K)
        ### LDA + SECOND CLUSTERING ###
        #projection
        Lproj = project_data_for_second_turn(Lrepr, Lattack, to_keep)
        #Clustering
        clusters = KMeans(n_clusters=K, n_init='auto').fit_predict(Lproj)
        print(f"Second clustering done for {K} classes")
        #generating list
        to_keep_all = get_clustering_indices(clusters, Lattack, K=K)
        # removing all be 1 class
        to_keep = suppose_n_classes_attacked(to_keep_all, Lattack, classes_attacked)
        saveas(to_keep, Lid, filename=f"{save_file}_Eval8v2.pkl", root=SAVEROOT)

    else:
        saveas(to_keep, Lid, filename=f"{save_file}_Eval8v2.pkl", root=SAVEROOT)
    
    print(f"Final file saved in {save_file}_Eval8v2.pkl")
