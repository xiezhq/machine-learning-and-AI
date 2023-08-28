import argparse
import os
import sys
import datetime

# tools.py
import tools


# read wellindex file and convert the mapping into the dictionary
def readIndex(csvfile):
	rows = tools.readCsvFileSkipLine(csvfile, delimiter=',')

	# make sure the dual-direction index mapping (wellRow to wellLetter and wellLetter to wellRow) are unique
	if tools.checkDuplicate([row[0] for row in rows]) or tools.checkDuplicate([row[1] for row in rows]):
		e = "Duplicates in wellRow or wellLetter exist in {}".format(csvfile)
		raise RuntimeError(e)

	# convert rows into dictionay for well index
	dic = {}
	for row in rows:
		dic[row[0]] = row[1]

	return dic

def join(args4joinSetupRaw):
	print('joinSetupRaw.py starts at', datetime.datetime.now().ctime())

	rows4setup = tools.readDictCsvFile(args4joinSetupRaw['setup'], delimiter=',')
	rows4raw = tools.readDictCsvFile(args4joinSetupRaw['rawdata'], delimiter=',')

	# read wellindex file and convert the mapping into the dictionary
	dic4index = readIndex(args4joinSetupRaw['wellindex'])

	# create unique data id (plate id and well id) for both setup and raw data
	dic4rows4setup = {}
	for row in rows4setup:
		id = row['Plate_ID'] + row['well']
		dic4rows4setup[id] = row
	dic4rows4raw = {}
	for row in rows4raw:
		id = row['plate'].replace(' ','') + dic4index[row['row']] + row['col'].zfill(2)
		dic4rows4raw[id] = row

	# based on unique data id, merge setup rows into raw data rows
	ids = dic4rows4raw.keys()
	rows4joined = []
	for id in ids:
		row4setup = dic4rows4setup[id]
		row4raw = dic4rows4raw[id]
		for key4setup in row4setup.keys():
			row4raw[key4setup] = row4setup[key4setup]
		rows4joined.append(row4raw)
			
	# output joined data
	fieldnames = rows4joined[0].keys()
	tools.writeDictCsvFile(args4joinSetupRaw['joined'], fieldnames, rows4joined, delimiter=',')	

	print('joinSetupRaw.py ends at', datetime.datetime.now().ctime())

if __name__ == "__main__":
	import argparse
	import textwrap

	# Parse command line arguments
	descriptStr = ("Join experimental setup and raw luciferase data, and then output joined data.")

	parser = argparse.ArgumentParser(prog=sys.argv[0], description = textwrap.dedent(descriptStr), 
			formatter_class=argparse.RawDescriptionHelpFormatter)

	parser.add_argument(
		'--setup',
		required = True,
		default='',
		help = "CSV file containing the experimental setup, '' by default",
                )

	parser.add_argument(
		'--rawdata',
		required = True,
		default='',
		help = "CSV containing the raw luciferase data, '' by default",
                )

	parser.add_argument(
		'--joined',
		required = True,
		default='',
		help = "CSV containing the joined data, '' by default",
                )

	parser.add_argument(
		'--wellindex', 
		required = False, 
		default = 'well_row_index.csv', 
		help = "The index file mapping the idnex number in column 'row' in the raw luciferase data to the starting letter of the column 'well' in the experimental setup, 'well_row_index.csv' by default. If the mapping is changed in the luciferase experiments or assays, the index file must be updated accordingly.")

	args = parser.parse_args()

	args4joinSetupRaw = {
					'setup': args.setup.strip(),
					'rawdata': args.rawdata.strip(),
					'joined': args.joined.strip(),
					'wellindex': args.wellindex,
				}

	join(args4joinSetupRaw)
