#!/usr/bin/env python

import sys
import matplotlib.pyplot as plt
from osgeo import gdal

try:
    import numpy as Numeric
except ImportError:
    import Numeric


# =======================================get lat lon and elevation,and write to a csv

def Usage():
    print('Usage: gdal2xyz.py [-skip factor] [-srcwin xoff yoff width height]')
    print('                   [-band b] [-csv] srcfile [dstfile]')
    print('')
    sys.exit(1)

if __name__ == '__main__':

    srcwin = None
    skip = 1
    srcfile = ''
    dstfile = ''
    pngfile = ''
    band_nums = []
    delim = ','

    gdal.AllRegister()
    argv = gdal.GeneralCmdLineProcessor(sys.argv)
    if argv is None:
        sys.exit(0)

    # Parse command line arguments.
    i = 1
    while i < len(argv):
        arg = argv[i]

        if arg == '-srcwin':
            srcwin = (int(argv[i + 1]), int(argv[i + 2]),
                      int(argv[i + 3]), int(argv[i + 4]))
            i = i + 4

        elif arg == '-skip':
            skip = int(argv[i + 1])
            i = i + 1

        elif arg == '-band':
            band_nums.append(int(argv[i + 1]))
            i = i + 1

        elif arg == '-csv':
            delim = ','

        elif arg[0] == '-':
            Usage()

        elif srcfile == '':
            srcfile = arg
            
        elif dstfile == '':
            dstfile = srcfile.replace('.img','.csv')

        else:
            Usage()

        i = i + 1

    if srcfile is None:
        Usage()

    if band_nums == []:
        band_nums = [1]
    # Open source file.
    srcds = gdal.Open(srcfile)
    if srcds is None:
        print('Could not open %s.' % srcfile)
        sys.exit(1)

#=====================================save png
    # pngfile=srcfile.replace('.img','.png')
    # tband=srcds.GetRasterBand(1)
    # elev=tband.ReadAsArray()
    # plt.imsave(pngfile,elev,format='png',cmap='gist_earth')
#============================================

    bands = []
    for band_num in band_nums:
        band = srcds.GetRasterBand(band_num)
        if band is None:
            print('Could not get band %d' % band_num)
            sys.exit(1)
        bands.append(band)

    gt = srcds.GetGeoTransform()

    # Collect information on all the source files.
    if srcwin is None:
        srcwin = (0, 0, srcds.RasterXSize, srcds.RasterYSize)

    # Open the output file.
    dstfile=srcfile.replace('.img','.csv')

    if dstfile is not None:
        dst_fh = open(dstfile, 'wt')
    else:
        dst_fh = sys.stdout

    dt = srcds.GetRasterBand(1).DataType
    if dt == gdal.GDT_Int32 or dt == gdal.GDT_UInt32:
        band_format = (("%d" + delim) * len(bands)).rstrip(delim) + '\n'
    else:
        band_format = (("%g" + delim) * len(bands)).rstrip(delim) + '\n'

    # Setup an appropriate print format.
    if abs(gt[0]) < 180 and abs(gt[3]) < 180 \
       and abs(srcds.RasterXSize * gt[1]) < 180 \
       and abs(srcds.RasterYSize * gt[5]) < 180:
        frmt = '%.10g' + delim + '%.10g' + delim + '%s'
    else:
        frmt = '%.3f' + delim + '%.3f' + delim + '%s'

    # Loop emitting data.

    step=0

    for y in range(srcwin[1], srcwin[1] + srcwin[3], skip):

        data = []
        for band in bands:

            band_data = band.ReadAsArray(srcwin[0], y, srcwin[2], 1)
            band_data = Numeric.reshape(band_data, (srcwin[2],))
            data.append(band_data)

        for x_i in range(0, srcwin[2], skip):
            step+=1
            x = x_i + srcwin[0]

            geo_x = gt[0] + (x + 0.5) * gt[1] + (y + 0.5) * gt[2]
            geo_y = gt[3] + (x + 0.5) * gt[4] + (y + 0.5) * gt[5]

            x_i_data = []
            for i in range(len(bands)):
                x_i_data.append(data[i][x_i])

            band_str = band_format % tuple(x_i_data)

            line = frmt % (float(geo_x), float(geo_y), band_str)

#========================set the img pixel level===================================
            if step == 10:
                dst_fh.write(line)
                step=0

    print('succeed')
    