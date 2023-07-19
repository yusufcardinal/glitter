"""
Glitter- A map processor for AoS v0.1

Lets you apply all sorts of post-processing shenanigans to your maps. Featuring everything I was able to come up with.

More information on AoS map format: https://silverspaceship.com/aosmap/aos_file_format.html

"""

from random import uniform as rand
import argparse


# User toggles
debug_mode = False
noise_mono = False
noise_lvl_mono = 1
noise_color = False
noise_lvl_color = 1
grade = False
grade_color = (0,0,0)
ramp_x = False
ramp_x_rev = False
ramp_x_color = (0,0,0)
ramp_x_range = 512
ramp_y = False
ramp_y_rev = False
ramp_y_color = (0,0,0)
ramp_y_range = 512
ramp_z = False
ramp_z_rev = False
ramp_z_color = (0,0,0)
ramp_z_range = 64
shadow = False
shadow_sub = (255,255,255)
rain = False
rain_lvl = 0
snow = False
repair = False

parser = argparse.ArgumentParser(description='Lets you apply all sorts of post-processing shenanigans to your maps. Featuring everything I was able to come up with. More information on AoS map format: https://silverspaceship.com/aosmap/aos_file_format.html',
                                 usage='glitter.py filename [-h] [-d] [-g  [...]] [-nm [...]] [-nc [...]] [-rx  [...]] [-ry  [...]] [-rz  [...]] [-sh  [...]] [-rn [...]] [-sn]')

# Arguments
parser.add_argument('Filename', metavar='filename',
    help="Filename of the map to process (without the .vxl).")
parser.add_argument('-d', '--debug', action='store_true',
    help="Replaces colors with a P-map gradient. Useful for debugging/making sure the script works fine.")
parser.add_argument('-g', '--grade', type=int, metavar='', nargs='+',
    help='Multiplies the map\'s colors with a RGB value. Takes 3 arguments (R, G, B [0-255])')
parser.add_argument('-nm', '--noisemono', metavar='[ ...]', type=int,
    help='Adds monochromatic noise to map. Takes 1 argument (percentage).')
parser.add_argument('-nc', '--noisecolor', metavar='[ ...]', type=int,
    help='Adds chromatic noise to map. Takes 1 argument (percentage).')
parser.add_argument('-rx', '--rampx', metavar='', type=int, nargs='+',
    help='Ramps X axis of the map. Takes 5 arguments (R, G, B [0-255], reversed [0-1], range[0-512]')
parser.add_argument('-ry', '--rampy', metavar='', type=int, nargs='+',
    help='Ramps Y axis of the map. Takes 5 arguments (R, G, B [0-255], reversed [0-1], range[0-512]')
parser.add_argument('-rz', '--rampz', metavar='', type=int, nargs='+',
    help='Ramps Z axis of the map. Takes 5 arguments (R, G, B [0-255], reversed [0-1], range[0-64]')
parser.add_argument('-sh', '--shadow', metavar='', type=int, nargs='+',
    help='Substracts input as shadows. Takes 3 arguments (R, G, B [0-255])'
                    '\n\n(cringe feature don\'t use. OpenSpades already renders shadows.)')
parser.add_argument('-rn', '--rain', metavar='[ ...]', type=int,
    help='Adds rain to the map. Takes 1 argument (percentage).')
parser.add_argument('-sn', '--snow', action='store_true',
    help='Adds snow to the map.')
parser.add_argument('-rp', '--repair', action='store_true',
    help='Fixes alpha channel issue with some file editors.')
parser.add_argument('-gc', '--glowcompliant', action='store_true',
    help='Ensures the fed glow map keeps')
args = parser.parse_args()

mapName = args.Filename

if args.repair:
    repair = True
if args.debug:
    debug_mode = True
if args.noisemono:
    noise_mono = True
    noise_lvl_mono = args.noisemono/100
if args.noisecolor:
    noise_color = True
    noise_lvl_color = args.noisecolor/100
if args.snow:
    snow = True
if args.rain:
    rain = True
    rain_lvl = (args.rain/100)*255
if args.shadow:
    shadow = True
    shadow_sub = (args.shadow[0],args.shadow[1],args.shadow[2])
if args.grade:
    grade = True
    grade_color = (args.grade[0], args.grade[1], args.grade[2])
if args.rampx:
    ramp_x = True
    ramp_x_color = (args.rampx[0],args.rampx[1],args.rampx[2])
    ramp_x_rev = args.rampx[3]
    ramp_x_range = args.rampx[4]
if args.rampy:
    ramp_y = True
    ramp_y_color = (args.rampy[0], args.rampy[1], args.rampy[2])
    ramp_y_rev = args.rampy[3]
    ramp_y_range = args.rampy[4]
if args.rampz:
    ramp_z = True
    ramp_z_color = (args.rampz[0],args.rampz[1],args.rampz[2])
    ramp_z_rev = args.rampz[3]
    ramp_z_range = args.rampz[4]

# PROCESS POOLS

BYTES = []
SPANS = []
COLUMNS = []

# x, y are stored in MAP[x,y] . z is stored in spans
ZINDEX = []
ZOFFSET = []
MAP = {}


BYTESPROC = []


def process_block(x, y, zlist, zft, span, ispan):
    # rdmr is random streak lengths along spans (used in rain)
    rdmr = rand(5, 20)
    for z in zlist:
        # Index of colored block within span
        r, g, b = 6+(z*4), 5+(z*4), 4+(z*4)
        
        # Add offset to Z index for correct height-based shading
        toplength = span[2] - span[1] + 1
        if z > toplength:
            zi = z+zft
        else:
            zi = z+span[1]

        # Shading
        R, G, B = span[r], span[g], span[b]
        if repair:
            a = 7+(z*4)
            span[a] = 255
        if snow:
            if z == 0 and ispan == 0:
                rdm = rand(0, 0.05)
                R, G, B = int(250-(250*rdm)), int(250-(250*rdm)), int(250-(250*rdm))
        if rain:
            if z < rdmr and ispan == 0:
                if z != 0:
                    rfactor = (rain_lvl/100)*(abs(z-rdmr)/rdmr)
                    R, G, B = int(R - (R*rfactor)), int(G - (G*rfactor)), int(B - (B*rfactor))
                else:
                    rfactor = (rain_lvl/100)
                    R, G, B = int(R - (R*rfactor)), int(G - (G*rfactor)), int(B - (B*rfactor))
        if shadow:
            if z > toplength or ispan != 0:
                R, G, B = int(R - shadow_sub[0]), int(G - shadow_sub[1]), int(B - shadow_sub[2])
        if grade:
            R, G, B = int(R * grade_color[0]/255), int(G * grade_color[1]/255), int(B * grade_color[2]/255)
        if ramp_x:
            if ramp_x_rev == 1:
                rx = abs(x-512)/ramp_x_range
            else:
                rx = x/ramp_x_range
            rmpx = (rx*ramp_x_color[0], rx*ramp_x_color[1], rx*ramp_x_color[2])
            R, G, B = int(R + rmpx[0]), int(G + rmpx[1]), int(B + rmpx[2])
        if ramp_y:
            if ramp_y_rev == 1:
                ry = abs(y-512)/ramp_y_range
            else:
                ry = y/ramp_y_range
            rmpy = (ry*ramp_y_color[0], ry*ramp_y_color[1], ry*ramp_y_color[2])
            R, G, B = int(R + rmpy[0]), int(G + rmpy[1]), int(B + rmpy[2])
        if ramp_z:
            if ramp_z_rev == 1:
                rz = abs(zi-64)/ramp_z_range
            else:
                rz = zi/ramp_z_range
            rmpz = (rz*ramp_z_color[0], rz*ramp_z_color[1], rz*ramp_z_color[2])
            R, G, B = int(R + rmpz[0]), int(G + rmpz[1]), int(B + rmpz[2])
        if noise_mono:
            rdm = rand(0, noise_lvl_mono)
            R, G, B = int(R - (R * rdm)), int(G - (G * rdm)), int(B - (B * rdm))
        if noise_color:
            R, G, B = int(R - (R * rand(0, noise_lvl_color))), int(G - (G * rand(0, noise_lvl_color))), int(B - (B * rand(0, noise_lvl_color)))
        if debug_mode:
            R, G, B = int((x / 512) * 255), int((y / 512) * 255), int((zi / 64) * 255)
        if R < 0:
            R = 0
        if G < 0:
            G = 0
        if B < 0:
            B = 0
        if R > 255:
            R = 255
        if G > 255:
            G = 255
        if B > 255:
            B = 255
        span[r], span[g], span[b] = R, G, B

def segmentBytes(N, byt):

    S = N + 1
    E = N + 2
    A = N + 3
    K = byt[E] - byt[S] + 1
    Z = (byt[N] - 1) - K
    span = []
    zlist = []
    if byt[N] == 0:
        Z = 0
        step = (4 * (1 + (byt[E] - byt[S] + 1)))
        for b in range(N, step + N):
            span.append(byt[b])
        SPANS.append(span)
        spancopy = SPANS.copy()
        COLUMNS.append(spancopy)
        SPANS.clear()
        M = 64
        zoffset = byt[E]
    else:
        step = byt[N] * 4
        for b in range(N, step + N):
            span.append(byt[b])
        SPANS.append(span)
        M = N + step + 3
        zoffset = byt[M] - Z
    if M != 64:
        for z in range(0, byt[N]-1):
            zlist.append(z)
    else:
        for z in range(byt[S], byt[E] + 1):
            zlist.append(z - byt[S])
    return step + N, zlist, zoffset


def orderbytes():
    byt = BYTES
    lbyte = len(byt)
    index1 = 0
    while index1 < lbyte:
        # Separates bytes by span > columns, stores points' Z index (byte offset of their Z color).
        calcul = segmentBytes(index1, byt)
        index1 = calcul[0]
        ZINDEX.append(calcul[1])
        ZOFFSET.append(calcul[2])

    col = COLUMNS
    lcol = len(col)
    for i in range(0, lcol):
        y = i
        rc = 0
        while y >= 512:
            y -= 512
            rc += 1
        x = rc
        coords = tuple((x, y))

        MAP[coords] = col[i]



with open(mapName + ".vxl", "rb") as f:
    while (byte := f.read(1)):
        value = int.from_bytes(byte, byteorder='little', signed=False)
        BYTES.append(value)
print("File opened. (" + str(len(BYTES)) + " bytes)")
print("Decoding file structure...")

orderbytes()

if SPANS:
    print("WARNING! Spans omitted during bytes ordering. File may be corrupted.")
if len(COLUMNS) != 512**2:
    print("WARNING! Number of columns does not equal 512x512. File may be corrupted. (Expected 262144, got " + str(len(COLUMNS)) + ")")


print("Shading blocks...")

zn = 0
for x in range(512):
    for y in range(512):
        map = MAP[x,y]
        ispan = 0
        for span in map:
            zlist = ZINDEX[zn]
            zft = ZOFFSET[zn]
            process_block(x, y, zlist, zft, span, ispan)
            zn += 1
            ispan += 1
        for i in range(len(map)):
            for b in map[i]:
                BYTESPROC.append(b)


if len(BYTESPROC) == len(BYTES):
    print("Success!")
else:
    print("WARNING! Output is not the same size as input. Is your .vxl file broken?")

print("Writing to disk as \"" + mapName + "-edit.vxl\"...")
with open(mapName + "-edit.vxl", "wb") as f:
    exportBytes = bytearray(BYTESPROC)
    f.write(exportBytes)
    f.close()
