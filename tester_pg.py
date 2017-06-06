#!/usr/bin/env python2.7

import os
import psycopg2
import re
import struct

try:
    conn = psycopg2.connect("dbname='postgres' user='postgres' host='localhost'")
except:
    print "I am unable to connect to the database"

cur = conn.cursor()

def run(s, verbose=True):
    global conn
    if verbose:
        print("Running: {0}".format(s))
    cur = conn.cursor()
    cur.execute(s)
    return cur


def ddl():
    run("""drop table if exists dimx""")
    run("""drop table if exists dimy""")
    run("""drop table if exists fact""")
    run("""create table dimX(xid integer, x integer)""")
    run("""create table dimY(yid integer, y integer)""")
    run("""create table fact(id integer, xid integer, yid integer, x integer, y integer)""")
    run("""commit""")

def loadtable(nm, file):
    pwd = os.getcwd()
    run("""copy {0} from '{1}/{2}' with delimiter ','""".format(nm, pwd, file))

def load(prefix):
    loadtable("dimx", prefix + "-x-data.csv")
    loadtable("dimy", prefix + "-y-data.csv")
    loadtable("fact", prefix + "-fact-data.csv")

def analyze():
    run("analyze dimx")
    run("analyze dimy")
    run("analyze fact")

#ddl()
#load("surajit2.png")
#analyze()

def subtest(gray, png, XS, YS, query):

    print "Creating " + gray
    with open(gray, "wb") as f:

        for y in range(0, YS):
            for x in range(0, XS):
                q = query.format(x, y)
                cur = run(q, verbose=False)
                rows = cur.fetchall()
                card = None
                l = rows[1][0]
                m = re.match('.*rows=(\d+) .*', l)
                assert m
                card = int(m.group(1))
                assert card is not None
                card = min(255, max(0, card))
                # print "{0},{1},{2}".format(x, y, card)
                f.write(struct.pack('B', card))

    cmd = "convert -size {XS}x{YS} -depth 8 GRAY:{gray} {png}".format(XS=XS, YS=YS, gray=gray, png=png)
    print "Running: {0}".format(cmd)
    os.system(cmd)

def test(prefix="surajit2.png", XS=100, YS=150):

    q1 = """
    EXPLAIN SELECT COUNT(*) 
    FROM 
      fact 
      join dimx on fact.xid = dimx.xid
      join dimy on fact.yid = dimy.yid
      where dimx.x = {0} and dimy.y={1}
    """

    gray = prefix + "-pg-join.gray"
    png = prefix + "-pg-join.png"
    subtest(gray, png, XS, YS, q1)

    q2 = """
    EXPLAIN SELECT COUNT(*) 
    FROM 
      fact 
      where x = {0} and y = {1}
    """

    gray = prefix + "-pg-table.gray"
    png = prefix + "-pg-table.png"
    subtest(gray, png, XS, YS, q1)


    subtest(gray, png, XS, YS, q2)
