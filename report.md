# Report

In this markdown file I report how the test screen was answered. Since the file format is intended to be rendered, it is advised to read it in a platform with support (e.g., Github). This report and the codes written can be found in the Github repository [cassy_n_ribs](https://github.com/embatbr/cassy_n_ribs).


## Learning

I used many sources (documentation, books and tutorials) to understand how Cassandra works *under the hood* (needed before running any tests). Also, I had to learn how to used the [Python driver for Cassandra](https://github.com/datastax/python-driver) and [Jmxterm](http://wiki.cyclopsgroup.org/jmxterm/).


## Tools Used

- Apache Cassandra 2.1.8, saved in the same directory of this file.
- A driver for Cassandra written in Python (for version 3.4).
- Jmxterm, a command line interface for querying jmx metrics.


## Tests

Three types of tests are described step by step. The first (and simpler) is performed on a single node cluster (no partitioning). Later, a single data center with multiple clusters is tested. The last test is with multiples data centers.

In my machine I created a Python virtual environment using `virtualenv` and `virtualenvwrapper` (the folder is created in the `HOME` directory).


### Single Node Cluster


### Multiple Node Cluster - Single Data Center


### Multiple Node Cluster - Multiples Data Centers