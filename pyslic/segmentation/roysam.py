from collections import defaultdict
import ncreduce
from ..imageprocessing import thresholding
from .. import features
from scipy import ndimage
import pymorph
import morph
import numpy

__all__ = ['roysam_watershed']
def roysam_watershed(dna,thresh=None,blur_factor=3):
    '''
    Run watershed on mixed gradient & intensity image as suggested by Lin et al.

    -Input
    dna:            DNA image
    thresh:         Gray value threshold (default: computed using Murphy's RC)
    blur_factor:    Blur factor (default: 3)
    
    
    REFERENCE
    Gang Lin, Umesh Adiga, Kathy Olson, John F. Guzowski, Carol A. Barnes, and Badrinath Roysam
    "A Hybrid 3-D Watershed Algorithm Incorporating Gradient Cues & Object Models for Automatic
        Segmentation of Nuclei in Confocal Image Stacks"
     Vol. 56A, No. 1, pp. 23-36 Cytometry Part A, November 2003.
    '''
    if thresh is None:
        thresh=thresholding.murphy_rc(dna)
    M=(ndimage.gaussian_filter(dna,4)>thresh)
    G=pymorph.gradm(dna)
    D=ndimage.distance_transform_edt(M)
    D=D*numpy.exp(1-G/float(G.max()))
    T=ndimage.gaussian_filter(D.max() - D,blur_factor)
    T=pymorph.to_uint8(T)
    R=pymorph.regmin(T)
    R,N=ndimage.label(R)
    for i in xrange(R.size):
        if R.flat[i] == 0 and M.flat[i] == 0:
            R.flat[i]=N+1
            break
    W,WL=morph.cwatershed(T*M,R,return_lines=True)
    return W,WL

def border(W,Bc=None):
    '''
    B, neighbours, border_id = border(Regs,Bc=None)

    Label the borders between regions.

    B[y,x] = border_id[r0,r1]
    
    if (y,x) is on the border between regions (r0,r1).
    neighbours is a dict : (region) -> (list of regions)

    -Input:
    Regs:   A labeled image
    Bc:     A structuring element (default: 3x3 cross)
    '''
    if Bc is None: Bc = pymorph.secross()
    V,_=pymorph.mat2set(Bc)
    shapea=numpy.array(W.shape)
    B=W*0
    bg=W.max()
    neighbours=defaultdict(set)
    border_id=defaultdict(xrange(1,W.max()**2).__iter__().next)
    for pos,val in numpy.ndenumerate(W):
        if val and val != bg:
            for vi in V:
                if ncreduce.all((pos+vi)>=0) and ncreduce.all((pos+vi)<shapea):
                    other=W[tuple(pos+vi)]
                    if other and other != bg and other != val:
                        a1,a2=min(other,val),max(other,val)
                        B[tuple(pos)]=border_id[(a1,a2)]
                        neighbours[a1].add(a2)
                        neighbours[a2].add(a1)
    return B, neighbours, border_id

class Merger(object):
    '''
    Implements Roysam's region merging algorithm.

    REFERENCE
    Gang Lin, Umesh Adiga, Kathy Olson, John F. Guzowski, Carol A. Barnes, and Badrinath Roysam
    "A Hybrid 3-D Watershed Algorithm Incorporating Gradient Cues & Object Models for Automatic
        Segmentation of Nuclei in Confocal Image Stacks"
     Vol. 56A, No. 1, pp. 23-36 Cytometry Part A, November 2003.
    '''

    def __init__(self,dna):
        '''
        M = Merged(dna)
        '''
        self.C=pymorph.gradm(dna)
        self.W,self.WL=roysam_watershed(dna)
        self.B,self.neighbours,self.border_id=border(self.W)
        self.border_regions=dict((y,x) for x,y in self.border_id.iteritems())

    def _merge(self,c0,c1):
        '''Merge region c0 & c1'''
        self.W[self.W==c1]=c0
        self.neighbours[c0].remove(c1)
        self.neighbours[c1].remove(c0)
        self.neighbours[c0].update(self.neighbours[c1])
        del self.neighbours[c1]
        for v in self.neighbours.values():
            if c1 in v:
                v.remove(c1)
                v.add(c0)
        b=self.border_id[min(c0,c1),max(c0,c1)]
        del self.border_id[min(c0,c1),max(c0,c1)]
        self.B[self.B==b]=0
        for (r0,r1),b in self.border_id.items():
            if r0 == c1 or r1 == c1:
                del self.border_id[r0,r1]
                if r1 == c1: r1=r0
                d0,d1=min(r1,c0),max(r1,c0)
                if (d0,d1) in self.border_id:
                    self.B[self.B==b] = self.border_id[d0,d1]
                else:
                    self.border_id[d0,d1]=b
                
    def _Rw(self,c0,c1):
        '''Implement Rw in the paper.'''
        def RSw(c0,c1):
            def logS(img):
                F=numpy.r_[features.hullfeatures.hullfeatures(img),features.hullfeatures.hullsizefeatures(img)]
                return -.5*sqrt( dot(dot(F-mu,iSigma),F-mu) )
            S0=logS(self.W==c0)
            S1=logS(self.W==c1)
            Sc=logS((self.W==c0)|(self.W==c1))
            logR=log(2)+Sc-S0-S1
            if abs(logR) < 100:
                return exp(logR)
            return exp(sign(logR)*100)
        def RGw(c0,c1):
            b=self.border_id[min(c0,c1),max(c0,c1)]
            return (self.C[self.W==c0].mean()+self.C[self.W==c1].mean())/2./self.C[self.B==b].mean()
        return RSw(c0,c1)*RGw(c0,c1)

    def greedy(self,beta=1.2):
        border_regions=dict((y,x) for x,y in self.border_id.iteritems())
        while True:
            values=dict((b,self._Rw(c0,c1)) for (c0,c1),b in self.border_id.iteritems())
            val,best=max((y,x) for x,y in values.items())
            if val < beta: break
            self._merge(*border_regions[best])
            border_regions=dict((y,x) for x,y in self.border_id.iteritems())
        return self.W


def greedy_roysam_merge(dna):
    M=Merger(dna)
    M.greedy()
    return M.W
