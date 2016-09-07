MAC_PDFTOTEXT_COMMAND = 'ebook-convert'
LINUX_PDFTOTEXT_COMMAND = 'ebook-convert'

import argparse
from shlex import split
import sys, subprocess, re, csv
from pdb import pm
from pdb import set_trace as st

class Entity():pass

platform=sys.platform
    
def main():
	ap = argparse.ArgumentParser()
	ap.add_argument("-input", "-input", required = True, help = "Input pdf file")
	ap.add_argument("-output", "-output", required = True, help = "Output csv file")
	args = vars(ap.parse_args())

	# args = {'input': 'Part19.pdf', 'output': 'output.csv'}

	input_file = args['input']
	output_file = args['output']

	if platform=='win32': returncode = subprocess.call(r'"C:\Program Files\Calibre2\ebook-convert.exe" %s %s.txt' % (input_file, input_file[:-4]), shell=True)
	elif platform=='linux2': returncode = subprocess.call(r'%s %s %s.txt' % (LINUX_PDFTOTEXT_COMMAND, input_file, input_file[:-4]), shell=True)
	elif platform=='darwin': returncode = subprocess.call(r'%s %s %s.txt' % (MAC_PDFTOTEXT_COMMAND, input_file, input_file[:-4]), shell=True)
	
	text_file = open('%s.txt' % input_file[:-4], 'r')
	text_data = text_file.read()
	text_data = re.sub(r"# (\d)", r'\1', text_data)
	text_data = re.sub(r".*?(\d{1,3})\n{0,2} ?(EPIC)", r'\1 \2', text_data)
	text_data = re.sub(r"\n\n", r'\n', text_data)
	text_data = re.sub(r" ((Father|Husband|Mother)'s|House No)", r"\n\1", text_data)
	text_data = re.sub(r" Name:\n", r'\nName:\n', text_data)
	text_data = re.sub(r"Name :+\n(.*)", r'\1', text_data)
	text_data = re.sub(r"((Father|Husband|Mother)'s)\n", r'\1 ', text_data)
	text_data = re.sub(r"(Age|Sex|House No) :", r'\1: ', text_data)
	text_data = re.sub(r"\nPincode:", r' Pincode:', text_data)
	text_data = re.sub(r"\nPolling Station", r' Polling Station', text_data)
	text_data = re.sub(r" Age: ", r' \nAge: ', text_data)
	text_data = re.sub(r"\n.\n", r'\n', text_data)
	
	# tempout = open('output.txt', 'w')
	# tempout.write(text_data)
	# tempout.close()

	###PAGE 1
	# AC_No, AC_Name, PC_No, PC_Name, Main_Village, Police_Station, Tehsil, District, Pin_Code, PS_No, PS_Name, PS_Address
	AC_search = re.search('Name and Reservation Status of Assembly Constituency : *(\d*)-(.*)', text_data)
	AC_No = AC_search.group(1)
	AC_Name = AC_search.group(2)

	PC_search = re.search(' Assembly Constituency is located : (\d)*\W*(.*)1\. ', text_data)
	PC_No = PC_search.group(1)
	PC_Name = PC_search.group(2)

	Main_Village = re.search('Main Village :\n *(.*)', text_data).group(1)
	Police_Station = re.search('Police Station :\n *(.*)', text_data).group(1)
	Tehsil = re.search('Tehsil :\n *(.*)', text_data).group(1)
	District = re.search('District :\n *(.*)', text_data).group(1)
	Pin_Code = re.search('PIN Code :\n *(.*)', text_data).group(1)

	PS_search = re.search('No. and Name of Polling Station :.*\n?(\d+)\. (.{1,77})', text_data)
	PS_No = PS_search.group(1)
	PS_Name	= PS_search.group(2)

	PS_Address = re.search('Address of Polling Station : Number of Auxillary\n(.*)Polling Station', text_data).group(1)

	#------------------------

	PC=re.finditer('Section No\. & Name: (\d+)\. ?(.*)', text_data)
	PC_positions = [[x.span(), x.groups()] for x in PC]
	PC_positions.append([(len(text_data) - 1,0),])

	with open(output_file, 'wb') as csvfile:
		csvwriter = csv.writer(csvfile)
		csvwriter.writerow(['Assembly Constituency Number', 'Assembly Constituency Name', 'Parliamentary Constituency Number', 'Parliamentary Constituency Name', 'Main Village', 'Police Station', 'Tehsil', 'District', 'Pin Code', 'Polling Station No', 'Polling Station Name', 'Polling Station Address',
		    	            'Name', 'Surname Import Check', 'House No', 'Age', 'Sex', 'Section No', 'Section Name', 'Relation Type', 'Relation Name', 'Serial No', 
		    	            "Serial No2"])
		for xp, pos in enumerate(PC_positions[:-1]):
			scanner = text_data[pos[0][1]+1:PC_positions[xp + 1][0][0]].splitlines()
			stage = 0
			tri_list = []

			for line in scanner:
				if stage == 0: #serials
					serial = re.search('(\d*) EPIC NO: (.*)', line)
					if serial:
						entity = Entity()
						entity.serial1 = serial.group(1)
						entity.serial2 = serial.group(2)
						tri_list.append(entity)
						continue
					else:
						tri_length = len(tri_list)
						stage_cnt = 0
						stage = 1
				if stage == 1: #names
					if stage_cnt < tri_length:
						tri_list[stage_cnt].name = line
						tri_list[stage_cnt].extra = ''
						stage_cnt += 1
						continue
					else:
						breaker = re.search("(Father|Husband|Mother)'s ", line)
						if not breaker:
							for entity in tri_list:
								entity.extra += " | " + line
							continue
						else:
							stage_cnt = 0
							stage = 2
							names_cnt = -1
				if stage == 2: #relations
					if stage_cnt < tri_length:
						relation = re.search("(Father|Husband|Mother)'s (.*)", line)
						tri_list[stage_cnt].relation = relation.group(1)
						tri_list[stage_cnt].relation_name = relation.group(2)
						stage_cnt += 1
						continue
					else:
						if line.startswith('Name'):
							names_cnt += 1
							continue
						elif line.startswith('House No'):
							stage_cnt = 0
							stage = 3
						else:
							tri_list[names_cnt].relation_name += " " + line
							continue
				if stage == 3: #house
					if stage_cnt < tri_length:
						house = re.search('House No. (.*)', line)
						if house:
							tri_list[stage_cnt].house = house.group(1)
							stage_cnt += 1
							continue
						else:
							for x in xrange(stage_cnt, len(tri_list)):
								tri_list[x].house = ''
								stage_cnt = 0
								stage = 4						
					else:
						stage_cnt = 0
						stage = 4
				if stage == 4: #sex/age
					if stage_cnt < tri_length:
						age = re.search('Age: (\d*) Sex: (.*)', line)
						if age:
							tri_list[stage_cnt].age = age.group(1)
							tri_list[stage_cnt].sex = age.group(2)
							stage_cnt += 1
						else:
							for x in xrange(stage_cnt, len(tri_list)):
								tri_list[x].age = ''
								tri_list[x].sex = ''
							stage_cnt = tri_length

						if stage_cnt == tri_length:
							for tri in tri_list:								
								csvwriter.writerow([AC_No, AC_Name, PC_No, PC_Name, Main_Village, Police_Station, Tehsil, District, Pin_Code, PS_No, PS_Name, PS_Address, tri.name, tri.extra, tri.house, tri.age, tri.sex, pos[1][0], pos[1][1], tri.relation, tri.relation_name, tri.serial1, tri.serial2])
							tri_list = []
							stage_cnt = 0
							stage = 0

							if not age:
								serial = re.search('(\d*) EPIC NO: (.*)', line)
								entity = Entity()
								entity.serial1 = serial.group(1)
								entity.serial2 = serial.group(2)
								tri_list.append(entity)


if __name__ == '__main__':
	main()