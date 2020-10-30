#!/bin/bash

# Try to kill previously running background processes
killall -9 redis-server
killall -9 uvicorn


redis-server  
sleep 1
uvicorn server:app --reload --log-level critical 
sleep 1
python3 simulate.py
