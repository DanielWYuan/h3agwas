#!/usr/bin/env python3

########################################################
# ma_formatmetasoft.py modification of plink2metasoft.py                                    
#   Convert file of assoc files to Metasoft input file  
#   Free license -- you are free to use it in any ways 
#   Buhm Han (2012)                                    
#   memories used is very high
########################################################

import sys, subprocess, os
#import stats
from scipy import stats

comple = {'A':'T', 'T':'A', 'G':'C', 'C':'G'}
vectortorbase=['A','T','C','G']

rsHead="RSID"
ChHead="CHRO"
PsHead="POS"
A1Head="A1"
A2Head="A2"
BetHead="BETA"
PHead="PVAL"
SError="SE"

# PROCESS ARGUMENTS
if len(sys.argv) < 3:
    print_and_exit()
out=sys.argv[1]
files=sys.argv[2:]

# MERGE STUDIES
fout=open(out+'.meta','w')
#fmap=open(out+'.mmap','w')
flog=open(out+'.log','w')


def GetInfoRsGWAS(rsid, snp,A1Pivot, A2Pivot,CompSE, PosA1Head, PosA2Head, PosBetHead, PosPHead,PosSError) :
    snp[PosA1Head]=snp[PosA1Head].upper()
    snp[PosA2Head]=snp[PosA2Head].upper()
    studyindex=-1
    pivotstudyindex=-2
    if PosA1Head : 
      if snp[PosA1Head] not in vectortorbase:
         return 'NA NA '
    if PosA2Head : 
      if snp[PosA2Head] not in vectortorbase:
         return 'NA NA '
    
    beta=snp[PosBetHead]
    if CompSE :
        if float(p)==0.5 :
              p2=0.499999
        else :
           p2=snp[PosPHead]
        stderr="%f"%abs(float(beta)/stats.norm.ppf(float(p2), loc =0, scale = 1))  #'abs(%s/qnorm(%s/2))'%(beta,p)
    else :
         stderr=snp[PosSError]
    # CHECK ALLELE TO PIVOT
    if PosA2Head and PosA1Head :
       if A1Pivot == snp[PosA1Head] and A2Pivot == snp[PosA2Head]:
          return beta+' '+stderr+' ' 
       elif A1Pivot == snp[PosA2Head] and A2Pivot == snp[PosA1Head]:
            # SIMPLE FLIP
            beta='%f'%(float(beta)*-1)
       elif A1Pivot == comple[snp[PosA1Head]] and A2Pivot == comple[snp[PosA2Head]]:
                        # STRAND INCONSIS., BUT GOOD
            flog.write('FLIP_STRAND %s in study %d\n'%(rsid,studyindex))
       elif  A1Pivot == comple[snp[PosA2Head]] and A2Pivot == comple[snp[PosA1Head]]:
             # STRAND INCONSIS., SIMPLE FLIP
             flog.write('FLIP_STRAND %s in study %d\n'%(rsid,studyindex))
             beta='%f'%(float(beta)*-1)
       else:
            flog.write('EXCLUDE %s due to allele inconsistency: A1:%s A2:%s in study %d but A1:%s A2:%s in study %d\n'
                                   %(rsid, A1Pivot, A2Pivot, pivotstudyindex,
                               snp[PosA1Head], snp[PosA2Head], studyindex))
            return 'NA NA '
    return beta+' '+stderr+' ' 


# READ FILES
#studies=[]
newfileslist=[]
rsidschar={}
rsidsinfo={}
listrsall=set([])
for f in files:
    listrsfile=set([])
    study={}
    fin=open(f)
    colnames=fin.readline().split()
    CompSE=False
    if SError not in colnames:
       CompSE=True
       if PHead not in colnames :
          print("no Phead in "+ f+" : skip")
          continue
    if BetHead not in colnames :
       print("no beta in "+ f+" : skip")
       continue
    newfileslist.append(os.path.basename(f))
    PosA1Head=None
    PosA2Head=None
    PosPHead=None
    PosSError=None
    if A1Head in colnames :
       PosA1Head=colnames.index(A1Head)
    if A2Head in colnames:
       PosA2Head=colnames.index(A2Head)
    if PHead in  colnames:
       PosPHead=colnames.index(PHead)
    if SError in  colnames:
       PosSError=colnames.index(SError)
    PosBetHead=colnames.index(BetHead)
    PosRsHead=colnames.index(rsHead)
    for line in fin:
        spll=line.split()
        rsid=spll[PosRsHead]
        if rsid not in listrsall :
           listrsall.add(rsid)
           rsidschar[rsid]=rsid+" "
           if PosA2Head and PosA1Head:
             rsidsinfo[rsid]=[0,spll[PosA1Head],spll[PosA2Head]]
        if rsid not in listrsfile :
           if not spll[PosA1Head] or  not spll[PosA2Head]:
              if PosA2Head and PosA1Head:
                rsidsinfo[rsid][0]=[rsidsinfo[rsid][0] , spll[PosA1Head],spll[PosA2Head]]
           rsidsinfo[rsid][0]+=1  
           rsidschar[rsid]+=GetInfoRsGWAS(rsid, spll,rsidsinfo[rsid][1], rsidsinfo[rsid][2],CompSE, PosA1Head, PosA2Head, PosBetHead, PosPHead,PosSError)
           listrsfile.add(rsid)
        else :
           print("rs "+ rsid +" multi times :skip")
    fin.close()

for rsid in listrsall :
   if rsidsinfo[rsid][0] > 1:
         fout.write(rsidschar[rsid]+'\n')    

wf=open(out+'.'+'files', 'w') 
wf.write("\n".join(newfileslist))
wf.close()


