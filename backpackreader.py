#!/usr/bin/env python3
import os, json, sys, requests, time
from shutil import rmtree,make_archive
getMD5 = lambda file: \
         "https://cdn.assets.scratch.mit.edu/internalapi/asset/" + file + "/get"
item_json = None
json_obj = None
cur_file = None
backpack = None
cur_file_data = ""
script_num = 0
normal = True
suppress = False
verbose = False
user_input = False
overwrite = False
nozipsprites = False
wrap_scripts_in_sprites = False
script_json = """{
	"objName": "%s",
	"scripts": [[5, 5, %s]],
	"costumes": [{
			"costumeName": "costume1",
			"baseLayerID": 0,
			"baseLayerMD5": "d36f6603ec293d2c2198d3ea05109fe0.png",
			"bitmapResolution": 2,
			"rotationCenterX": 0,
			"rotationCenterY": 0
		}],
	"currentCostumeIndex": 0,
	"scratchX": 0,
	"scratchY": 0,
	"scale": 1,
	"direction": 90,
	"rotationStyle": "normal",
	"isDraggable": false,
	"indexInLibrary": 100000,
	"visible": true,
	"spriteInfo": {
	}
}"""
def usage():
    print("""\
python3 backpackreader3.py [options] [/path/to/file]

To use this utility correctly you'll need to log in and go to \
"https://scratch.mit.edu/internalapi/backpack/{YOUR USERNAME}/get/".
From there, copy the contents of the page into a text file (e.g. backpack.txt)
and pass the filename to this utility as an argument. If you don't pass a
filename to the command, it will try to read from "./backpack.txt".

This tool saves your Scratch 2.0 backpack to a folder on your computer.
That's right, it wasn't deleted when Scratch 3.0 came around, it's still there!

The contents are saved in these formats:
    Sprites: a .sprite2 file (zipped folder)
    Costumes/Images and Sounds: a folder containing the costume/sound
    Scripts: JSON text (or wrapped in a sprite folder).

NOTE: Sprites that had scripts wrapped into them don't work (yet?), therefore
      only the raw JSON text data of the scripts will be saved unless specified.

Options:
\t--    Empty argument, allows the program to run without extra args.

\t-h    Prints this text and abruptly exits.

\t-n    Automatically renames the folder name of an entry if it clashes
        with the folder name of another created entry.
        This is on by default.
        Turning this on turns -u and -o off.

\t-o    Automatically overwrites entries when the current entry's name
        clashes with an already added entry. This flag is not recommended.
        Turning this flag on turns -u and -n off.

\t-s    Suppresses all output from this command.
        Turning this flag on turns -v off.

\t-u    Alerts the user when the current entry's name clashes with an
        already existing one. The user can then either save the entry
        under a predesignated name, overwrite the old entry or
        abruptly exit.
        Turning this flag on turns -o and -n off.

\t-v    Turns verbose output on.
        Turning this flag on turns -s off.

\t--no-zip-sprites
        All extracted sprites won't automatically be zipped into
        .sprite2 files.

\t--wrap-scripts-in-sprites
        All scripts will be wrapped in sprites. Currently, the sprites
        made from this won't load, therefore those sprites won't be
        zipped.

\t--version
        Prints the version number and exits.
        
This tool was created on April 16, 2020 by Zexxerd (1a3c5e7g9i on Scratch).
This tool requires at least Python3.6.
""")
    sys.exit()
def user_mkdir(d):
    """Safely makes a new directory.
Requires user input if the folder already exists.
Returns the relative filepath to the folder."""
    alt_d = ''
    if os.path.isdir(d):
        i = 1
        while os.path.isdir(f"-{i}".join(os.path.splitext(d))):
            i+=1
        alt_d = f" ({i})".join(os.path.splitext(d))
        print(f"Warning: Folder {d} already exists. Make a new folder {alt_d}?",file=sys.stderr)
        yn = input("Y/N ")
        if yn in "Yy":
            os.mkdir(alt_d)
            return os.getcwd() + '/' + alt_d
        else:
            print(f"Delete {d} and all of its contents?",file=sys.stderr)
            yn = input("Y/N ")
            if yn in "Yy":
                rmtree(d)
                os.mkdir(d)
                print(f"{d} was deleted.")
                return os.getcwd() + '/' + d
            else:
                raise OSError(f"Folder exists: {d}")
    else:
        os.mkdir(d)
        return os.getcwd() + '/' + d

def safe_mkdir(d):
    """Safely makes a new directory. Returns the relative filepath to the folder."""
    alt_d = ''
    if os.path.isdir(d):
        i = 1
        while os.path.isdir(f"-{i}".join(os.path.splitext(d))):
            i+=1
        alt_d = f"-{i}".join(os.path.splitext(d))
        os.mkdir(alt_d)
        return os.getcwd() + '/' + alt_d
    else:
        os.mkdir(d)
        return os.getcwd() + '/' + d

def just_mkdir(d):
    "Makes a new directory, deleting its contents if it already exists."
    if os.path.isdir(d):
        rmtree(d)
    os.mkdir(d)
    return d
if len(sys.argv) == 1:
    usage()
for i in sys.argv[1:]:
    if i[0] == "-":
        if i[1]=="h":
            usage()
        if i[1]=="s":
            suppress = True
            verbose = False
        if i[1]=="v":
            verbose = True
            suppress = False
        if i[1]=="n":
            normal = True
            user_input = False
            overwrite = False
        if i[1]=="u":
            user_input = True
            overwrite = False
            normal = False
        if i[1]=="o":
            overwrite = True
            normal = False
            user_input = False
        if i[1]=="-":
            if i[2:]=="no-zip-sprites":
                nozipsprites = True
            elif i[2:]=="wrap-scripts-in-sprites":
                wrap_scripts_in_sprites = True
            elif i[2:]=="version":
                print("Backpack Reader v0.1")
                sys.exit()
    else:
        backpack = open(i,"r")
backpack = backpack or open("backpack.txt","r")
filename = backpack.name
backpack = json.load(backpack)
backpack_folder = user_mkdir("Backpack")
os.chdir(backpack_folder) #os.getcwd() + '/Backpack'

if verbose:
    print("Input file:",filename)
    print("Flags set:",
          'n'*normal,
          'o'*overwrite,
          'u'*user_input,
          'v')
    print("no-zip-sprites flag set\n"*nozipsprites,end='')
    print("wrap-scripts-in-sprites flag set\n"*wrap_scripts_in_sprites,end='')
del filename
if not suppress:
    sprites = 0
    images = 0
    sounds = 0
    scripts = 0
    for item in backpack:
        if item["type"] == "sprite":
            sprites += 1
        elif item["type"] == "image":
            images += 1
        elif item["type"] == "sound":
            sounds += 1
        elif item["type"] == "script":
            scripts += 1
    print(f"Number of items: {len(backpack)}")
    print(f"Sprites: {sprites}\nImages: {images}\nSounds: {sounds}\nScripts: {scripts}")
now = time.time()
for item in backpack:
    os.chdir(backpack_folder)
    if item['type'] == "sprite":
        if verbose:
            print("Sprite - Name:",item['name'])
        if not overwrite:
            if user_input:
                os.chdir(user_mkdir("Sprite - " + item['name']))
            elif normal:
                os.chdir(safe_mkdir("Sprite - " + item['name']))
        else:
            os.chdir(just_mkdir("Sprite - " + item['name']))
        #cur_file = open("sprite.json","w")
        #cur_file.write(item_json)
        #cur_file.close()
        item_json = requests.get(getMD5(item['md5'])).content.decode('utf-8')
        json_obj = json.loads(item_json)

        if "costumes" in json_obj.keys():
            costume_id = 0
            for costume in json_obj['costumes']:
                #Adjusts the baseLayerID so that projects can use it
                json_obj['costumes'][costume_id]['baseLayerID'] = costume_id
                costume_id += 1
                
                cur_file_data = requests.get(getMD5(costume['baseLayerMD5'])).content
                cur_file = open(str(costume['baseLayerID'])+os.path.splitext(costume['baseLayerMD5'])[1],"wb")
                cur_file.write(cur_file_data)
                cur_file.close()
        if "sounds" in json_obj.keys():
            sound_id = 0
            for sound in json_obj['sounds']:
                cur_file_data = requests.get(getMD5(sound['md5'])).content
                cur_file = open(str(sound_id)+".wav","wb")
                cur_file.write(cur_file_data)
                cur_file.close()
                sound_id+=1
        with open("sprite.json","w") as temp:
            json.dump(json_obj,temp,indent=4)
        if not nozipsprites:
            os.chdir(backpack_folder)
            make_archive("Sprite - " + item['name'],'zip',"Sprite - " + item['name'])
            os.rename("Sprite - " + item['name'] + '.zip',"Sprite - " + item['name'] + '.sprite2')
            rmtree("Sprite - " + item['name'])
            #os.system("zip -r 'Sprite - " + item['name'] + ".zip'
    elif item['type'] == "image":
        if verbose:
            print("Costume - Name:",item['name'])
        if not overwrite:
            if user_input:
                os.chdir(user_mkdir("Costume - " + item['name']))
            elif normal:
                os.chdir(safe_mkdir("Costume - " + item['name']))
        else:
            os.chdir(just_mkdir("Costume - " + item['name']))
            
        with open(item['name']+os.path.splitext(item['md5'])[1],"wb") as temp:
            temp.write(requests.get(getMD5(item['md5'])).content)
            
    elif item['type'] == "sound":
        if verbose:
            print("Sound - Name:",item['name'])
        if not overwrite:
            if user_input:
                os.chdir(user_mkdir("Sound - " + item['name']))
            elif normal:
                os.chdir(safe_mkdir("Sound - " + item['name']))
        else:
            os.chdir(just_mkdir("Sound - " + item['name']))
            
        with open(item['name']+'.wav',"wb") as temp:
            temp.write(requests.get(getMD5(item['md5'])).content)
    elif item['type'] == "script":
        if verbose:
            print(f"Script - #{script_num}")
        if not overwrite:
            if user_input:
                os.chdir(user_mkdir(f"Script - #{script_num}"))
            elif normal:
                os.chdir(safe_mkdir(f"Script - #{script_num}"))
        else:
            os.chdir(just_mkdir(f"Script - #{script_num}"))
        if wrap_scripts_in_sprites:
            with open('0.png','wb') as temp:
                #The bytes of an empty png file.
                #The same bytes as the costume link in the
                #baseLayerMD5 key in the `sprite_json` var
                temp.write(b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x02\x00\x00\x00\x02\x08\x06\x00\x00\x00r\xb6\r$\x00\x00\x00\x0eIDATx\xdaca\x80\x02\x16\x18\x03\x00\x00~\x00\t\x8c\x06i \x00\x00\x00-tEXtSoftware\x00by.blooddy.crypto.image.PNG24Encoder\xa8\x06\x7f\xee\x00\x00\x00\x00IEND\xaeB`\x82')
            cur_file_data = script_json % (f"Script - #{script_num}",item['scripts'][0])
            cur_file = open("sprite.json","w")
            cur_file.write(cur_file_data)
            cur_file.close()
        else:
            with open("script.txt","w") as temp:
                temp.write(str(item['scripts'][0]))
        script_num += 1
    else:
        raise RuntimeError(f"Item type: {item['type']}")
if not suppress:
    print("Time spent:",time.time() - now)
    print("Successful.")
os.chdir("..")
