import os
import pickle
import pandas as pd
import warnings
from source.logger import logging
from source.exception import ChurnException
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, confusion_matrix, classification_report, make_scorer
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier, AdaBoostClassifier
from sklearn.naive_bayes import GaussianNB
from sklearn.neighbors import KNeighborsClassifier
from sklearn.model_selection import GridSearchCV
from xgboost import XGBClassifier

warnings.filterwarnings('ignore')


def hyperparameter_tuning(x_train, y_train):
    try:
        model = GradientBoostingClassifier()

        param_grid = {
            'loss': ['log_loss'],
            'learning_rate': [0.01],
            'n_estimators': [50]
        }

        f1_scorer = make_scorer(f1_score, average='macro')

        grid_search = GridSearchCV(estimator=model, param_grid=param_grid, cv=5, scoring=f1_scorer)

        grid_search.fit(x_train, y_train)

        best_params = grid_search.best_params_
        best_score = grid_search.best_score_

        return best_params, best_score

    except ChurnException as e:
        raise e


class ModelTrainEvaluate:
    def __init__(self, utility_config):
        self.utility_config = utility_config

        self.models = {
            "DecisionTreeClassifier": DecisionTreeClassifier(),
            "RandomForestClassifier": RandomForestClassifier(),
            "GradientBoostingClassifier": GradientBoostingClassifier(),
            "AdaBoostClassifier": AdaBoostClassifier(),
            "GaussianNB": GaussianNB(),
            "KNeighborsClassifier": KNeighborsClassifier(),
            "XGBClassifier": XGBClassifier()
        }

        self.model_evaluation_report = pd.DataFrame(columns=["model_name","accuracy", "precision", "recall", "f1", "class_report", "confu_matrix"])

    def model_training(self, train_data, test_data):
        try:
            x_train = train_data.drop('Churn', axis=1)
            y_train = train_data['Churn']
            x_test = test_data.drop('Churn', axis=1)
            x_test = x_test.drop(x_test.index[-3:])
            y_test = test_data['Churn']
            y_test = y_test.drop(y_test.index[-3:])

            dir_path = os.path.dirname(self.utility_config.model_path)
            os.makedirs(dir_path, exist_ok=True)

            train_data.to_csv("train_data.csv", index=False)
            for name, model in self.models.items():
                model.fit(x_train, y_train)
                y_pred = model.predict(x_test)

                with open(f"{self.utility_config.model_path}/{name}.pkl", "wb") as f:
                    pickle.dump(model, f)

                self.metrics_and_log(y_test, y_pred, name)

        except ChurnException as e:
            raise e

    def metrics_and_log(self, y_test, y_pred, model_name):
        try:
            accuracy = accuracy_score(y_test, y_pred)
            precision = precision_score(y_test, y_pred)
            recall = recall_score(y_test, y_pred)
            f1 = f1_score(y_test, y_pred)
            class_report = classification_report(y_test, y_pred)
            confu_matrix = confusion_matrix(y_test, y_pred)

            logging.info(f"model: {model_name}, accuracy:{accuracy}, precision:{precision}, recall:{recall}, f1_score: {f1}, classification_report:{class_report}, confusion matrix:{confu_matrix}")
            new_row = [model_name, accuracy, precision, recall, f1, class_report, confu_matrix]
            self.model_evaluation_report = self.model_evaluation_report._append(pd.Series(new_row, index=self.model_evaluation_report.columns), ignore_index=True)

        except ChurnException as e:
            print(e)
            raise e

    def retrain_final_model(self, train_data, test_data):
        try:
            x_train = train_data.drop('Churn', axis=1)
            y_train = train_data['Churn']
            x_test = test_data.drop('Churn', axis=1)
            x_test = x_test.drop(x_test.index[-3:])
            y_test = test_data['Churn']
            y_test = y_test.drop(y_test.index[-3:])

            best_params, best_score = hyperparameter_tuning(x_train, y_train)

            final_model = GradientBoostingClassifier(**best_params)
            final_model_name = "GradientBoostingClassifier"

            final_model.fit(x_train, y_train)

            test_score = final_model.score(x_test, y_test)

            logging.info(f"final model: GradientBoostingClassifier, test score: {test_score}")

            with open(f"{self.utility_config.final_model_path}/{final_model_name}.pkl", "wb") as f:
                pickle.dump(final_model, f)

        except ChurnException as e:
            raise e

    def initiate_model_training(self):
        try:
            print("Model Training Started...")

            logging.info("Start: Model Training and evaluation")

            train_data = pd.read_csv(self.utility_config.train_dt_train_file_path+'/'+self.utility_config.train_file_name, dtype={"TotalCharges": "float64"})
            test_data = pd.read_csv(self.utility_config.train_dt_test_file_path+'/'+self.utility_config.test_file_name, dtype={"TotalCharges": "float64"})

            self.model_training(train_data, test_data)
            self.model_evaluation_report.to_csv("source/ml/model_evaluation_report.csv", index=False)

            self.retrain_final_model(train_data, test_data)

            print('Model train Complete')

            logging.info("Complete model training and evaluation")

        except ChurnException as e:
            raise e