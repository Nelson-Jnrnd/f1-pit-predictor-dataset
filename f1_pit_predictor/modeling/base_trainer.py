from abc import ABC, abstractmethod
import mlflow
from sklearn.metrics import accuracy_score

class BaseTrainer(ABC):
    """
    Abstract base class for model training.
    """

    def __init__(self, config, name):
        super().__init__()
        self.config = config
        self.name = name
        self.model = None
        mlflow.set_experiment(config["experiment_name"])
    
    @abstractmethod
    def train(self, x, y):
        """
        Train the model.
        """
        pass

    @abstractmethod
    def evaluate(self, x, y):
        """
        Evaluate the model.
        """
        y_pred = self.predict(x)
        acc = accuracy_score(y, y_pred)

        mlflow.log_metric("accuracy", acc)
        return acc

    @abstractmethod
    def predict(self, x):
        """
        Make predictions using the trained model.
        """
        pass

    @abstractmethod
    def save(self, path):
        """
        Save the trained model to a file.
        """
        pass