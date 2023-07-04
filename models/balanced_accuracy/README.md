#Balanced Accuracy model
Le modèle optimisé avec le score de balanced accuracy devrait être plus équilibré. La balanced accuracy est définie comme :
$$
\frac{\text{specificity} + \text{sensitivity}}{2}
$$
Modèle RandomForestClassifier avec les paramètres suivants :
```python
score : 0.7958320909904882
params : {'class_weight': 'balanced_subsample', 'max_depth': 10, 'min_samples_leaf': 5, 'min_samples_split': 2, 'n_estimators': 100}
```

Trouvé avec GridSearchCV sur les paramètres suivants :
```python
param_grid = {
    'n_estimators': [100, 200, 300],
    'max_depth': [5, 10, 20],
    'min_samples_split': [2, 5, 10],
    'min_samples_leaf': [1, 2, 5],
    'class_weight': ['balanced_subsample']
}
```

Résultats sur le jeu de données de test :
```python
[[13576  2231]
 [  134   358]]
              precision    recall  f1-score   support

       False       0.99      0.86      0.92     15807
        True       0.14      0.73      0.23       492

    accuracy                           0.85     16299
   macro avg       0.56      0.79      0.58     16299
weighted avg       0.96      0.85      0.90     16299
```
Résultats sur le jeu de données de validation (7 courses de 2023):
```python
[[6470  725]
 [ 123  118]]
              precision    recall  f1-score   support

       False       0.98      0.90      0.94      7195
        True       0.14      0.49      0.22       241

    accuracy                           0.89      7436
   macro avg       0.56      0.69      0.58      7436
weighted avg       0.95      0.89      0.92      7436
```

Les résultats entre test et validation sont assez similaires, on remarque simplement une baisse du recall sur la validation. On a appriori, pas de surapprentissage.
## ROC curve
![roc_curve](figures/roc_curve.svg)
## Performance course par course
![f1_score_per_track](figures/f1_score_per_track.svg)
Il est intéressant de noter que les résultats sont pas simplement meilleur que ceux des modèles specificity et sensitivity. 
![safety_car](figures/sc_or_vsc_periods.svg)
### Barcelone
![barcelone](figures/predictions_by_lapNumber_9.svg)
### Melbourne
![melbourne](figures/predictions_by_lapNumber_19.svg)
### Montreal
![montreal](figures/predictions_by_lapNumber_29.svg)
### Baku
![baku](figures/predictions_by_lapNumber_4.svg)
### Jeddah
![jeddah](figures/predictions_by_lapNumber_14.svg)
### Miami
![miami](figures/predictions_by_lapNumber_24.svg)
### Sakhir
![sakhir](figures/predictions_by_lapNumber_34.svg)

## Conclusion