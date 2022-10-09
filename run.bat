set TSA_URL=http://e-imzo.uz/cams/tst
set TRUSTSTORE_FILE=keys/truststore.jks
set TRUSTSTORE_PASSWORD=12345678

java -Dfile.encoding=UTF-8 -jar dsv-server.jar -p 9090
