#!/bin/bash

export TSA_URL=http://e-imzo.uz/cams/tst
export TRUSTSTORE_FILE=keys/truststore.jks
export TRUSTSTORE_PASSWORD=12345678

java -Dfile.encoding=UTF-8 -jar dsv-server.jar -p 9090


exit 0
