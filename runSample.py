from ete2 import Tree
import getAdjacencies
import globalAdjacencyGraph
import SR
import scaffolding
import argparse
import time

from calculate_SCJ import calculate_SCJ
import multiprocessing

#run method, does one sampling
def runSample(params):
        #retrieving the given parameter
        ccs=params[0]
        tree=params[1]
        extantAdjacencies=params[2]
        adjacencyProbs=params[3]
        alpha=params[4]
        i=params[5]
        extantAdjacencies_species_adj=params[6]
        outputDirectory=params[7]
        reconstructedMarkerCount=params[8]
        allSampleReconstructionStatistic={}
        dict_SCJ={}
        #lock = multiprocessing.Lock()
        #output text log
        outLog="Sample: "+str(i)+"\n"

        #start sampling method like in the Main.py
        outLog+="Enumerate joint labelings...\n"
        jointLabels, first = SR.enumJointLabelings(ccs)
        outLog+="Check valid labels...\n"
        validLabels, validAtNode = SR.validLabels(jointLabels, first)

        #lock.acquire()
        outLog+= "Compute ancestral labels with SR...\n"
        topDown = SR.sampleLabelings(tree, ccs, validAtNode, extantAdjacencies, adjacencyProbs, alpha)
        #lock.release()
        reconstructedAdj = SR.reconstructedAdjacencies(topDown)
        SR.outputReconstructedAdjacencies(reconstructedAdj, outputDirectory+"/reconstructed_adjacencies_" + str(i))

        for node in reconstructedAdj:
            # count for each adjaency on each internal node, how often this adjacencies over all samples occurs there
            for adjacency in reconstructedAdj[node]:
                #lock.acquire()
                if (node,adjacency) in allSampleReconstructionStatistic:
                    allSampleReconstructionStatistic[(node,adjacency)] += 1
                else:
                    allSampleReconstructionStatistic.update({(node,adjacency):1})
                #lock.release()
        outLog+="Scaffolding...\n"
        scaffolds = scaffolding.scaffoldAdjacencies(reconstructedAdj)
        undoubled = scaffolding.undoubleScaffolds(scaffolds)
        scaffolding.outputUndoubledScaffolds(undoubled, outputDirectory+"/undoubled_scaffolds_" + str(i))
        scaffolding.outputScaffolds(scaffolds, outputDirectory+"/doubled_scaffolds_" + str(i))
        log=scaffolding.sanityCheckScaffolding(undoubled)
        outLog+=log
        for node in undoubled:
            outLog+= str(node)+'\n'
            markerCounter = 0
            for scaffold in undoubled[node]:
                first = scaffold[0]
                last = scaffold[-1]
                if not first == last:
                    markerCounter = markerCounter + len(scaffold)
                else:
                    markerCounter = markerCounter + len(scaffold) - 1
            outLog+= str(node) + " number of reconstructed undoubled marker in scaffolds: " + str(markerCounter)+'\n'
            # number of reconstructed markerIds given by reconstructedMarkerCount
            # singleton scaffolds number / number of not reconstructed marker
            notReconstructedMarkerCount = reconstructedMarkerCount - markerCounter
            # number of all scaffolds
            allScaffoldCount = len(undoubled[node]) + notReconstructedMarkerCount
            outLog+= str(node) + " number of singleton scaffolds (not reconstructed marker): " + str(
                notReconstructedMarkerCount)+'\n'
            outLog+= str(node) + " number of scaffolds: " + str(allScaffoldCount)+'\n'


        #lock.acquire()
        scj = calculate_SCJ(tree, reconstructedAdj, extantAdjacencies_species_adj)
        outLog+="Single-Cut-or-Join-Distance: " + str(scj)+'\n'
        dict_SCJ.update({'Sample_' + str(i): scj})
        #lock.release()
        return (allSampleReconstructionStatistic,dict_SCJ,outLog)

