#!/bin/bash
killall -9 redis-server
killall -9 uvicorn
killall -9 python3

redis-server 
uvicorn server:app --reload
python3 verify_payload.py
