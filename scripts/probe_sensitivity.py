"""Post-hoc regularization sensitivity; preserve all original pilot_v1 results."""
import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression

out = Path('results/pilot_v1')
config = json.loads((out/'config.json').read_text())
manifest = [r for r in json.loads((out/'manifest.json').read_text()) if r['split'] in ['train','val']]
y = np.array([r['label'] for r in manifest])
train = np.array([r['split']=='train' for r in manifest])
conditions = pd.read_csv(out/'conditions.csv',keep_default_na=False)
target = conditions.label.to_numpy()
results = []
for model in ['aimv2','dinov2']:
    x = np.load(out/'features'/f'{model}_clean_trainval.npy',mmap_mode='r')
    evaluation = np.load(out/'features'/f'{model}_evaluation.npy',mmap_mode='r')
    for c in [10.,100.,1000.]:
        clf=LogisticRegression(C=c,max_iter=2000,solver='lbfgs',random_state=config['seed'])
        clf.fit(x[train],y[train])
        row={'model':model,'C':c,'validation_accuracy':float((clf.predict(x[~train])==y[~train]).mean()),'iterations':int(clf.n_iter_.max())}
        correct=(clf.predict(evaluation)==target).astype(int)
        for name,pattern,fraction in [('clean','clean',1.),('random_25','random',.25),('center_25','center',.25)]:
            mask=(conditions.pattern==pattern)&(conditions.fraction==fraction)
            row[name+'_accuracy']=float(correct[mask].mean())
        selected=conditions[conditions.pair_type=='visibility_matched'].copy()
        selected['correct']=correct[selected.index]
        table=selected.pivot(index='image_id',columns='pair_role',values='correct')
        row['matched_correctness_flip_rate']=float((table.a!=table.b).mean())
        results.append(row)
        print(row,flush=True)
frame=pd.DataFrame(results)
frame['chosen_by_expanded_validation_grid']=False
for model,g in frame.groupby('model'):
    frame.loc[g.validation_accuracy.idxmax(),'chosen_by_expanded_validation_grid']=True
frame.to_csv(out/'probe_regularization_sensitivity.csv',index=False)
(out/'probe_sensitivity_scope.json').write_text(json.dumps({
    'post_hoc':True,'trigger':'Both original clean validation searches selected the prespecified C-grid upper boundary.',
    'grid':[10,100,1000],'selection':'Expanded-grid choice uses clean validation only; every test result is reported and none replaces the original pilot.',
    'original_results_changed':False,'limitation':'Not a pooling sensitivity study or a general model ranking.'},indent=2))
