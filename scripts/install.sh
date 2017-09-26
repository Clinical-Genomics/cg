source activate stage3

conda install numpy

pip install --upgrade --no-deps git+https://github.com/Clinical-Genomics/trailblazer@trailblazer2
pip install --upgrade --no-deps git+https://github.com/Clinical-Genomics/housekeeper@housekeeper2
pip install --upgrade --no-deps git+https://github.com/Clinical-Genomics/genotype@no-housekeeper

pip install --upgrade --no-deps git+https://github.com/Clinical-Genomics/cg@cg2

# API server

conda install gunicorn

# Setup databases

chanjo-stage db setup --reset
chanjo-stage link /mnt/hds/proj/cust000/STAGE/resources/scout.exons.bed
hk-stage init --reset --force
tb-stage init --reset --force
tb-stage user --name "Robin Andeer" robin.andeer@scilifelab.se
gt-stage init --reset resources/genotype.snps.grch37.txt
cg-stage init --reset --force
