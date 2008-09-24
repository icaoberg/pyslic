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
from numpy import array, zeros, sqrt, inf, empty

from ..utils import get_pyrandom
from ..classify.normalise import zscore

__all__ = ['kmeans','repeated_kmeans']

def _euclidean2(fmatrix,x):
    try:
        from scipy import weave
        from scipy.weave import converters
        N,q=fmatrix.shape
        D=zeros(N)
        code = '''
        for (int i = 0; i != N; ++i) {
            for (int j = 0; j != q; ++j) {
                D(i) += (fmatrix(i,j) - x(j))*(fmatrix(i,j)-x(j));
            }
        }
        '''
        weave.inline(
                code,
                ['fmatrix','N','q','x','D'],
                type_converters=converters.blitz)
        return D
    except:
        return ((fmatrix - x)**2).sum(1)

def _mahalabonis2(fmatrix,x,icov):
    diff=(fmatrix-x)
    icov=(icov)
    # The expression below seems to be faster than looping over the elements and summing 
    return dot(diff,dot(icov,diff.T)).diagonal()

def centroid_errors(fmatrix,assignments,centroids):
    errors=[]
    for k in xrange(len(centroids)):
        errors.extend(fmatrix[assignments == k] - centroids[k])
    return array(errors)

def residual_sum_squares(fmatrix,assignments,centroids,distance='euclidean',**kwargs):
    if distance != 'euclidean':
        raise NotImplemented, "residual_sum_squares only implemented for 'euclidean' distance"
    return (centroid_errors(fmatrix,assignments,centroids)**2).sum()

def kmeans(fmatrix,K,distance='euclidean',max_iter=1000,R=None,**kwargs):
    '''
    assignmens, centroids = kmean(fmatrix, K, distance='euclidean', icov=None, covmat=None)

    K-Means Clustering

    @param distance can be one of:
        'euclidean'   : euclidean distance (default)
        'seuclidean'  : standartised euclidean distance. This is equivalent to first normalising the features.
        'mahalanobis' : mahalanobis distance.
                This can make use of the following keyword arguments:
                    'icov' (the inverse of the covariance matrix), 
                    'covmat' (the covariance matrix)
                If neither is passed, then the function computes the covariance from the feature matrix
    @param max_iter: Maximum number of iteration
    '''
    fmatrix=numpy.asanyarray(fmatrix)
    if distance == 'euclidean':
        distfunction=_euclidean2
    elif distance == 'seuclidean':
        fmatrix = zscore(fmatrix)
        distfunction=_euclidean2
    elif distance == 'mahalanobis':
        icov = kwargs.get('icov',None)
        if icov is None:
            covmat=kwargs.get('covmat',None)
            if covmat is None:
                covmat=cov(fmatrix.T)
            icov=linalg.inv(covmat)
        distfunction=lambda f,x: _mahalabonis2(f,x,icov)
    else:
        raise 'Distance argument unknown (%s)' % distance
    R=get_pyrandom(R)

    N,q = fmatrix.shape
    centroids = array(R.sample(fmatrix,K))
    prev = zeros(N)
    dists = empty((K,N))
    for i in xrange(max_iter):
        for ci,C in enumerate(centroids):
            dists[ci,:] = distfunction(fmatrix,C)
        assignments = dists.argmin(0)
        if (assignments == prev).all():
            break
        try:
            from scipy import weave
            from scipy.weave import converters
            centroids[:]=0
            counts=zeros(K,numpy.uint32)
            code = '''
            for (int i = 0; i != N; ++i) {
                int c = assignments(i);
                ++counts(c);
                for (int j = 0; j != q; ++j) {
                    centroids(c,j) += fmatrix(i,j);
                }
            }
            for (int i = 0; i != K; ++i) {
                for (int j = 0; j != q; ++j) {
                    centroids(i,j) /= counts(i);
                }
            }
            '''
            weave.inline(
                    code,
                    ['fmatrix','centroids','N','q','K','assignments','counts'],
                    type_converters=converters.blitz)
        except Exception, e:
            print 'scipy.weave.inline failed. Resorting to Python code (Exception was "%s")' % e
            centroids = array([fmatrix[assignments == C].mean(0) for C in xrange(K)])
        prev = assignments
    return assignments, centroids
        
def repeated_kmeans(fmatrix,k,iterations,distance='euclidean',max_iter=1000,R=None,**kwargs):
    '''
    assignments,centroids = repeated_kmeans(fmatrix, k, repeats, distance='euclidean',max_iter=1000,**kwargs)

    Runs kmeans repeats times and returns the best result as evaluated according to distance

    @see kmeans
    '''
    if distance == 'seuclidean':
        fmatrix = zscore(fmatrix)
        distance = 'euclidean'
    if distance != 'euclidean':
        raise NotImplementedError, "repeated_kmeans is only implemented for 'euclidean' or 'seuclidean' distance"
    best=+inf
    for i in xrange(iterations):
        A,C=kmeans(fmatrix,k,distance,max_iter=max_iter,R=R,**kwargs)
        rss=residual_sum_squares(fmatrix,A,C,distance,**kwargs)
        if rss < best:
            Ab,Cb=A,C
            best=rss
    return Ab,Cb
# vim: set ts=4 sts=4 sw=4 expandtab smartindent: