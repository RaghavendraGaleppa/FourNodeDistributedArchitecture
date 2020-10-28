#!/bin/bash

redis-server  > /dev/null
sleep 1
uvicorn server:app --reload --log-level critical > /dev/null
sleep 1
python3 simulate.py

