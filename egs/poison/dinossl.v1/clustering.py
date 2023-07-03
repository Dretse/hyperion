import numpy as np
import pandas as pd
from kaldiio import ReadHelper
from sklearn.cluster import KMeans
import pickle
from sklearn.discriminant_analysis import LinearDiscriminantAnalysis as LDA
import sys

def import_xv(dataroot):
    print(dataroot)
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
    print('List saved')

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

def suppose_n_classes_attacked(to_keep, labels, n_classes_attacked=1):
    classes = np.zeros((len(set(labels))))
    for (keep, label) in zip(to_keep, labels):
        classes[label]+= int(1-keep)
    classes = [i[0] for i in sorted([(i,c) for (i,c) in enumerate(classes)], key=lambda x:x[1], reverse=True)[:n_classes_attacked]]
    print(f"Attacked classes detected : {str(classes)}")
    new_keep = np.zeros_like(to_keep)
    for i, label in enumerate(labels):
        if label not in classes: new_keep[i]=1
        else: new_keep[i]=to_keep[i]
    return new_keep

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
    reduction=1
    reduce = False if reduction==1 else True
    mesure=False
    print(f"the file will be saved as {save_file}.pkl")
    Lid, Lattack, Lrepr = import_xv(dataroot=dataroot)
    print(f"total files imported : {Lid.shape}, {Lattack.shape}, {Lrepr.shape}")
    if len(Lid)==0:
        print(f"Error : no xvectors found in {dataroot}")
        exit()

    if reduce:
    #Reduce
        rdm_idx = np.arange(Lrepr.shape[0])
        np.random.shuffle(rdm_idx)
        idx = rdm_idx[:int(Lrepr.shape[0]*reduction)]
        #use only 10% of the data
        Lrepr = Lrepr[idx]
        Lattack = Lattack[idx]
        Lid = Lid[idx]
        print(f'Took only {100*reduction}% of the data')
    else: print("Took all the data")

    if mesure:
        #Set poison index
        Loracle = np.copy(Lattack)
        with open('/export/b17/xli257/poison_data_dumps/source11_target5_p10_und/poison_index_train', 'rb') as poison_index_file:
            poison_index = pickle.load(poison_index_file)
            print(poison_index.shape, Lid.shape)
            for idx, id in enumerate(Lid):
                if id in poison_index:
                    Loracle[idx]=12
        print_stats(Loracle)


    clusters = KMeans(n_clusters=K).fit_predict(Lrepr)
    print(f"Clustering done for {K} classes")

    #generating list
    to_keep = get_clustering_indices(clusters, Lattack, K=K)
    #Measure perfs
    if mesure: clustering_perf_from_keep(to_keep, Loracle)

    saveas(to_keep, Lid, filename=save_file+'.pkl', root='/home/tthebau1/GARD/DINO_FILTERING/lists_to_keep_v2/')
    """
    for N in range(1,11):
        #remove 11-N classes
        to_keep1 = suppose_n_classes_attacked(to_keep, Lattack, N)
        #Measure perfs
        clustering_perf_from_keep(to_keep1, Loracle)
    """


    #keep 1 class
    if classes_attacked>0: to_keep = suppose_n_classes_attacked(to_keep, Lattack, classes_attacked)


    #SECOND ROUND
    #projection
    Lproj = project_data_for_second_turn(Lrepr, Lattack, to_keep)
    #Clustering
    clusters = KMeans(n_clusters=K).fit_predict(Lproj)
    print(f"Clustering done for {K} classes")
    #generating list
    to_keep = get_clustering_indices(clusters, Lattack, K=K)
    #Measure perfs
    if mesure: clustering_perf_from_keep(to_keep, Loracle)
    #remove 11-N classes
    if classes_attacked>0: to_keep = suppose_n_classes_attacked(to_keep, Lattack, classes_attacked)
    #Measure perfs
    #clustering_perf_from_keep(to_keep, Loracle)
    #save file
    saveas(to_keep, Lid, filename=save_file+'_LDA.pkl', root='/home/tthebau1/GARD/DINO_FILTERING/lists_to_keep_v2/')
    print(f"Final file saved in {save_file}_LDA.pkl")
