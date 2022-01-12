import argparse
import subprocess
import os

from PIL import Image
from struct import unpack
from binascii import hexlify
from bannergif import bannergif

iconsize = (48, 48)

parser = argparse.ArgumentParser(description="CTR-NDSForwarder Generator")
parser.add_argument("input", metavar="input.nds", type=str, nargs=1, help="DS ROM path")
parser.add_argument("-o", "--output", metavar="output.cia", type=str, nargs=1, help="output CIA")

args = parser.parse_args()

path = args.input[0]
err = bannergif(path)
print("Extracting icon...")
if err != 0:
    print("Failed to open ROM. Is the path valid?")
    exit()
else:
    print("Resizing icon...")
    im = Image.open('output.gif')
    im = im.resize(iconsize)
    im.save('output.png')

    # get banner title
    print("Extracting game title...")
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
    if chn_title[0][0] == "\uffff":
        chn_title = None
    if kor_title[0][0] == "\uffff":
        kor_title = None
    print("Creating SMDH...")
    bannertoolarg = 'bannertool makesmdh -i "output.png" '
    bannertoolarg += f'-s "{eng_title[0]}" -js "{jpn_title[0]}" -es "{eng_title[0]}" -fs "{fra_title[0]}" -gs "{ger_title[0]}" -is "{ita_title[0]}" -ss "{spa_title[0]}" '
    if len(jpn_title) == 3:
        haspublisher = True
    if haspublisher:
        bannertoolarg += f'-l "{eng_title[1]}" -jl "{jpn_title[1]}" -el "{eng_title[1]}" -fl "{fra_title[1]}" -gl "{ger_title[1]}" -il "{ita_title[1]}" -sl "{spa_title[1]}" -p "{eng_title[2]}" -jp "{jpn_title[2]}" -ep "{eng_title[2]}" -fp "{fra_title[2]}" -gp "{ger_title[2]}" -ip "{ita_title[2]}" -sp "{spa_title[2]}" '
    else:
        bannertoolarg += f'-l "{eng_title[0]}" -jl "{jpn_title[0]}" -el "{eng_title[0]}" -fl "{fra_title[0]}" -gl "{ger_title[0]}" -il "{ita_title[0]}" -sl "{spa_title[0]}" -p "{eng_title[1]}" -jp "{jpn_title[1]}" -ep "{eng_title[1]}" -fp "{fra_title[1]}" -gp "{ger_title[1]}" -ip "{ita_title[1]}" -sp "{spa_title[1]}" '
    if chn_title is not None:
        bannertoolarg += f'-scs "{chn_title[0]}" '
        if haspublisher:
            bannertoolarg += f'-scl "{chn_title[1]}" -scp "{chn_title[2]}" '
        else:
            bannertoolarg += f'-scl "{chn_title[0]}" -scp "{chn_title[1]}" '
    if kor_title is not None:
        bannertoolarg += f'-ks "{kor_title[0]}" '
        if haspublisher:
            bannertoolarg += f'-kl "{kor_title[1]}" -kp "{kor_title[2]}" '
        else:
            bannertoolarg += f'-kl "{kor_title[0]}" -kp "{kor_title[1]}" '
    bannertoolarg += '-o "output.smdh"'
    bannertoolrun = subprocess.Popen(bannertoolarg, shell=True)
    bannertoolrun.wait()
    print("Getting filepath...")
    romfs = open('romfs/path.txt', 'w')
    if os.name == 'nt':
        path = os.path.abspath(path)
        path = "sd:" + path[2:]
        path = path.replace('\\', '/')
        romfs.write(f"{path}\n")
    else:
        path = os.path.abspath(path)
        temp = path
        orig_dev = os.stat(temp).st_dev
        while path != '/':
            direc = os.path.dirname(temp)
            if os.stat(direc).st_dev != orig_dev:
                break
            temp = direc
        path = path.replace(temp, "")
        romfs.write(f"sd:{path}\n")
    romfs.close()
    rom.seek(0xC, 0)
    gamecode = str(rom.read(0x4), "ascii")
    rom.close()
    gamecodehex = f"0x{hexlify(gamecode.encode()).decode()}"
    gamecodehex = gamecodehex[:-3]
    print("Running makerom...")
    makeromarg = "makerom -f cia -target t -exefslogo -rsf data/build-cia.rsf -elf data/forwarder.elf -icon output.smdh -DAPP_ROMFS=romfs -major 1 -minor 0 -micro 0 -DAPP_VERSION_MAJOR=1 "
    makeromarg += f"-o {args.output[0] if args.output else 'output.cia'} "
    makeromarg += f'-DAPP_PRODUCT_CODE=CTR-H-{gamecode} -DAPP_TITLE="{eng_title[0]}" -DAPP_UNIQUE_ID={gamecodehex}'
    makeromrun = subprocess.Popen(makeromarg, shell=True)
    makeromrun.wait()
    print("CIA generated.")
