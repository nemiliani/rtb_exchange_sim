#!/bin/bash
ncat -v -l 9876 -k -d 20 -m 1000 --exec '/bin/cat'
