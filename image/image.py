from scipy.misc.pilutil import *
from numpy import *

__all__ = ['Image']

class Image(object):
    """
    class Image(object)

    Represents a multi-channel image.
    """
    dna_channel='dna'
    protein_channel='protein'
    autofluorescence_channel='autofluorescence'
    crop_channel='crop'

    procdna_channel='procdna'
    procprotein_channel='procprotein'

    __slots__ = ['label','features','regions','channels','channeldata']
    def __init__(self):
        self.label=''
        self.features=None
        self.regions=None
        self.channels={}
        self.channeldata={}

    def load(self):
        for k,v in self.channels.items():
            if k != self.crop_channel: # Crop is handled like a region
                self.channeldata[k]=imread(v)
        if self.crop_channel in self.channels:
            self.regions = imread(self.channels[self.crop_channel])

    def unload(self):
        self.channeldata={}

    def show(self):
        self.load()
        X,Y=self.channeldata[self.protein_channel].shape
        composite=zeros((X,Y,3))
        composite[:,:,1]=self.channeldata[self.protein_channel]
        if self.dna_channel in self.channeldata:
            composite[:,:,0]=self.channeldata[self.dna_channel]
        imshow(composite)

# vim: set ts=4 sts=4 sw=4 expandtab smartindent:
