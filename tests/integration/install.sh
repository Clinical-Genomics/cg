source activate stage3

conda install numpy

pip install --upgrade --no-deps git+https://github.com/Clinical-Genomics/trailblazer@trailblazer2
pip install --upgrade --no-deps git+https://github.com/Clinical-Genomics/housekeeper@housekeeper2
pip install --upgrade --no-deps git+https://github.com/Clinical-Genomics/genotype@no-housekeeper

pip install --upgrade --no-deps git+https://github.com/Clinical-Genomics/cg@cg2

# API server
conda install gunicorn
