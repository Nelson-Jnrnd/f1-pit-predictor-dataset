from sklearn.ensemble import RandomForestClassifier
from f1_pit_predictor.modeling.base_trainer import BaseTrainer
import pickle

class RandomForestTrainer(BaseTrainer):
    """
    Trainer for a random forest classifier.
    """

    def __init__(self, config, name):
        super().__init__(config, name)
        self.model = RandomForestClassifier(
            **config["random_forest"],
            random_state=config["random_state"]
            )

    def train(self, x, y):
        self.model.fit(x, y)
        self.evaluate(x, y)


    def predict(self, x):
        return self.model.predict(x)

    def save(self, path):
        pickle.dump(self.model, open(path, "wb"))