import pandas as pd
import numpy as np
import tkinter.filedialog
import matplotlib.pyplot as plt

def lire(path,time_step=0.21):
    df=pd.read_csv(path,sep=',', header=2)
    df=df[['Position X','Position Y', 'Time', 'TrackID']]
    df['Time']=df.Time * time_step
    return df

def traiter(df,recs,n_max,tresh):
    cpt_t=0
    cpt_v=0
    cpt_rec=0
    periods=3
    #300 nm =0.3 um
    stop_value=0.3
    grp=df.groupby('TrackID')
    rsl=[]
    rslt=[]
    rslt2=[]
    rslt_tot=[]
    for track_id in grp.groups:
        indexs=[i for i in grp.groups[track_id]]
        tr=df.T[indexs].T
        sp_ve_lisse=tr.diff(periods=periods).fillna(0.)
        sp_ve=tr.diff().fillna(0.)
        tr['delta'] = np.sqrt(sp_ve['Position X']**2 + sp_ve['Position Y']**2)
        tr['delta_lisse'] = np.sqrt(sp_ve_lisse['Position X']**2 + sp_ve_lisse['Position Y']**2)
        tr['speed']=(tr['delta']/sp_ve.Time).fillna(0.)
        tr['speed_lisse']=(tr['delta_lisse']/sp_ve_lisse.Time).fillna(0.)
        posx=[k for k in tr["Position X"]]
        posy=[k for k in tr["Position Y"]]
        displacement=np.sqrt((posx[0] - posx[-1])**2+(posy[0]-posy[-1])**2)
        track_len=tr['delta'].sum()
        nb_points=len(tr)
        duration=sp_ve['Time'].sum()
        vitesse_max=tr.speed.max()
        vitesse_moyenne=tr.speed.mean()
        vitesse_mediane=tr.speed.median()
        vitesse_max_lisse=tr.speed_lisse.max()
        vitesse_moyenne_lisse=tr.speed_lisse.mean()
        vitesse_mediane_lisse=tr.speed_lisse.median()
        pred=(tr["delta_lisse"] <= stop_value)
        stop_coeff=(len(pred[pred])-periods)/max(1,nb_points-periods)
        mspeed=np.max(tr.speed)
        rslt_tot.append(tr)
        for rec in recs:
            predicat=(tr['Position X'] <= rec['x2']) & (tr['Position Y'] <= rec['y2'])
            predicat=predicat & ((tr['Position X'] >= rec['x1']) & (tr['Position Y'] >= rec['y1']))
            n=len(predicat[predicat])
            if n>n_max:
                tr['Position X'] = tr['Position X'] - list(tr['Position X'])[0]
                tr['Position Y'] = tr['Position Y'] - list(tr['Position Y'])[0]
                a=tr[(tr['Position X']==0.) & (tr['Position Y']==0.)]
                rslt.append(a)
                rslt2.append(tr)
                cpt_rec+=1
                break
        else:
            tr['Position X'] = tr['Position X'] - list(tr['Position X'])[0]
            tr['Position Y'] = tr['Position Y'] - list(tr['Position Y'])[0]
            a=tr[(tr['Position X']==0.) & (tr['Position Y']==0.)]
            if len(tr[tr.speed > mspeed*tresh])>1:
                rslt.append(tr)
                rslt2.append(a)
                row=np.array([track_id,nb_points,duration,vitesse_max,vitesse_max_lisse,vitesse_mediane,vitesse_mediane_lisse,vitesse_moyenne,vitesse_moyenne_lisse,displacement,track_len,stop_coeff])
                rsl.append(row)
            else:
                rslt.append(a)
                rslt2.append(tr)
                cpt_v+=1
        cpt_t+=1
    print(str(100*cpt_v/max(cpt_t,1))+'% enlevés')
    print('dont '+str(100*cpt_rec/max(cpt_t,1)) + '% enlevés par rectangle')
    return rsl, rslt,rslt_tot, rslt2

def afficher(rslt,rslt_tot, rslt2,save_path,manual,xlim,ylim):
    plt.figure()
    if manual:
        plt.xlim(xlim)
        plt.ylim(ylim)
    for rsl in rslt_tot:
        X,Y=rsl['Position X'],rsl['Position Y']
        plt.plot(X,Y)
    plt.savefig(save_path+"_depart.jpg")
    xl=plt.xlim()
    yl=plt.ylim()
    
    plt.figure()
    plt.ylim(yl)
    plt.xlim(xl)
    for rsl in rslt2:
        X,Y=rsl['Position X'],rsl['Position Y']
        plt.plot(X,Y)
    plt.savefig(save_path+"_deleted.jpg")
    
    plt.figure()
    plt.ylim(yl)
    plt.xlim(xl)
    for rsl in rslt:
        X,Y=rsl['Position X'],rsl['Position Y']
        plt.plot(X,Y)
    plt.savefig(save_path+"_filtre.jpg")

###
input("Sélection du chemin d'accès (enter pour continuer)")
path=tkinter.filedialog.askopenfilename()
output_name_img=input("Entrer debut nom du fichier de sortie pour les images (sera complété pour les 3 images): ")
time_step=input('Entrer le pas du temps (Ne rien entrer pour valeur par défaut 0.21): ')
if time_step == '':
    time_step=0.21
else:
    time_step=float(time_step)
    
tresh=input("Entrer la limite (Ne rien entrer pour valeur par défaut 0.5): ")
if tresh == '':
    tresh=0.5
else:
    tresh=float(tresh)
    
recs=[]
while True:
    action=input("Entrer un rectangle? (y/n)")
    if action=="y":
        x1=float(input('x1='))
        x2=float(input('x2='))
        y1=float(input('y1='))
        y2=float(input('y2='))
        act=input('valider? (y/n)')
        if act=='y':
            recs.append({'x1':x1,'y1':y1,'x2':x2,'y2':y2})
    else:
        break
print(recs)
n_max=int(input('Nombre max de points dans un rectangle: nmax='))
output_name=input("Entrer nom du fichier de sortie: ")
manual = (input("Echelle manuelle? (y/n)") == "y")
xlim=()
ylim=()
while manual:
    try:
        X1=int(input("xmin="))
        X2=int(input("xmax="))
        Y1=int(input("ymin="))
        Y2=int(input("ymax="))
        xlim=(X1,X2)
        ylim=(Y1,Y2)
        break
    except ValueError:
        print("Entrez un nombre valide.")
         
print("Traitement en cours...")
rsl,r,rt,r2=traiter(lire(path,time_step),recs,n_max,tresh)
print("Création des graphes...")
afficher(r,rt,r2,output_name_img,manual,xlim,ylim)
rsl=np.array(rsl)
cols=[["Track ID","Nb Points","Duration","Vitesse max","Vitesse max lisse","Vitesse mediane","Vitesse mediane lisse","Vitesse Moyenne","Vitesse moyenne lisse","Displacement length","Track Length", "Stop coefficient"]]
rsl=pd.DataFrame(data=rsl,columns=cols)
rsl.to_csv(output_name,sep=',')
print('Terminé.\n')