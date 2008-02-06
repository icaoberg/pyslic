from numpy import array
from PyML import *

__ALL__=['PyMLSVM']
class PyMLSVM(object):
    def __init__(self):
        pass

    def train(self,feats,labels):
        allabels=dict([(L,None) for L in labels])
        if len(allabels) > 2:
            self.s = multi.OneAgainstRest(svm.SVM())
        else:
            self.s = svm.SVM()
        data=datafunc.VectorDataSet(feats,L=labels)
        self.s.train(data)
        self.trained=True

    def apply(self,feats):
        assert self.trained
        data=datafunc.VectorDataSet(feats)
        return array(self.s.test(data))

# vim: set ts=4 sts=4 sw=4 expandtab smartindent:
