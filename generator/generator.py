import argparse
import subprocess
import os
import requests
import unicodedata

from PIL import Image
from struct import unpack
from binascii import hexlify
from bannergif import bannergif

parser = argparse.ArgumentParser(description="CTR-NDSForwarder Generator")
parser.add_argument("input", metavar="input.nds", type=str, nargs=1, help="DS ROM path")
parser.add_argument("-o", "--output", metavar="output.cia", type=str, nargs=1, help="output CIA")
parser.add_argument("-b", "--boxart", metavar="boxart.png", type=str, nargs=1, help="Custom banner box art")

args = parser.parse_args()

cmdarg = ""
if os.name != 'nt':
    cmdarg = "./"

path = args.input[0]
err = bannergif(path)
print("Extracting icon...")
if err != 0:
    print("Failed to open ROM. Is the path valid?")
    exit()
else:
    print("Resizing icon...")
    im = Image.open('output.gif')
    im.putpalette(b"\xFF\xFF\xFF" + im.palette.palette[3:])
    im = im.convert('RGB')
    im = im.resize((48, 48), resample=Image.LINEAR)
    im.save('output.png')

    # get banner title
    print("Extracting game metadata...")
    rom = open(args.input[0], "rb")
    rom.seek(0x68, 0)
    banneraddrle = rom.read(4)
    banneraddr = unpack("<I", banneraddrle)[0]
    rom.seek(banneraddr, 0)
    title = []
    haspublisher = False
    for x in range(8):
        offset = 0x240 + (0x100 * x)
        rom.seek(banneraddr + offset, 0)
        title.append(str(rom.read(0x100), "utf-16-le"))
        title[x] = title[x].split('\0', 1)[0]
    jpn_title = title[0].split("\n")
    eng_title = title[1].split("\n")
    fra_title = title[2].split("\n")
    ger_title = title[3].split("\n")
    ita_title = title[4].split("\n")
    spa_title = title[5].split("\n")
    chn_title = title[6].split("\n")
    kor_title = title[7].split("\n")
    if chn_title == [""] or chn_title[0][0] == "\uffff":
        chn_title = None
    if kor_title == [""] or kor_title[0][0] == "\uffff":
        kor_title = None
    rom.seek(0xC, 0)
    gamecode = str(rom.read(0x4), "ascii")
    rom.close()

    print("Creating SMDH...")
    bannertoolarg = f'{cmdarg}bannertool makesmdh -i "output.png" '
    if len(jpn_title) == 3:
        haspublisher = True
    if haspublisher:
        bannertoolarg += f'-s "{eng_title[0]} {eng_title[1]}" -js "{jpn_title[0]} {jpn_title[1]}" -fs "{fra_title[0]} {fra_title[1]}" -gs "{fra_title[0]} {ger_title[1]}" -is "{ita_title[0]} {ita_title[1]}" -ss "{spa_title[0]} {spa_title[1]}" '
        bannertoolarg += f'-l "{eng_title[0]} {eng_title[1]}" -jl "{jpn_title[0]} {jpn_title[1]}" -fl "{fra_title[0]} {fra_title[1]}" -gl "{fra_title[0]} {ger_title[1]}" -il "{ita_title[0]} {ita_title[1]}" -sl "{spa_title[0]} {spa_title[1]}" '
        bannertoolarg += f'-p "{eng_title[2]}" -jp "{jpn_title[2]}" -fp "{fra_title[2]}" -gp "{ger_title[2]}" -ip "{ita_title[2]}" -sp "{spa_title[2]}" '
    else:
        bannertoolarg += f'-s "{eng_title[0]}" -js "{jpn_title[0]}" -fs "{fra_title[0]}" -gs "{fra_title[0]}" -is "{ita_title[0]}" -ss "{spa_title[0]}" '
        bannertoolarg += f'-l "{eng_title[0]}" -jl "{jpn_title[0]}" -fl "{fra_title[0]}" -gl "{ger_title[0]}" -il "{ita_title[0]}" -sl "{spa_title[0]}" '
        bannertoolarg += f'-p "{eng_title[1]}" -jp "{jpn_title[1]}" -fp "{fra_title[1]}" -gp "{ger_title[1]}" -ip "{ita_title[1]}" -sp "{spa_title[1]}" '
    if chn_title is not None:
        if haspublisher:
            bannertoolarg += f'-scs "{chn_title[0]} {chn_title[1]}" '
            bannertoolarg += f'-scl "{chn_title[0]} {chn_title[1]}" '
            bannertoolarg += f'-scp "{chn_title[2]}" '
        else:
            bannertoolarg += f'-scs "{chn_title[0]}" -scl "{chn_title[0]} -scp "{chn_title[1]}" '
    if kor_title is not None:
        if haspublisher:
            bannertoolarg += f'-ks "{kor_title[0]} {kor_title[1]}" '
            bannertoolarg += f'-kl "{kor_title[0]} {kor_title[1]}" '
            bannertoolarg += f'-kp "{kor_title[2]}" '
        else:
            bannertoolarg += f'-ks "{kor_title[0]}" -kl "{kor_title[0]}" -kp "{kor_title[1]}" '
    bannertoolarg += '-o "output.smdh"'
    bannertoolrun = subprocess.Popen(bannertoolarg, shell=True)
    bannertoolrun.wait()

    # get boxart for DS, to make banner
    if not args.boxart:
        print("Downloading boxart...")
        ba_region = ""
        if gamecode[3] in ['E', 'T']:
            ba_region = "US"
        elif gamecode[3] == 'K':
            ba_region = "KO"
        elif gamecode[3] == 'J':
            ba_region = "JA"
        elif gamecode[3] == 'D':
            ba_region = "DE"
        elif gamecode[3] == 'F':
            ba_region = "FR"
        elif gamecode[3] == 'H':
            ba_region = "NL"
        elif gamecode[3] == 'I':
            ba_region = "IT"
        elif gamecode[3] == 'R':
            ba_region = "RU"
        elif gamecode[3] == 'S':
            ba_region = "ES"
        elif gamecode[3] == '#':
            ba_region = "HB"
        elif gamecode[3] == 'U':
            ba_region = "AU"
        else:
            ba_region = "EN"
        r = requests.get(f"https://art.gametdb.com/ds/coverM/{ba_region}/{gamecode}.jpg")
        if r.status_code != 200:
            print("Cannot find box art for game. Are you connected to the internet?")
            exit()
        boxart = open('data/boxart.jpg', 'wb')
        boxart.write(r.content)
        boxart.close()
    else:
        if not os.path.isfile(args.boxart[0]):
            print(f"{args.boxart[0]} does not exist. Is your argument correct?")
            exit()
    print("Resizing box art...")
    banner = Image.open(args.boxart[0] if args.boxart else 'data/boxart.jpg')
    width, height = banner.size
    new_height = 128
    new_width = new_height * width // height
    banner = banner.resize((new_width, new_height), resample=Image.ANTIALIAS)
    new_image = Image.new('RGBA', (256, 128), (0, 0, 0, 0))
    upper = (256 - banner.size[0]) // 2
    new_image.paste(banner, (upper, 0))
    new_image.save('data/banner.png', 'PNG')

    print("Creating banner...")
    bannertoolarg = f"{cmdarg}bannertool makebanner -i data/banner.png -a data/dsboot.wav -o banner.bin"
    bannertoolrun = subprocess.Popen(bannertoolarg, shell=True)
    bannertoolrun.wait()

    # CIA generation
    print("Getting filepath...")
    romfs = open('romfs/path.txt', 'w')
    path = unicodedata.normalize("NFC", os.path.abspath(path))
    if os.name == 'nt':
        path = path[2:]
        path = path.replace('\\', '/')
    else:
        temp = path
        orig_dev = os.stat(temp).st_dev
        while path != '/':
            direc = os.path.dirname(temp)
            if os.stat(direc).st_dev != orig_dev:
                break
            temp = direc
        path = path.replace(temp, "")
    romfs.write(f"sd:{path}")
    romfs.close()

    gamecodehex = hexlify(gamecode.encode()).decode()
    gamecodehex = f"0x{gamecodehex[3:8]}"
    print("Running makerom...")
    makeromarg = f"{cmdarg}makerom -f cia -target t -exefslogo -rsf data/build-cia.rsf -elf data/forwarder.elf -banner banner.bin -icon output.smdh -DAPP_ROMFS=romfs -major 0 -minor 1 -micro 0 -DAPP_VERSION_MAJOR=0 "
    makeromarg += f"-o {args.output[0] if args.output else 'output.cia'} "
    makeromarg += f'-DAPP_PRODUCT_CODE=CTR-H-{gamecode} -DAPP_TITLE="{eng_title[0]}" -DAPP_UNIQUE_ID={gamecodehex}'
    makeromrun = subprocess.Popen(makeromarg, shell=True)
    makeromrun.wait()
    print("CIA generated.")
    exit()