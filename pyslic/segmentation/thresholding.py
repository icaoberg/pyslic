# -*- coding: utf-8 -*-
# Copyright (C) 2008  Murphy Lab
# Carnegie Mellon University
# 
# Written by Luís Pedro Coelho <lpc@cmu.edu>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published
# by the Free Software Foundation; either version 2 of the License,
# or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA
# 02110-1301, USA.
#
# For additional information visit http://murphylab.web.cmu.edu or
# send email to murphy@cmu.edu

from __future__ import division
import numpy
from ..imageprocessing import thresholding, basics
from ..image import Image, loadedimage
from scipy import ndimage

def threshold_segment(dna, smooth=None,threshold_method='otsu',median_size=5, min_obj_size=2500):
    '''
    labeled = threshold_method(dna, threshold_method='otsu',median_size=5,min_obj_size=2500)

    Simple threshold-based segmentation

    Params
    ------
        * dna: either a pyslic.Image or a DNA image
        * smooth: either None (no smoothing) or a sigma value for a gaussian blur (default: None)
        * threshold_method: thresholding method to use. Can be either a function or 
            string which denotes the name of a function in pyslic.imageprocessing.thresholding (default: otsu)
        * median_size: median filter size (default: 5)
        * min_obj_size: minimum object size (default: 2500)
    '''
    if type(dna) == Image:
        with loadedimage(dna):
            return threshold_segment(dna.get('dna'),threshold_method,median_size,min_obj_size)
    if smooth is not None:
        dna = ndimage.gaussian_filter(dna,smooth)
    T = threshold(dna,threshold_method)
    binimg = (basics.majority_filter(dna > T, median_size))
    L,N = ndimage.label(binimg)
    if N == 0:
        return L
    sizes = numpy.array(ndimage.sum(binimg,L,numpy.arange(N+1)))
    for oid in numpy.where(sizes < min_obj_size)[0]:
        L[L == oid] = 0
    L,N = ndimage.label(L != 0)
    return L


# vim: set ts=4 sts=4 sw=4 expandtab smartindent:
