MAC_PDFTOTEXT_COMMAND = 'pdftotext'

import argparse
from shlex import split
import sys, subprocess, re, csv
from pdb import pm

class Entity():pass

platform=sys.platform
    
def main():
	ap = argparse.ArgumentParser()
	ap.add_argument("-input", "-input", required = True, help = "Input pdf file")
	ap.add_argument("-output", "-output", required = True, help = "Output csv file")
	args = vars(ap.parse_args())

	input_file = args['input']
	output_file = args['output']

	if platform=='win32':
	    returncode = subprocess.call("pdftotext.exe -table %s" % (input_file), shell=True)
	elif platform=='linux2':
	    returncode = subprocess.call("pdftotext -table %s" % (input_file), shell=True)
	elif platform=='darwin':
		returncode = subprocess.call("%s -table %s" % (MAC_PDFTOTEXT_COMMAND, input_file), shell=True)
	
	text_file = open('%s.txt' % input_file[:-4], 'r')
	text_data = text_file.read()
	text_data = re.sub("\n\n(\D)", r'\n\1', text_data)
	text_data = re.sub("Name:                                                Name:                                                   Name:\n", '', text_data)
	text_data = re.sub("Name:  ", '       ', text_data)
	text_data = re.sub("Name:\n", '     \n', text_data)
	text_data = re.sub(" {100,}\n", '', text_data)

	# tempout = open('output.txt', 'w');tempout.write(text_data);tempout.close()

	###PAGE 1
	# AC_No, AC_Name, PC_No, PC_Name, Main_Village, Police_Station, Tehsil, District, Pin_Code, PS_No, PS_Name, PS_Address
	AC_search = re.search('Name and Reservation Status of Assembly Constituency : *(\d*)-(.*)', text_data)
	AC_No = AC_search.group(1)
	AC_Name = AC_search.group(2)

	PC_search = re.search('Assembly Constituency is located : (\d)*\W*(.*)', text_data)
	PC_No = PC_search.group(1)
	PC_Name = PC_search.group(2)

	Main_Village = re.search('Main Village : *(.*)', text_data).group(1)
	Police_Station = re.search('Police Station : *(.*)', text_data).group(1)
	Tehsil = re.search('Tehsil : *(.*)', text_data).group(1)
	District = re.search('District : *(.*)', text_data).group(1)
	Pin_Code = re.search('PIN Code : *(.*)', text_data).group(1)

	PS_search = re.search('No. and Name of Polling Station :.*\n\n(\d+)\. (.{1,77})', text_data)
	PS_No = PS_search.group(1)
	PS_Name	= PS_search.group(2)

	PS_Address = re.search('Address of Polling Station :.*(\n+([^ ]+ )+[^ ]+)', text_data).group(1)

	#------------------------

	PC=re.finditer('Section No\. & Name: (\d+)\. ?(.*)', text_data)
	PC_positions = [[x.span(), x.groups()] for x in PC]
	PC_positions.append([(len(text_data) - 1,0),])

	with open(output_file, 'wb') as csvfile:
		csvwriter = csv.writer(csvfile)
		csvwriter.writerow(['Assembly Constituency Number', 'Assembly Constituency Name', 'Parliamentary Constituency Number', 'Parliamentary Constituency Name', 'Main Village', 'Police Station', 'Tehsil', 'District', 'Pin Code', 'Polling Station No', 'Polling Station Name', 'Polling Station Address',
		    	            'Name', 'House No', 'Age', 'Sex', 'Section No', 'Section Name', 'Relation Type', 'Relation Name', 'Import Check' ,'Serial No', 
		    	            "Serial No2"])
		for xp, pos in enumerate(PC_positions[:-1]):
			scanner = text_data[pos[0][1]:PC_positions[xp + 1][0][0]].splitlines()
			stage = 0

			for line in scanner:
				if stage == 0:
					relations_list = []
					tri_list = [Entity(), Entity(), Entity()]
					serials = re.findall('(\d{0,3}) {1,13}EPIC NO: ([^\s]*)', line)
					if serials:
						for xs, serial in enumerate(serials): tri_list[xs].serial = serial
						stage = 1
						continue
				elif stage == 1:
					names = re.findall('Name : +(([^ \n]+ ?)+ {0,10}[^ \n]+)', line)
					if names:
						for xn, name in enumerate(names): tri_list[xn].name = name
						stage = 2
						continue
				elif stage == 2:
					if not re.search('House No', line): relations_list.append(line)
					else: 
						relations = [[None, '', False], [None, '', False], [None, '', False]]
						if len(relations_list) > 1: relations[0][2] = relations[1][2] = relations[2][2] = True
						for line2 in relations_list:
							columns = re.search('^(.{1,53})(.{1,52}\s{0,14})(.*)$', line2).groups(1)
							# ^(.{1,53})(.{1,53}\s{0,3})(.*)$
							for x, val in enumerate(columns):
								relations[x][1] += val
						for relation in relations:#[r for r in relations if r[0] != None]:
							result = re.search("(Father|Husband|Mother)'s", relation[1])
							if result:
								relation[0] = result.groups(0)
								relation[1] = re.sub("(Father's)|(Husband's)|(Mother's)", '', relation[1])
								relation[1] = re.sub(" {2,}", ' ', relation[1])
								relation[1] = re.sub("^ *", '', relation[1])
						for xr, relation in enumerate(relations): tri_list[xr].relation = relation
						stage = 3
				if stage == 3:
					houses = re.findall('House No..([^ \n]{1,10})', line)
					if houses:
						for xh, house in enumerate(houses): tri_list[xh].house = house
						stage = 4
						continue
				elif stage == 4:
					ages = re.findall('Age {0,8}: ?(\d{1,3})\s{1,10}Sex {0,2}: ?([^\s]*)', line)
					for xa, age in enumerate(ages): tri_list[xa].age = age
					for tri in [t for t in tri_list if hasattr(t, 'name')]:
						csvwriter.writerow([AC_No, AC_Name, PC_No, PC_Name, Main_Village, Police_Station, Tehsil, District, Pin_Code, PS_No, PS_Name, PS_Address,
						    	            tri.name[0], tri.house, tri.age[0], tri.age[1], pos[1][0], pos[1][1], tri.relation[0][0], tri.relation[1], tri.relation[2], tri.serial[0], 
						    	            tri.serial[1]])
					stage = 0

if __name__ == '__main__':
	main()