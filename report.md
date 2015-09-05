# Report

In this markdown file I report how the test was answered. This format was chosen for being human readable (and renderable to html). This report and the codes written can be found in the Github repository [cassy_n_ribs](https://github.com/embatbr/cassy_n_ribs) (the name is to keep a low profile).


## Learning

I used many sources (docs, books and tutorials - Kiyu Gabriel's was specially useful) to understand how Cassandra works *under the hood* (needed before running any tests). Also, I had to learn how to used the [Python driver for Cassandra](https://github.com/datastax/python-driver) to connect with the database and [JMXTerm](http://wiki.cyclopsgroup.org/jmxterm/) to record the metrics during the stress test.


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

In my machine I created a Python virtual environment using `virtualenv` and `virtualenvwrapper` (the environment hidden folder is created in the `HOME` directory). Its name is `ds_hire` and it is activated typing `workon ds_hire` on the terminal.

The directories *data* and *logs* are created in Cassandra's own directory (inside the directory *project*). There is a recommendation to create them in */var/lib/cassandra*, but this would require sudo privilegies and is an unnecessary overhead to add here (also the current mode is easier to check using Sublime Text).

The stress test creates a keyspace named **keyspace1**, with scopes **counter1**, **Counter3** and **standard1**.


### Test: Single Node Cluster

#### Tasks

The list of tasks defined in the document *JMXTextScreen.pdf*.

1. OK
2. OK. The metric "AllMemTablesDataSize" was (probably) renamed to "AllMemtablesLiveDataSize" in the newer versions.
3. OK. No extras. n = 1000000, #threads = 10 (changeable)
4. OK
5. OK. Recorded in the file *jmx.log* along with many other infos, if existent.
6. TODO
7 (graphs). OK. Plotting each metric for each scope in a single file. Extra: automatized by the script


#### Explanation

- The single node cluster "EduardoTestCluster" is initialized manually.
- Using the command **nodetool** with option **status**, for 127.0.0.1:7199, the script ensures Cassandra is running and returns its PID and version
- The metrics **LiveSSTableCount**, **AllMemtablesLiveDataSize** (the name, in 2.1+ versions, for AllMemTablesDataSize) and **Latency** (with attribute 95thPercentile) begin to be recorded using JMXTerm to communicate with JMX.
- The stress test is runned using **cassandra-stress** with the command **write**, no-warmup, 1 million operations and 10 threads.
- After the stress test is completed, the recording of JMX metrics stops (the script waits some seconds after the test finishes).
- Perform some assertations of the metrics: if there's values 0, a few times or always (occurs in some *scopes*) and if they go negative (never).
- TODO cassandra tables
- The results are **automatically** saved in PNG files.

For scopes **counter1** and **Counter3**, there's no writing in the table (their value are zero). For scope **standard1**, the values of **AllMemtablesLiveDataSize** vary with the number of operations per second. With more operations, the latency increases and the 95thPercentile measure decreases (many operations takes too much time). The number of live SSTables increases when the number of operations per second becames very high (see that its values always increase - an opposite behavior to the Latency 95thPercentile).