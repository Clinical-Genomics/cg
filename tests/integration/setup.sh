# API server
export CG_SQL_DATABASE_URI
export CG_ENABLE_ADMIN=1
gunicorn -w 2 -b 0.0.0.0:7070 --access-logfile - --error-logfile - --keyfile /tmp/myserver.key --certfile /tmp/server.crt --timeout 60 cg.server.auto:app > ~/STAGE/logs/cg.server.log

cg init --reset
python ./scripts/transfer.py [config]

# add FASTQ files to Housekeeper for the downsampled HapMap samples
for sampleId in ADM1059A1 ADM1059A2 ADM1059A3; do
    hk-stage add bundle ${sampleId}
    for fastqFile in /mnt/hds/proj/cust000/validations/HapMap-WGS/${sampleId}/testset/*.fastq.gz; do
        hk-stage add file ${sampleId} ${fastqFile} --tag fastq
    done
done
