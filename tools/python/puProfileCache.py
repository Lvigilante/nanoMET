''' Class to construct & cache MC PU profiles (necessary for 2017 MC)
'''

# Standard imports
import ROOT
import os

# RootTools
from RootTools.core.standard import *

# Analysis
from nanoMET.tools.ResultsDB import ResultsDB
from nanoMET.tools.user      import dbDir

loggerChoices = ['CRITICAL', 'ERROR', 'WARNING', 'INFO', 'DEBUG', 'TRACE', 'NOTSET']

if __name__ == "__main__":
    # Arguments
    import argparse
    argParser = argparse.ArgumentParser( description="Argument parser" )
    argParser.add_argument( '--logLevel',  action='store',      default='INFO',  nargs='?', choices=loggerChoices, help="Log level for logging" )
    argParser.add_argument( '--makePlots', action='store_true',                                                    help="Make PU profile plots?")
    argParser.add_argument( '--overwrite', action='store_true',                                                    help="overwrite Database?")
    args      = argParser.parse_args()

    # Logger
    import nanoMET.tools.logger as logger
    import RootTools.core.logger as logger_rt
    logger    = logger.get_logger(    args.logLevel, logFile = None )
    logger_rt = logger_rt.get_logger( args.logLevel, logFile = None )

else:
    # Logger
    import logging
    logger = logging.getLogger(__name__)


class puProfile:

    def __init__( self, source_sample, cacheDir=os.path.join(dbDir,"puProfiles") ):

        if not os.path.isdir( cacheDir ): os.makedirs( cacheDir )

        self.source_sample = source_sample
        self.initCache( cacheDir )
        self.binning        = [ 100, 0, 100 ]
        self.draw_string    = "Pileup_nTrueInt"

    def initCache(self, cacheDir):
        self.cache = ResultsDB( os.path.join( cacheDir, 'puProfiles_v2.sql' ), "puProfile", [ "selection", "weight", "source" ] )

    def uniqueKey( self, *arg ):
        '''No dressing required'''
        return arg

    def cachedTemplate( self, selection, weight = '(1)', save = True, overwrite = False):
        key = {"selection":selection, "weight":weight, "source":self.source_sample.name}
        if (self.cache and self.cache.contains(key)) and not overwrite:
            result = self.cache.get(key)
            logger.info( "Loaded MC PU profile from %s"%(self.cache.database_file) )
            logger.debug( "Key used: %s result: %r"%(key, result) )
        elif self.cache:
            logger.info( "Obtain PU profile for %s"%( key, ) )
            result = self.makeTemplate( selection = selection, weight = weight)
            if result:
                result = self.cache.addData( key, result, overwrite=save )
                logger.info( "Adding PU profile to cache for %s : %r" %( key, result) )
            else:
                logger.warning( "Couldn't create PU profile to cache for %s : %r" %( key, result) )
        else:
            result = self.makeTemplate( selection = selection, weight = weight)
        return result

    def makeTemplate( self, selection, weight='(1)' ):
        logger.info( "Make PU profile for sample %s and selection %s and weight %s", self.source_sample.name, selection, weight )

        h_source = self.source_sample.get1DHistoFromDraw(self.draw_string, self.binning, selectionString = selection, weightString = weight )
        logger.info( "PU histogram contains %s weighted events", h_source.Integral() )
        h_source.Scale( 1./h_source.Integral() )
        return h_source

if __name__ == "__main__":

    # Get all NanoAOD tuples for caching
    from nanoMET.nanoAOD.Fall17_private_legacy_v1 import *
    from nanoMET.tools.user                       import plot_directory

    if args.overwrite: os.remove( dbDir + "/puProfiles/puProfiles_v2.sql" )
    for sample in allSamples:
        logger.info( "Working on samples %s", sample.name )
        puProfiles = puProfile( source_sample=sample, cacheDir=dbDir + "/puProfiles/" )

        # reweighting selection
        selection = "( 1 )"
        profile = puProfiles.cachedTemplate( selection, weight='genWeight', overwrite=False )

        # plot the MC PU profile
        if args.makePlots:
            profilePlot = Plot.fromHisto( sample.name, texX = "nTrueInt", histos = [[profile]] )
            plotting.draw( profilePlot, plot_directory = os.path.join( plot_directory, 'puProfiles'), logY=True, copyIndexPHP=True, extensions = ["png"] )
