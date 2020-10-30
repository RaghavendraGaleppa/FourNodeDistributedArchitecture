#!/bin/bash

# Try to kill previously running background processes
killall -9 redis-server
killall -9 python3


redis-server > /dev/null &
sleep 1
uvicorn server:app --reload --log-level error > /dev/null &
sleep 1
python3 simulate.py
