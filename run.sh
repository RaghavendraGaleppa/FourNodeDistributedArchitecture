#!/bin/bash

redis-server  &
sleep 1
uvicorn server:app --reload & 
sleep 1
python3 simulate.py

