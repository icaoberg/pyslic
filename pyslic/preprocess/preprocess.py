# -*- coding: utf-8 -*-
# Copyright (C) 2008  Murphy Lab
# Carnegie Mellon University
# 
# Written by Luis Pedro Coelho <lpc@cmu.edu>
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
import numpy as np
from ..image import Image
from ..imageprocessing.basics import fullhistogram, majority_filter
from ..imageprocessing.thresholding import rc
from mahotas.bbox import bbox
from numpy import *
from warnings import warn
fn = np

__all__ = ['preprocessimg','bgsub']

def preprocessimage(image, regionid, crop=True, options = {}):
    """
    Preprocess the image

    image should be an Image object
    regionid should be an integer, which indexes into image.region

    options is a dictionary. The following options are accepted:

        + 'bgsub.way': One of
            - 'ml' (default) 
            - 'mb' and controls whether the region is selected prior to preprocessing
         + '3d.mode': One of
            - 'perslice' (default): process each slice separately
         + 'threshold.algorithm': One of
            - 'rc': Riddlar-Calvard
            - 'mean':  Image mean
    """
    def preprocessimg(img):
        if len(img.shape) > 2:
            assert len(img.shape) == 3, "Cannot handle images of more than 3 dimensions."
            if options.get('3d.mode','perslice') == 'perslice':
                nr_slices=img.shape[0]
                out_proc=img.copy()
                out_res=img.copy()
                for z in xrange(nr_slices):
                    proc,res=preprocessimg(img[z])
                    out_proc[z]=proc
                    out_res[z]=res
                return out_proc,out_res
            else:
                raise Exception('pyslic.preprocessimg: Do not know how to handle 3d.mode: %s' % options['3d.mode'])
        img=img.copy()
        cropimg=image.regions
        if cropimg is not None:
            if options.get('bgsub.way','ml') == 'ml':
                img *= (cropimg == regionid)
                img = bgsub(img,options)
            else:
                img = bgsub(img,options)
                img *= (cropimg == regionid)
        elif regionid != 1:
            warn('Selecting a region different from 1 for an image without region information')
        imgscaled=_scale(img)
        T=thresholdfor(imgscaled,options)
        mask=(imgscaled > T)
        mask=majority_filter(mask)
        residual=img.copy()
        img *= mask.astype(bool)
        residual *= ~mask
        return img,residual
    image.lazy_load()
    image.channeldata['procprotein'],image.channeldata['resprotein'] = preprocessimg(image.channeldata['protein'])
    if 'dna' in image.channeldata:
        image.channeldata['procdna'],_ = preprocessimg(image.channeldata['dna'])

    if crop:
        fullimage = (image.channeldata['procprotein'] > 0) | (image.channeldata['resprotein'] >0)
        if 'dna' in image.channeldata:
            fullimage |= (image.channeldata['procdna'] > 0)

        min1,max1,min2,max2 = bbox(fullimage)
        border = 2
        min1 = max(0, min1 - border)
        min2 = max(0, min2 - border)
        max1 += border
        max2 += border


        image.channeldata['procprotein'] = image.channeldata['procprotein'][min1:max1,min2:max2]
        image.channeldata['resprotein'] = image.channeldata['resprotein'][min1:max1,min2:max2]
        if 'dna' in image.channeldata:
            image.channeldata['procdna'] = image.channeldata['procdna'][min1:max1,min2:max2]


def thresholdfor(img,options = {}):
    type = options.get('threshold.algorithm','rc')
    if type == 'rc':
        return rc(img,ignore_zeros=True)
    elif type == 'mean':
        return img.mean()
    else:
        raise KeyError('Threshold option not recognised (%s).' % type)

def bgsub(img,options = {}):
    '''
    bgsub(img,options = None)

    Background subtract img (which must be a numpy-type array).

    Changes are done inplace and the img is returned. Use the following idiom for operating on a copy:

    B = bgsub(A.copy(),options)
    '''
    type=options.get('bgsub.type','lowcommon')
    if type == 'nobgsub':
        return img
    elif type == 'lowcommon':
        hist=fullhistogram(img)
        M=round(img.mean())-1
        if M <= 0:
            T=0
        else:
            T=argmax(hist[:M])
        img -= minimum(img,T)
        return img
    else:
        raise KeyError('Background subtraction option not recognised (%s).' % type)

def _scale(img):
    '''
    scaled = _scale(img)

    Returns a scaled version of img, where
        scaled.min() ~= 0
        scaled.max() ~= 255
    '''
    img = img.astype(np.float_)
    M = img.max()
    m = img.min()
    if M == m:
        return np.zeros(img.shape,np.uint8)
    img -= m
    img *= 255/(M-m)
    return img.astype(np.uint8)

# vim: set ts=4 sts=4 sw=4 expandtab smartindent:
