# Report

In this markdown file I report how the test was answered. This format was chosen for being human readable. This report and the codes written can be found in the Github repository [cassy_n_ribs](https://github.com/embatbr/cassy_n_ribs) (the name is to keep a low profile).


## Learning

I used many sources (documentation, books and tutorials - Kiyu Gabriel's was specially useful) to understand how Cassandra works *under the hood* (needed before running any tests). Also, I had to learn how to used the [Python driver for Cassandra](https://github.com/datastax/python-driver) and [Jmxterm](http://wiki.cyclopsgroup.org/jmxterm/).


## Tools Used

- Java 7.
- Apache Cassandra 2.1.9, saved in the directory *project* (and gitignored).
- [Jmxterm](http://wiki.cyclopsgroup.org/jmxterm/download.html), a command line interface for querying jmx metrics. Saved in the directory *project/lib*.
- A driver for Cassandra written in Python (for version 3.4), provided by DataStax.


## Understanding of the Architecture

**Massively linearly scalable NoSQL database**

Cassandra is a NoSQL database in the AP side of the CAP theorem. It is composed of a (unique) **cluster** of nodes, that may be grouped in multiple **data centers** (a logical division, since multiple Cassandra DCs may be physically located in the same data center). Inside each DC, the nodes are grouped in **racks**, that are, in plain English, failure zones (usually physical connections between nodes - e.g., power, network and etc.). Racks are single points of failure that are isolated (the disposal must be one that prevents a failure of a node and its replicas).

The idea of multiple nodes is very useful when the cluster is geographically distributed. This reduces the overhead from request a data from the other side of the planet and delivers a system with no point of failure. To correctly storage the data, a partition key is extracted from the primary key of the CQL table. Also, each node may be replicated (with no hierarchy of copies) the rows, increasing the fault tolerance.

A cluster has a **token range**, used to partition the dataset. When not using virtual nodes, each node has a piece of the token range.

Cassandra = Google BigTable + Amazon Dynamo, roughly speaking.

Cassandra architecture has many similarities with Bitcoin's blockchain.


## Implementation and Tests

In my machine I created a Python virtual environment using `virtualenv` and `virtualenvwrapper` (the environment folder is created in the `HOME` directory). Its name is `ds_hire` and is activated typing

```
$ workon ds_hire
```

on the terminal.

The directories *data* and *logs* are created in Cassandra's own directory. There is a recommendation to create them in */var/lib/cassandra*, but this would require sudo privilegies and is an unnecessary overhead to add here (also the current mode is easier to check in the Sublime Text).


### Test: Single Node Cluster


#### Tasks

The list of tasks defined in the document *JMXTextScreen.pdf*.

1. OK
2.
3.
4.
5.
6.