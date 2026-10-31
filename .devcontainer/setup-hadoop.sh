#!/bin/bash

echo "=== Downloading and Extracting Hadoop 3.3.6 ==="
wget -q https://dlcdn.apache.org/hadoop/common/hadoop-3.3.6/hadoop-3.3.6.tar.gz
sudo tar -xzvf hadoop-3.3.6.tar.gz -C /usr/local/
sudo mv /usr/local/hadoop-3.3.6 /usr/local/hadoop
sudo chown -R vscode:vscode /usr/local/hadoop

echo "=== Setting Environment Variables ==="
JAVA_PATH=$(dirname $(dirname $(readlink -f $(which java))))
echo "export JAVA_HOME=$JAVA_PATH" >> ~/.bashrc
echo "export HADOOP_HOME=/usr/local/hadoop" >> ~/.bashrc
echo 'export PATH=$PATH:$HADOOP_HOME/bin:$HADOOP_HOME/sbin' >> ~/.bashrc

export JAVA_HOME=$JAVA_PATH
export HADOOP_HOME=/usr/local/hadoop
export PATH=$PATH:$HADOOP_HOME/bin:$HADOOP_HOME/sbin

echo "export JAVA_HOME=$JAVA_HOME" >> $HADOOP_HOME/etc/hadoop/hadoop-env.sh
echo "localhost" > $HADOOP_HOME/etc/hadoop/workers

echo "=== Updating Hadoop Configuration Files ==="
# core-site.xml
cat << 'EOF' > $HADOOP_HOME/etc/hadoop/core-site.xml
<configuration>
    <property>
        <name>fs.defaultFS</name>
        <value>hdfs://localhost:9000</value>
    </property>
</configuration>
EOF

# hdfs-site.xml
cat << 'EOF' > $HADOOP_HOME/etc/hadoop/hdfs-site.xml
<configuration>
    <property>
        <name>dfs.replication</name>
        <value>1</value>
    </property>
    <property>
        <name>dfs.namenode.name.dir</name>
        <value>/usr/local/hadoop/data/namenode</value>
    </property>
    <property>
        <name>dfs.datanode.data.dir</name>
        <value>/usr/local/hadoop/data/datanode</value>
    </property>
</configuration>
EOF

echo "=== Formatting HDFS NameNode ==="
mkdir -p /usr/local/hadoop/data/namenode /usr/local/hadoop/data/datanode
$HADOOP_HOME/bin/hdfs namenode -format -force

echo "=== Installing Python Libraries ==="
pip install --no-cache-dir pyspark pandas duckdb scikit-learn matplotlib seaborn

echo "=== Setup Complete! ==="
