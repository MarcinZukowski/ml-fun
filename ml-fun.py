#!/usr/bin/env python2.7

import array
import optparse
import os
import re
import struct

import tester_pg

# Load libraries
from math import floor, ceil
from random import randint

import pandas
from pandas.tools.plotting import scatter_matrix
# import matplotlib.pyplot as plt
from sklearn import model_selection
from sklearn.metrics import classification_report
from sklearn.metrics import confusion_matrix
from sklearn.metrics import accuracy_score
from sklearn.linear_model import LogisticRegression, BayesianRidge, RANSACRegressor, Ridge
from sklearn.tree import DecisionTreeClassifier
from sklearn.neighbors import KNeighborsClassifier
from sklearn.discriminant_analysis import LinearDiscriminantAnalysis
from sklearn.naive_bayes import GaussianNB
from sklearn.svm import SVC, LinearSVR
from sklearn.decomposition import KernelPCA

parser = optparse.OptionParser()

(options, args) = parser.parse_args()

assert len(args) == 4, len(args)

XS = int(args[0])
YS = int(args[1])
fname = args[2]
prefix = args[3]

# Read the data
with open(fname) as f:
    data = f.read()
assert len(data) == (XS * YS), "data:{0} X={1} Y={2}".format(len(data), XS, YS)
bytes = array.array('B')
bytes.fromstring(data)


csv = None

def generateMainCSV():
    global prefix, csv
    # Generate
    csv = prefix + ".csv"
    print "Creating " + csv
    with open(csv, "w") as f:
        for y in range(0, YS):
            for x in range(0, XS):
                idx = y * XS + x
                val = bytes[idx]
                f.write("{0},{1},{2}\n".format(x, y, val))

# http://machinelearningmastery.com/machine-learning-in-python-step-by-step/

generateMainCSV()

names = ['x', 'y', 'count']
dataset = pandas.read_csv(csv, names=names)
# Split-out validation dataset
arr = dataset.values
X = arr[:,0:2]
Y = arr[:,2]

def runML(nm, training_fraction):
    global XS, YS, X, Y, prefix

    validation_size = 1.0 - training_fraction
    seed = 7
    X_train, X_validation, Y_train, Y_validation = model_selection.train_test_split(
        X, Y, test_size=validation_size, random_state=seed)

    classifier = None
    classifier = eval(nm)
    classifier.fit(X_train, Y_train)

    X_validation = X
    predictions = classifier.predict(X_validation)

    res = [0] * (XS * YS)
    for i in range(0, len(predictions)):
        idx = X_validation[i][1] * XS + X_validation[i][0]
        res[idx] = int(predictions[i])

    outb = array.array('B')
    for i in range(0, XS * YS):
        outb.append(res[i])

    suff = re.sub("[\'\(\)\-\,= ]", "_", nm)

    suff = "{0}_tf_{1}".format(suff, training_fraction)
    print
    print suff

    gray = "{0}_{1}.out.gray".format(prefix, suff)
    png = "{0}_{1}.out.png".format(prefix, suff)

    print "Creating {0}".format(gray)
    with open(gray, "wb") as f:
        outb.tofile(f)

    cmd = "convert -size {XS}x{YS} -depth 8 GRAY:{gray} {png}".format(XS=XS, YS=YS, gray=gray, png=png)
    print "Running: {0}".format(cmd)
    os.system(cmd)

def runML1(nm):
    runML(nm, 0.01)
    runML(nm, 0.03)
    runML(nm, 0.1)
    runML(nm, 0.3)
#    runML(nm, 1.0)

def runMLAll():
    """
    runML1("LogisticRegression()")
    runML1("LogisticRegression(C=0.1)")
    runML1("LogisticRegression(C=10)")
    """
    runML1("KNeighborsClassifier(1)")
    runML1("KNeighborsClassifier(10)")
    runML1("GaussianNB()")
    runML1("DecisionTreeClassifier()")
    runML1("SVC()")
    runML1("SVC(10)")
    runML1("LinearSVR()")
    runML1("SVC(decision_function_shape='ovo')")
    runML1("BayesianRidge()")

# We produce an array of sums indices of size of roughly outsize, with each index in
# sums receiving a number proportional to its value in sums (and at least 1)
def normalize(sums, outsize, fname):
    total = sum(sums)
    per_bucket = floor(total / outsize)

    out = []
    starts = []
    counts = []
    for i in range(0, len(sums)):
        count = int(ceil(sums[i] / per_bucket))
        starts.append(len(out))
        counts.append(count)
        for j in range(0, count):
            out.append(i)

    print "Creating {0}".format(fname)
    with open(fname, "w") as f:
        for i in range(0, len(out)):
            f.write("{0},{1}\n".format(i, out[i]))

    return out, starts, counts

def prepareData():
    global bytes, XS, YS

    xsums = [0] * XS
    ysums = [0] * YS

    for y in range(0, YS):
        for x in range(0, XS):
            idx = y * XS + x
            xsums[x] += bytes[idx]
            ysums[y] += bytes[idx]

    xdata, xstarts, xcounts = normalize(xsums, XS * 10, "{0}-x-data.csv".format(prefix))
    ydata, ystarts, ycounts = normalize(ysums, YS * 10, "{0}-y-data.csv".format(prefix))

    factdata = "{0}-fact-data.csv".format(prefix)

    print("Creating {0}".format(factdata))

    with open(factdata, "w") as f:
        id = 0
        for y in range(0, YS):
            for x in range(0, XS):
                idx = y * XS + x
                count = bytes[idx]
                id = 0
                for i in range(0, count):
                    xid = xstarts[x] + randint(0, xcounts[x] - 1)
                    yid = ystarts[y] + randint(0, ycounts[y] - 1)
                    f.write("{id},{xid},{yid},{x},{y}\n".format(id=id,xid=xid,yid=yid,x=x,y=y))
                    id += 1

# This tests various "ML" algorithms
runMLAll()

# This generates data that can be loaded into a database, and runs it on pgsql
prepareData()
tester_pg.ddl()
tester_pg.load(prefix)
tester_pg.analyze()
tester_pg.test(prefix, XS, YS)
