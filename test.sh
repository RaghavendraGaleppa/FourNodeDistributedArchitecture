#!/bin/bash
killall -9 redis-server
killall -9 uvicorn
killall -9 python3

sudo apt-get update
sudo apt-get install uvicorn
wget http://download.redis.io/redis-stable.tar.gz
tar xvzf redis-stable.tar.gz
cd redis-stable
sudo make > /dev/null
sudo make install > /dev/null
