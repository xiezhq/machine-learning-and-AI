import os
import pandas
import plotly.graph_objects
import plotly.express
import statsmodels.api



# trial parameters, fraction, for testing model fit
fraction = 2.0/3
fraction_test = 3.0/3


# subset data for drugs
def getdata4drugs(data):
	return data[data["chem_M"].notna()]

# subset data for negative controls
def getdata4ngcontrols(data):
	return data[data["chem_M"].isna()]


# Perform data preprocessing which incude:
# - rescaling assay values in the same assay by controls
# - removing batch effect between assays by controls
#
# Return the rescaled data, dataframe.
def preprocess(data):
	# drug data
	data4drugs = getdata4drugs(data)
	# Get the mean of "value" for each dose of for each drug
	# Group by "chem_M" because each drug dose ("chem_M") is tested two times
	group4drugs = data4drugs.groupby(["Plate_ID", "row", "chem_M"], sort=False, as_index=False)
	means4drugs = group4drugs["value"].mean()

	# control data
	data4ngcontrols = getdata4ngcontrols(data)
	# Get the mean of "value" of control for each drug ("row")
	means4ngcontrols = data4ngcontrols.groupby(["Plate_ID", "row"], sort=False, as_index=True)["value"].mean()
	# Get the mean of "value" of control for each assay/plate ("Plate_ID")
	means4ngcontrols4plate = means4ngcontrols.groupby(level="Plate_ID").mean()

	# First, normalize the values so the values for each drug within the same plate can be comparable:
	# normlizedByRow = drug_value - control_value_mean_in_same_row
	# Note: more solid normlization method should be used to normalize the data within the same plate/assay.
	# Second, calibrate the values so the value for the drugs from different plates can be comparable, namely, removing batch effect:
	# normlizedByPlate = normlizedByRow / control_value_mean_in_same_plate
	# Note: more solid normalization method should be used to remove batch effect among the different plates/assays.

	# Group drug data for each drug and then get each group
	valueNorm = []
	for name,group in means4drugs.groupby(["Plate_ID", "row"], sort=False, as_index=True):
		plate, row = name
		valueNorm4group = (group["value"] - means4ngcontrols.xs(name)) / means4ngcontrols4plate.xs(plate)
		valueNorm.append(valueNorm4group)

	calibrated = pandas.concat(valueNorm).rename("valueNorm")
	# join the calibratealized values and the averaged drug dose into a dataframe
	df = means4drugs.join(calibrated)

	return df

# fit data using LOWESS model
def fitByLoess(x, y, frac=2.0/3, it=3):
	lowess = statsmodels.api.nonparametric.lowess
	xyfit = lowess(y, x, frac=frac)

	return xyfit


def fitmodel4drug(modelname, data, x, y):
	print("group\n",data)
	if modelname == 'LOWESS':
		xyfit = fitByLoess(x, y, frac=fraction)
		xyfit_test = fitByLoess(x, y, frac=fraction_test)
		models = (xyfit, xyfit_test)
	else:
		e = "Invalid model name ({}) was supplied by '--model'".format(modelname)
		raise RuntimeError(e)

	return models
	

def plotModel(data, x, y, models):
	xyfit, xyfit_test = models

	# Create plots

	# create a scatter plot
	#print("xy\n",pandas.concat([x,y], axis=1).sort_values(by='chem_M'))
	fig = plotly.express.scatter(data, x=x, y=y,
					opacity=0.8, color_discrete_sequence=['black'])
	# add the fitted line
	fig.add_traces(plotly.graph_objects.Scatter(x=xyfit[:,0], y=xyfit[:,1], 
							name='LOWESS frac=' + str(fraction), line=dict(color='red')))
	fig.add_traces(plotly.graph_objects.Scatter(x=xyfit_test[:,0], y=xyfit_test[:,1], 
							name='LOWESS frac=' + str(fraction_test), line=dict(color='orange')))
	# change plot background
	fig.update_layout(dict(plot_bgcolor = 'white'))
	# update axes lines
	fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor='lightgray',
			zeroline=True, zerolinewidth=1, zerolinecolor='lightgray',
			showline=True, linewidth=1, linecolor='black')
	fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='lightgray',
			zeroline=True, zerolinewidth=1, zerolinecolor='lightgray',
			showline=True, linewidth=1, linecolor='black')
	# add figure title
	fig.update_layout(title=dict(text="Relationship of receptor activity (y-axis) to changes in drug concentration (x-axis)",
					font=dict(color='black')))
	# update marker size
	fig.update_traces(marker=dict(size=3))
	
	# return plot for the drug
	
	return fig
	

# Return chemids
#
# chemids: a series with group name as index, (Plate_ID, row)
# data structure layout:
# Plate_ID  row
# Plate2    2      O-50
#           3      O-66
#           4      O-41
# ...	...	...
# Plate1    2      O-44
#           3      O-70
# 
def platerow2chemid(data):
	data4drugs = getdata4drugs(data)
	chemids = data4drugs.groupby(["Plate_ID", "row"], sort=False, as_index=True)["chem_ID"].agg(lambda g: g.head(1))

	return chemids

def fitmodel(args4fitmodel):
	data = pandas.read_csv(args4fitmodel["data"])
	modelname = args4fitmodel["model"]
	opath = args4fitmodel["opath"]

	dataNorm = preprocess(data)
	fname = os.path.join(opath, "dataNorm.csv")
	dataNorm.to_csv(fname, na_rep='NA', index=False)

	# Fit models seperately for each drug

	chemids = platerow2chemid(data)

	drugs = dataNorm.groupby(["Plate_ID", "row"], sort=False, as_index=False)
	for gid,drug in drugs:
		x = drug["chem_M"]
		y = drug["valueNorm"]
		# create model
		models = fitmodel4drug(modelname, drug, x, y)
		# create plot
		fig = plotModel(drug, x, y, models)

		# output model plot
		chemid = chemids.xs(gid)
		fname = '_'.join([chemid, gid[0], str(gid[1]), modelname]) + '.pdf'
		p2file = os.path.join(opath, fname)
		fig.write_image(p2file)
	

if __name__ == "__main__":
	import argparse
	import textwrap
	import datetime
	import sys

	# Parse command line arguments
	descriptStr = ("Fit dose-response curves using specified model, LOWESS by default. Briefly, the fitted model shows the relationship of receptor activity (y-axis) to changes in drug concentration (x-axis).")

	parser = argparse.ArgumentParser(prog=sys.argv[0], description = textwrap.dedent(descriptStr), 
			formatter_class=argparse.RawDescriptionHelpFormatter)

	parser.add_argument(
		'--data',
		required = True,
		default='',
		help = "CSV containing the input data, '' by default. It is the assay data containing experimental setup and raw luciferase data, which is usually the output of qcreport.py, where the outliers are removed.",
                )

	parser.add_argument(
		'--model', 
		required = False, 
		default = 'LOWESS', 
		help = "The model you want to fit dose-response curves, 'LOWESS' (Locally Weighted scatterplot Smoothing) by default. Briefly, they show the relationship of receptor activity (y-axis) to changes in drug concentration (x-axis).")

	parser.add_argument(
		'--opath',
		required = True,
		default='',
		help = "The output directory where all output files are, '' by default.",
                )

	args = parser.parse_args()

	args4fitmodel = {
					'data': args.data,
					'model': args.model,
					'opath': args.opath,
				}

	print('fitmodel.py starts at', datetime.datetime.now().ctime())

	fitmodel(args4fitmodel)

	print('fitmodel.py ends at', datetime.datetime.now().ctime())
