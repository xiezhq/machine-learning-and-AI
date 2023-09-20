# Dependencies:
- Pandas
- Scikit-learn 
- statsmodels (for LOWESS model), https://www.statsmodels.org/dev/install.html
- plotly (for visulazation), https://plotly.com/python/getting-started/
- Kaleido (required by plotly), https://github.com/plotly/Kaleido

# data
- Input folder: ../bixeng
- Output folder: ../analysis

# how to run
1. kernelDensityEstimation.py

   It is used to checking the distribution of the data points. It outputs hist*.pdf and kde*.pdf in ../analysis/.

2. joinSetupRaw.py

   It is used to combine the data and the corresponding meta data, and output the final data in ../analysis/joined.csv.

3. qcReport.py

   It is ued to do data quanlity control and detect the potential outliers in data. It produces the data QC reports in both .csv and .html versions. It also output the rescaled/normalized data (dataNorm.csv) which is rescaled/normalized based on the negative control data, and cleaned data (cleaned.csv) in which the detected outliers are removed. All output files are placed in ../analysis/. 

4. fitmodel.py

   It fits LOWESS models seperately for each drug, with two different training data sets (2/3 of data, all data) and plot the data points and fitted models to visualize the performance of models. It outputs one *LOWESS.pdf per drug.
