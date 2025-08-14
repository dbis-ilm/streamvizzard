FROM flink:1.20

# install python3 and pip3

RUN apt-get update -y && \
apt-get install -y python3 python3-pip python3-dev && rm -rf /var/lib/apt/lists/*
RUN ln -s /usr/bin/python3 /usr/bin/python

# download required python libraries

RUN wget -nc https://files.pythonhosted.org/packages/1f/31/80cfa34b6a53a5c19d66faf3e7d29cb0689a69c128a381e584863eb9669a/apache-flink-libraries-1.20.0.tar.gz && \
    wget -nc https://files.pythonhosted.org/packages/37/85/830c518b8a80095c371d3af5143c90d51a21958f1d0c4095ce799445bcfe/apache-flink-1.20.0.tar.gz && \
    pip3 install apache-flink-libraries-1.20.0.tar.gz && \
    pip3 install apache-flink-1.20.0.tar.gz

# install custom python libraries for the examples

RUN pip3 install tensorflow==2.15.0
RUN pip3 install pillow
