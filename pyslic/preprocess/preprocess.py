from __future__ import division
from ..image import Image
from ..imageprocessing.basics import fullhistogram, majority_filter
from ..imageprocessing.thresholding import rc
from numpy import *
from warnings import warn

__all__ = ['preprocessimg','bgsub']

def preprocessimage(image,regionid,options = {}):
    """
    Preprocess the image

    image should be an Image object
    regionid should be an integer
    options is a dictionary:
        'bgsub.way' can be 'ml' (default) or 'mb' and controls whether the region is selected prior to
                    to preprocessing
    """
    def preprocessimg(img):
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
    img=image.channeldata[Image.protein_channel]
    image.channeldata[Image.procprotein_channel],image.channeldata[Image.residualprotein_channel]=preprocessimg(image.channeldata[Image.protein_channel])
    if Image.dna_channel in image.channeldata:
        image.channeldata[Image.procdna_channel],_=preprocessimg(image.channeldata[Image.dna_channel])


def thresholdfor(img,options = {}):
    type = options.get('threshold.algorithm','rc')
    if type == 'rc':
        return rc(img,remove_zeros=True)
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
    img=asarray(img,uint32)
    M=img.max()
    m=img.min()
    return (img-m)*255/(M-m)

# vim: set ts=4 sts=4 sw=4 expandtab smartindent: