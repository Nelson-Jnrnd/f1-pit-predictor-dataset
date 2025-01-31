Résultats sur le jeu de données de test :
```python
[[14397  1410]
 [  204   288]]
              precision    recall  f1-score   support

         0.0       0.99      0.91      0.95     15807
         1.0       0.17      0.59      0.26       492

    accuracy                           0.90     16299
   macro avg       0.58      0.75      0.60     16299
weighted avg       0.96      0.90      0.93     16299
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