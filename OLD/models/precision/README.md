#Specificity model
Modèle RandomForestClassifier avec les paramètres suivants :
```python
score : 0.538759591946067
params : {'class_weight': 'balanced_subsample', 'max_depth': 20, 'min_samples_leaf': 1, 'min_samples_split': 2, 'n_estimators': 200}
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
[[15650   157]
 [  357   135]]
              precision    recall  f1-score   support

       False       0.98      0.99      0.98     15807
        True       0.46      0.27      0.34       492

    accuracy                           0.97     16299
   macro avg       0.72      0.63      0.66     16299
weighted avg       0.96      0.97      0.96     16299
```
Résultats sur le jeu de données de validation (7 courses de 2023):
```python
[[7150   45]
 [ 201   40]]
              precision    recall  f1-score   support

       False       0.97      0.99      0.98      7195
        True       0.47      0.17      0.25       241

    accuracy                           0.97      7436
   macro avg       0.72      0.58      0.61      7436
weighted avg       0.96      0.97      0.96      7436
```

On observe que les performances sont similaire sur le jeu de données de test et de validation. On peut donc conclure que le modèle ne souffre pas d'overfitting.
## ROC curve
![roc_curve](figures/roc_curve.svg)
## Performance course par course
![f1_score_per_track](figures/f1_score_per_track.svg)
On peut voir que les performances sont très variables d'une course à l'autre. Parce que les courses n'ont pas la même difficulté...
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