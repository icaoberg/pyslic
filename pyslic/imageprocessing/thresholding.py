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
from numpy import *
from scipy.ndimage import histogram
from .basics import fullhistogram, nonzeromin

__all__=['rc','murphy_rc','otsu','softthreshold','hardthreshold']

def softthreshold(img,T):
    '''
    softthreshold(img,T)


    Implement a soft threshold:
        img[i] = max(img[i]-T,0)

    Processes the image inplace, return a reference to img.

    Use
    B = softthreshold(A.copy(),T)
    to get a copy.

    @see hardthreshold
    '''
    img -= minimum(img,T)
    return img

def hardthreshold(img,T):
    '''
    hardthreshold(img,T)


    Implement a soft threshold:
        img[i] = (img[i] if img[i] > T else 0)

    Processes the image inplace, return a reference to img.

    Use
    B = hardthreshold(A.copy(),T)
    to get a copy.

    @see softthreshold
    '''
    img *= (img > T)
    return img

def rc(img,remove_zeros=False):
    """
    T = rc(img, remove_zeros=False)
    
    Calculate a threshold according to the RC method.

    @param remove_zeros: Whether to ignore zero valued pixels (default: False)
    """
    hist=fullhistogram(img)
    if remove_zeros:
        if hist[0] == img.size:
            return 0
        hist[0]=0
    N=hist.size

    # Precompute most of what we need:
    sum1 = cumsum(arange(N) * hist)
    sum2 = cumsum(hist)
    sum3 = flipud(cumsum(flipud(arange(N) * hist)))
    sum4 = flipud(cumsum(flipud(hist)))

    maxt=N-1
    while hist[maxt] == 0:
        maxt -= 1

    res=maxt
    t=0
    while t < min(maxt,res):
        res=(sum1[t]/sum2[t] + sum3[t+1]/sum4[t+1])/2
        t += 1
    return res
        

def murphy_rc(img,remove_zeros=False):
    """
    T = murphy_rc(img)
    
    Calculate a threshold according to Murphy's adaptation of the RC method.

    @param remove_zeros: Whether to ignore zero valued pixels (default: False)
        Murphy's Matlab implementation always ignores zero valued pixels.
    """
    pmax=img.max()
    return pmax-rc(pmax-img,remove_zeros=remove_zeros)

def otsu(img, remove_zeros=False):
    """
    T = otsu(img)

    Calculate a threshold according to the Otsu method.
    """
    # Calculated according to CVonline: http://homepages.inf.ed.ac.uk/rbf/CVonline/LOCAL_COPIES/MORSE/threshold.pdf
    hist=fullhistogram(img)
    hist=asarray(hist,double) # This forces everything to be double precision
    if remove_zeros:
        hist[0]=0
    Ng=len(hist)
    nB=cumsum(hist)
    nO=nB[-1]-nB
    mu_B=0
    mu_O=(arange(1,Ng)*hist[1:]).sum()/hist[1:].sum()
    best=nB[0]*nO[0]*(mu_B-mu_O)*(mu_B-mu_O)
    bestT=0

    for T in xrange(1,Ng):
        if nB[T] == 0: continue
        if nO[T] == 0: break
        mu_B = (mu_B*nB[T-1] + T*hist[T]) / nB[T]
        mu_O = (mu_O*nO[T-1] - T*hist[T]) / nO[T]
        sigma_between=nB[T]*nO[T]*(mu_B-mu_O)*(mu_B-mu_O)
        if sigma_between > best:
            best = sigma_between
            bestT = T
    return bestT

# vim: set ts=4 sts=4 sw=4 expandtab smartindent:
