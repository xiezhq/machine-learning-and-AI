import pandas


# Calculate the boundaries to determine outliers
# 
# points:	array of float numbers, the data points to process.
# stdCutoff:	integer, the number of standard deviation, default 3. 
#		By default, the data points which lies 3 * standard deviations away from the mean are considered as outliers. 
def outliersCutoff(points, stdCutoff = 3):
	bdUpper = points.mean() + stdCutoff * points.std()
	bdLower = points.mean() - stdCutoff * points.std()
	return bdUpper, bdLower


# generate data for qc report
def qc(data4negControls, bdUpper, bdLower):
	outliers = data4negControls[(data4negControls["value"] > bdUpper) | (data4negControls["value"] < bdLower)] 
	nNegControl = data4negControls["value"].count()
	nOutlier = outliers["value"].count()
	percentOutliers = nOutlier / nNegControl
	outlierWells = outliers
	
	return percentOutliers, outlierWells
	
# remove outliers from joined data and return the cleaned data
def removeOutliers(data, bdUpper, bdLower):
	# ensure checking negative control value in case that a drug has strange value.
	cleaned = data[~ (data["chem_M"].isna() & ((data["value"] > bdUpper) | (data["value"] < bdLower)))]

	return cleaned

# process data from single plate (assay)
def plate(data, id):
	# get the boundaries (cutoff) to determine outliers in negative controls
	negControls = data.loc[data["chem_M"].isna(), "value"]
	bdUpper, bdLower = outliersCutoff(negControls, args4qcReport['cutoff'])

	# get data for qc report
	percentOutliers, outlierWells = qc(data.loc[data["chem_M"].isna()], bdUpper, bdLower)
	

	# generate qc report files, both csv and html versions

	# head information in the reports
	str4head = "Percentage of outliers in the negative controls: {:.2%}".format(percentOutliers)
	str4head4csv = '\n\n'.join([id, str4head, "The wells containning the outliers:"])
	str4head4html = '<br>\n'.join(["<p>"+id+"</p>", "<p>"+str4head+"</p>", "<b>The wells containning the outliers:</b>"])

	# csv version
	str4csv4outlierWells = outlierWells.to_csv(path_or_buf=None, na_rep='NA', index=False)
	str4filecontent4csv4outlierWells = '\n'.join([str4head4csv, str4csv4outlierWells])

	# html version
	str4html4outlierWells = outlierWells.to_html(buf=None, na_rep='NA', index=False)
	str4filecontent4html4outlierWells = '<br>\n'.join([str4head4html, str4html4outlierWells])

	# cleaned data
	cleaned = removeOutliers(data, bdUpper, bdLower)

	return (str4filecontent4csv4outlierWells, str4filecontent4html4outlierWells, cleaned)

def qcReport(args4qcReport):
	data = pandas.read_csv(args4qcReport['joined'])	

	# We assume that each plate is an independent assay, so the potential batch effect between assays (plates)
	# needs to be removed. The negative controls from A01 - A24 in each plate could be used as reference/control 
	# for removing batch effect. So, we'd better to the following processing for each plate: identifying/removing outliers,
	# normalizing drug effect (column "value" in data table) using average of the negative controls from wells 
	# 01,12,23,24 for each drug within each plate after removing outliers. When combining and comparing the data 
	# from different plates, we'd bette to remove batch effect using the negative controls from  A01 - A24 in each plate.
	plates = {}
	plateIDs = set(data["Plate_ID"])
	for id in plateIDs:
		plates[id] = data[data["Plate_ID"] == id]

	# process each plate (assay) data independently
	reports = {}
	for id in plateIDs:
		reports[id] = plate(plates[id], id)

	# merge data from multiple plates
	str4filecontent4csv = '\n\n'.join([reports[id][0] for id in plateIDs])
	str4filecontent4html = '<hr>'.join([reports[id][1] for id in plateIDs])
	cleaned = pandas.concat([reports[id][2] for id in plateIDs])

	# write reports and cleaned data to files

	# write csv report
	file2csv = args4qcReport['report']
	with open(file2csv,'w') as fp:
		fp.write(str4filecontent4csv)

	# write html report
	file2html = file2csv.replace(".csv", ".html")
	with open(file2html,'w') as fp:
		fp.write(str4filecontent4html)

	# write cleaned data
	cleaned.to_csv(args4qcReport['cleaned'], na_rep='NA', index=False)

if __name__ == "__main__":
	import argparse
	import textwrap
	import sys
	import datetime

	# Parse command line arguments
	descriptStr = ("Calculate percentage of outliers in the negative controls and display what wells contain those outliers.")

	parser = argparse.ArgumentParser(prog=sys.argv[0], description = textwrap.dedent(descriptStr), 
			formatter_class=argparse.RawDescriptionHelpFormatter)

	parser.add_argument(
		'--joined',
		required = True,
		default='',
		help = "CSV containing the joined data, '' by default. It is the joined data containing experimental setup and raw luciferase data, which is usually the output of running joinSetupRaw.py.",
                )

	parser.add_argument(
		'--report', 
		required = True, 
		default = '', 
		help = "CSV containing the Quality Control (QC) repor, '' by default. A web page containing the QC report is produced as well.")

	parser.add_argument(
		'--cutoff', 
		required = False, 
		default = 3, 
		help = "The cutoff to determine outliers if data points lie cutoff * standard_deviation from mean in negative controls, 3 by default.")

	parser.add_argument(
		'--cleaned',
		required = True,
		default='',
		help = "CSV containing the joined data with outliers removed, '' by default. It is the cleaned joined data where the outliers have been removed.",
                )

	args = parser.parse_args()

	args4qcReport = {
					'joined': args.joined.strip(),
					'report': args.report,
					'cutoff': args.cutoff,
					'cleaned': args.cleaned,
				}

	print('qcReport.py starts at', datetime.datetime.now().ctime())

	qcReport(args4qcReport)

	print('qcReport.py ends at', datetime.datetime.now().ctime())
