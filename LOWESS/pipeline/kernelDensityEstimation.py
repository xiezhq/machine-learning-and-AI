import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.neighbors import KernelDensity
from sklearn.model_selection import GridSearchCV


def my_scores(estimator, X):
    scores = estimator.score_samples(X)
    # Remove -inf
    scores = scores[scores != float('-inf')]
    # Return the mean values
    return np.mean(scores)

#kernels = ['cosine', 'epanechnikov', 'exponential', 'gaussian', 'linear', 'tophat']
kernels = ['exponential', 'gaussian', 'tophat']
h_vals = np.arange(0.05, 1, .1)

grid = GridSearchCV(KernelDensity(),
                    {'bandwidth': h_vals, 'kernel': kernels},
                    scoring=my_scores)

csvfile = "../analysis/joined.csv"
data = pd.read_csv(csvfile)
plate1 = data[data["Plate_ID"] == "Plate1"]
plate2 = data[data["Plate_ID"] == "Plate2"]
negControl = data.loc[data["chem_M"].isna(), "value"]
print("hello", negControl.count(), data[data["chem_M"].isna()]["value"].count())

negControl4plate1 = plate1.loc[data["chem_M"].isna(), "value"]
negControl4plate2 = plate2.loc[data["chem_M"].isna(), "value"]

negControl.plot.hist().get_figure().savefig("../analysis/hist.pdf")
#negControl.plot.kde().get_figure().savefig("../analysis/kde.pdf")
#negControl4plate1.plot.kde().get_figure().savefig("../analysis/kde1.pdf")
#negControl4plate2.plot.kde().get_figure().savefig("../analysis/kde2.pdf")

'''
x_train = negControl.values.reshape(-1,1)
print("x_train:", len(x_train))
print(x_train.shape)
x_test = x_train
print("x_test:", len(x_test))
print(x_test.shape)

grid.fit(x_train)
best_kde = grid.best_estimator_
log_dens = best_kde.score_samples(x_test)
plt.fill(x_test, np.exp(log_dens), c='green')
plt.title("Best Kernel: " + best_kde.kernel+" h="+"{:.2f}".format(best_kde.bandwidth))
#plt.show()
plt.savefig("../analysis/kde.pdf")
plt.close("all")
'''
