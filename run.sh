#!/bin/bash

# Try to kill previously running background processes
killall -9 redis-server
killall -9 uvicorn
killall -9 python3


echo "Running redis-server"
redis-server > /dev/null &

echo "Running uvicorn"
sleep 1
uvicorn server:app --reload --log-level error &

echo "Running simulate.py"
sleep 1
python3 simulate.py
