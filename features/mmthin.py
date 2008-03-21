# Copyright (C) 2006--2008  Murphy Lab
# Carnegie Mellon University
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

from numpy import *
from scipy.ndimage import binary_hit_or_miss
from scipy.misc.pilutil import imshow
from ..imageprocessing.bbox import bbox

__all__ = ['mmthin']

def mmthin(binimg):
    """
    skel = mmthin(binimg)
    image transformation by thinning

    rewrite the mmthin function in the morphological toolbox
    This code is written by yenixsa and Sam in Summer 2004
    Last updated on 12/3/2005
    Ported to Python by LPC on Feb 2008
    """

    binimg=binimg.copy()
    degrees = 45;
    num_elem = abs(360//degrees)

    struct_elem = []
    struct_elem.append([
            [0,0,0],
            [2,1,2],
            [1,1,1]])
    struct_elem.append([
            [2,0,0],
            [1,1,0],
            [1,1,2]])
    struct_elem.append([
            [1,2,0],
            [1,1,0],
            [1,2,0]])
    struct_elem.append([
            [1,1,2],
            [1,1,0],
            [2,0,0]])
    struct_elem.append([
            [1,1,1],
            [2,1,2],
            [0,0,0]])
    struct_elem.append([
            [2,1,1],
            [0,1,1],
            [0,0,2]])
    struct_elem.append([
            [0,2,1],
            [0,1,1],
            [0,2,1]])
    struct_elem.append([
            [0,0,2],
            [0,1,1],
            [2,1,1]])

    struct_elem=[array(E) for E in struct_elem]
    min1,max1,min2,max2 = bbox(binimg)
    r,c=(max1-min1+1,max2-min2+1)
    acnum_elem = 0;
    total_op=0

    image_exp = zeros((r+2, c+2),int8)
    imagebuf = zeros((r+2,c+2),int8)
    image_exp[1:r+1, 1:c+1] = binimg[min1:max1+1,min2:max2+1]
    while True:
        newimg=hitmiss(image_exp,struct_elem[acnum_elem],imagebuf)
        image_exp -= newimg
        total_op += fastany(newimg)

        acnum_elem +=  1;
        if acnum_elem == num_elem:
            if total_op == 0:
                break
            acnum_elem = 0
            total_op = 0
    binimg[min1:max1+1,min2:max2+1] = image_exp[1:r+1, 1:c+1]
    return binimg

def hitmiss(binimg,struct_elem,result = None):
    '''
    Implementation of hit-or-miss operation

    result,ops = hitmiss(binimg, struct_elem, result = None)

    @param result: A matrix of the same shape as binimg to hold the results.

    Returns result and ops == result.sum() [it is just easier to compute it directly]
    '''
# Adapted from ml_mmhitmiss and ported to python by Luis Pedro Coelho

    assert struct_elem.shape == (3,3)
    r,c=binimg.shape
    if result is None:
        result= empty((r,c))
    try:
        from scipy import weave
        from scipy.weave import converters
        code = '''
#line 105 "mmthin.py"
        for (int y = 0; y != r-1 ; ++y) {
            for (int x = 0; x != c-1; ++x) {
                result(y+1,x+1) = 0;
                for (int w = 0; w != 3; ++w) {
                    for (int z = 0; z != 3; ++z) {
                        if (struct_elem(w,z) != binimg(y+w,x+z) && struct_elem(w,z) != 2) {
                             goto next_position; // break out of the loop
                        }
                    }
                }
                result(y+1,x+1) = 1;
                next_position:  /* nothing */ ;
            }
        }
        '''
        weave.inline(code,
            ['r','c','binimg','result','struct_elem'],
            type_converters=converters.blitz
            )
    except Exception, e:
        print 'Weave failed. Resorting to (slow) python code'
        for y in xrange(r-2):
            for x in xrange(c-2):
                hits = 0
                for w in xrange(3):
                    for z in xrange(3):
                        if struct_elem[w,z] == binimg[y+w,x+z] or struct_elem[w,z] == 2:
                            hits += 1
                if hits == 9:
                    result[y+1,x+1]=1
                else:
                    results[y+1,x+1]=0
    return result

def fastany(A):
    try:
        from scipy import weave
        from scipy.weave import converters
        r,c=A.shape
        code = '''
#line 150 "mmthin.py"
        return_val = 0;
        for (int y = 0; y != r ; ++y) {
            for (int x = 0; x != c; ++x) {
                if (A(y,x) != 0) {
                    return_val = 1;
                    goto finished;
                }
            }
        }
        finished: /* do nothing*/ ;
        '''
        return weave.inline(code,
            ['r','c','A'],
            type_converters=converters.blitz
            )
    except Exception, e:
        print 'SLOW: ', e
# vim: set ts=4 sts=4 sw=4 expandtab smartindent:
