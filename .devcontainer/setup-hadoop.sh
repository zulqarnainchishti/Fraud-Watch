#!/bin/bash

echo "=== Updating system & installing dependencies ==="
sudo apt-get update && sudo apt-get install -y openssh-server openssh-client rsync wget

echo "=== Configuring passwordless SSH ==="
ssh-keygen -t rsa -P '' -f ~/.ssh/id_rsa
cat ~/.ssh/id_rsa.pub >> ~/.ssh/authorized_keys
chmod 0600 ~/.ssh/authorized_keys

echo "=== Downloading and Extracting Hadoop 3.3.6 ==="
wget -q https://dlcdn.apache.org/hadoop/common/hadoop-3.3.6/hadoop-3.3.6.tar.gz
sudo tar -xzvf hadoop-3.3.6.tar.gz -C /usr/local/
sudo mv /usr/local/hadoop-3.3.6 /usr/local/hadoop
sudo chown -R vscode:vscode /usr/local/hadoop

echo "=== Setting Environment Variables ==="
echo 'export JAVA_HOME=/usr/lib/jvm/default-java' >> ~/.bashrc
echo 'export HADOOP_HOME=/usr/local/hadoop' >> ~/.bashrc
echo 'export PATH=$PATH:$HADOOP_HOME/bin:$HADOOP_HOME/sbin' >> ~/.bashrc
export JAVA_HOME=/usr/lib/jvm/default-java
export HADOOP_HOME=/usr/local/hadoop
export PATH=$PATH:$HADOOP_HOME/bin:$HADOOP_HOME/sbin

echo "=== Updating Hadoop Configuration Files ==="
echo "export JAVA_HOME=$JAVA_HOME" >> $HADOOP_HOME/etc/hadoop/hadoop-env.sh

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
hdfs namenode -format -force

echo "=== Setup Complete! ==="
