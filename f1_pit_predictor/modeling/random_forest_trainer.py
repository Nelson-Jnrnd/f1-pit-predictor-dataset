from sklearn.ensemble import RandomForestClassifier
from f1_pit_predictor.modeling.base_trainer import BaseTrainer
import pickle
import mlflow

class RandomForestTrainer(BaseTrainer):
    """
    Trainer for a random forest classifier.
    """

    def __init__(self, config, name):
        super().__init__(config, name)
        self.model = RandomForestClassifier(
            **config["random_forest"],
            )

    def train(self, x, y):
        with mlflow.start_run(run_name=self.name):
            mlflow.log_params(self.config["random_forest"])
            self.model.fit(x, y)
            self.evaluate(x, y)
            mlflow.sklearn.log_model(self.model, "model")

    def predict(self, x):
        return self.model.predict(x)

    def save(self, path):
        pickle.dump(self.model, open(path, "wb"))