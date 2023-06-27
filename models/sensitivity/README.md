#Sensitivity model
Le modèle optimisé avec le score de sensitivité devrait prendre plus de risque. Il essaie de prédire le plus de vrais positifs possible au détriment des faux négatifs. On devrait voir plus de prédictions positives.

Modèle RandomForestClassifier avec les paramètres suivants :
```python
...
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
...
```
Résultats sur le jeu de données de validation (7 courses de 2023):
```python
[[5815 1380]
 [  98  143]]
              precision    recall  f1-score   support

       False       0.98      0.81      0.89      7195
        True       0.09      0.59      0.16       241

    accuracy                           0.80      7436
   macro avg       0.54      0.70      0.52      7436
weighted avg       0.95      0.80      0.86      7436
```
On observe plus de faux positifs mais pas beaucoup plus de vrais positifs par rapport au modèle specifique.
## ROC curve
![roc_curve](figures/roc_curve.svg)
## Performance course par course
![f1_score_per_track](figures/f1_score_per_track.svg)
Les performances sont en général moins bonne avec un maximum de 0.35 pour le circuit de Sakhir. Il n'y a pas de course où le F1-score est nul mais il reste très faible.
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