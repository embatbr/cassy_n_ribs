# Report

In this markdown file I report how the test screen was answered. Since the file format is intended to be rendered, it is advised to read it in a platform with support (e.g., Github). This report and the codes written can be found in the Github repository [cassy_n_ribs](https://github.com/embatbr/cassy_n_ribs).


## Learning

I used many sources (documentation, books and tutorials - Kiyu Gabriel's was specially useful) to understand how Cassandra works *under the hood* (needed before running any tests). Also, I had to learn how to used the [Python driver for Cassandra](https://github.com/datastax/python-driver) and [Jmxterm](http://wiki.cyclopsgroup.org/jmxterm/).


## Tools Used

- Apache Cassandra 2.1.8 (released after September 2014), saved in the same directory of this file.
- A driver for Cassandra written in Python (for version 3.4).
- Jmxterm, a command line interface for querying jmx metrics.


## Understanding of the Architecture

**Massively linearly scalable NoSQL database**

Cassandra is a NoSQL database in the AP side of the CAP theorem. It is composed of a (unique) **cluster** of nodes, that may be grouped in multiple **data centers** (a logical division, since multiple Cassandra DCs may be physically located in the same data center). Inside each DC, the nodes are grouped in **racks**, that are, in plain English, failure zones (usually physical connections between nodes - e.g., power, network and etc.). Racks are single points of failure that are isolated (the disposal must be one that prevents a failure of a node and its replicas).

The idea of multiple nodes is very useful when the cluster is geographically distributed. This reduces the overhead from request a data from the other side of the planet and delivers a system with no point of failure. To correctly storage the data, a partition key is extracted from the primary key of the CQL table. Also, each node may be replicated (with no hierarchy of copies) the rows, increasing the fault tolerance.

A cluster has a **token range**, used to partition the dataset. When not using virtual nodes, each node has a piece of the token range.

Cassandra = Google BigTable + Amazon Dynamo, roughly speaking.

Cassandra architecture has many similarities with Bitcoin's blockchain.


## Tests

Three types of tests are described step by step. The first (and simpler) is performed on a single node cluster (no partitioning). Later, a single data center with multiple clusters is tested. The last test is with multiples data centers.

In my machine I created a Python virtual environment using `virtualenv` and `virtualenvwrapper` (the `venv`'s folder is created in the `HOME` directory).

The directories *data* and *logs* are created in Cassandra's directory (*apache-cassandra-2.1.8*). There is a recommendation of create them in */var/lib*, but this would require sudo privilegies and is an unnecessary overhead to add here.


### Test 1: Single Node Cluster


### Test 2: Multiple Node Cluster - Single Data Center


### Test 3: Multiple Node Cluster - Multiples Data Centers