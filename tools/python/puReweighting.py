''' PU reweighting function
'''
#Standard imports
import ROOT

# helpers
from StopsDilepton.tools.helpers import getObjFromFile

# Logging
import logging
logger = logging.getLogger(__name__)

def extendHistoTo(h, hc):
    "Extend histo h to nbins of hc"
    res = ROOT.TH1D(h.GetName()+"_extended",h.GetTitle(), hc.GetNbinsX(),hc.GetXaxis().GetXmin(),hc.GetXaxis().GetXmax())
    assert  hc.GetXaxis().GetXmin()==h.GetXaxis().GetXmin() \
            and hc.GetNbinsX()==hc.GetXaxis().GetXmax()-hc.GetXaxis().GetXmin() \
            and h.GetNbinsX()==h.GetXaxis().GetXmax()-h.GetXaxis().GetXmin(), \
            "Error extending histogram! Check axis ranges!"
    res.Reset()
    for i in range(min(hc.GetNbinsX(), h.GetNbinsX())):
        res.SetBinContent(i, h.GetBinContent(i))
    return res

#Define a functor that returns a reweighting-function according to the era
def getReweightingFunction(data="PU_2100_XSecCentral", mc="Spring15"):

    # Data
    fileNameData = "$CMSSW_BASE/src/StopsDilepton/tools/data/puReweightingData/%s.root" % data

    histoData = getObjFromFile(fileNameData, 'pileup')
    histoData.Scale(1./histoData.Integral())
    logger.info("Loaded 'pileup' from data file %s", fileNameData )

    if type(mc)==type(""):
        if mc=='Summer16':
            mcProfile = extendHistoTo(getObjFromFile("$CMSSW_BASE/src/StopsDilepton/tools/data/puReweightingData/MCProfile_Summer16.root", 'pileup'), histoData)
        else:
            raise ValueError( "Don't know about MC PU profile %s" %mc )
    else:
        mcProfile = extendHistoTo(mc, histoData)

    mcProfile.Scale(1./mcProfile.Integral())

    # Create reweighting histo
    reweightingHisto = histoData.Clone( '_'.join(['reweightingHisto', data]) )
    reweightingHisto.Divide(mcProfile)

    # Define reweightingFunc
    def reweightingFunc(nvtx):
        return reweightingHisto.GetBinContent(reweightingHisto.FindBin(nvtx))

    return reweightingFunc

def getNVTXReweightingFunction(key, filename = "dilepton_allZ_isOS_4000pb4000_80X.pkl"):

    if not key in ['rw', 'up', 'down', 'vup', 'vdown']:
        raise ValueError( "Need to specify value PU reweighting key" )

    # 2016 PU reweighting with sigma(QCD) uncertainty
    import pickle, os
    data = pickle.load( file(os.path.expandvars("$CMSSW_BASE/src/StopsDilepton/tools/data/puReweightingData/%s" % filename)) )
    h = data[key]
    def reweightingFunc( nvtx ):
        ib = h.FindBin( nvtx )
        return h.GetBinContent( ib )

    return reweightingFunc
