import os
import pathlib
import sys, getopt
from bs4 import BeautifulSoup

# Middle C on a piano is C4
# midi note 36 이 Cubase 에서는 C1 인데 AKAI 에서는 C2 다.
# Roland(AKAI) 는 middle c(60) 를 C4 로 쓰고, Yamaha(Cubase) 는 C3 로 쓴다.
# 역사적으로는 Roland C4 가 표준인 거 같지만, 내가 쓰는 대부분의 소프트웨어가 C3 를 쓰므로
# 여기에서는 C3 를 기본값으로 한다.
def get_octave_modifier(using_middle_c_c4):
	if using_middle_c_c4 :
		return 1
	else:
		return 2

def convert_num_to_note(inote, using_middle_c_c4):
	note_array = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
	octave, interval = divmod(inote, 12)
	ret = note_array[interval] + str(octave - get_octave_modifier(using_middle_c_c4))
	return ret

def split_note_octave(inote_str):
	split_index = 1
	if inote_str[1] == "#":
		split_index = 2
	note_str = inote_str[0:split_index]
	octave_str = inote_str[split_index:]
	return note_str, octave_str

def convert_note_to_num(inote_str, using_middle_c_c4):
	note_array = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
	note_str, octave_str = split_note_octave(inote_str)
	octave = int(octave_str)
	note_index = note_array.index(note_str)
	return (octave + get_octave_modifier(using_middle_c_c4)) * 12 + note_index

def get_file_name_without_extension(file_path):
	file_name = os.path.basename(file_path)
	return os.path.splitext(file_name)[0]

def save_drm_as_txt_file(file_path_without_ext, item_list, using_middle_c_c4):
	with open(file_path_without_ext + ".txt", "w") as txt_file:
		for item in item_list:
			note_name = item.find("string")["value"]
			inote_value_str = item.find("int", {"name": "INote"})["value"]
			inote_value = int(inote_value_str)
			str = "|| " + convert_num_to_note(inote_value, using_middle_c_c4) + " || " + note_name + " ||"
			if using_middle_c_c4:
				str += " " + inote_value_str + " ||"
			print(str)
			txt_file.writelines(str + "\n")

def convert_drm_to_txt(file_path):
	file_path_without_ext, _ = os.path.splitext(file_path)
	with open(file_path_without_ext + ".drm", "r") as xml_file:
		soup = BeautifulSoup(xml_file, 'lxml')
		item_map = soup.find("list", {"name": "Map"})
		item_list = item_map.find_all("item")

		save_drm_as_txt_file(file_path_without_ext, item_list, False)
		save_drm_as_txt_file(file_path_without_ext + "_roland_middle_c4", item_list, True)

def convert_txt_to_drm(file_path, using_middle_c_c4):
	file_path_without_ext, _ = os.path.splitext(file_path)
	file_name = get_file_name_without_extension(file_path)
	with open(file_path_without_ext + ".txt", "r") as txt_file, open(file_path_without_ext + ".drm", "w") as xml_file :		
		xml_start = """<?xml version="1.0" encoding="utf-8"?>
<DrumMap>
   <string name="Name" value="%s" wide="true"/>
   <list name="Quantize" type="list">
      <item>
         <int name="Grid" value="4"/>
         <int name="Type" value="0"/>
         <float name="Swing" value="0"/>
         <int name="Legato" value="50"/>
      </item>
   </list>
   <list name="Map" type="list">"""
		xml_file.write(xml_start % file_name)

        # txt 파일을 읽어서 xml 으로 변환한다.
        # 1 부터 127까지 비어있으면 큐베이스의 Pitch 값이 밀려서 표시되므로 꽉 채워줘야 한다.
		list_to_name = ["" for x in range(128)]

		# .txt 파일에서 로딩한 데이터를 list_to_name 에 덮어쓴다.
		lines = txt_file.readlines()
		for line in lines:
			splited_data = line.split("||")
			list_to_name[convert_note_to_num(splited_data[1].strip(), using_middle_c_c4)] = splited_data[2].strip()

		xml_item = """\n      <item>
         <int name="INote" value="{0}"/>
         <int name="ONote" value="{0}"/>
         <int name="Channel" value="-1"/>
         <float name="Length" value="200"/>
         <int name="Mute" value="0"/>
         <int name="DisplayNote" value="{0}"/>
         <int name="HeadSymbol" value="0"/>
         <int name="Voice" value="0"/>
         <int name="PortIndex" value="0"/>
         <string name="Name" value="{1}" wide="true"/>
         <int name="QuantizeIndex" value="0"/>
      </item>"""

		# 0~127 까지 xml node 'item' 를 생성한다.
		for i in range(0, 128):
			print(str(i) + " " + list_to_name[i])
			xml_file.write(xml_item.format(i, list_to_name[i]))

		xml_file.write("""\n   </list>
   <list name="Order" type="int">\n""")

		for i in range(0, 128):
			xml_file.write("""      <item value="{0}"/>\n""".format(i))

		xml_file.write("""   </list>
   <list name="OutputDevices" type="list">
      <item>
         <string name="DeviceName" value="Default Device"/>
         <string name="PortName" value="Default Port"/>
      </item>
   </list>
</DrumMap>""")

def main():
	file_path = input("input file path: ")
	file_ext = pathlib.Path(file_path.lower()).suffix;

	# 확장자에 따라 .drm <-> .txt 로 변환한다.
	if file_ext == ".drm" :
		convert_drm_to_txt(file_path)
	elif file_ext == ".txt" :
		convert_txt_to_drm(file_path, False)

if __name__ == '__main__':
	main()