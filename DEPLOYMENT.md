## Deploying a new release to production
Before deploying, ensure that all GitHub actions related to the merge have finished, eg. bump version, create release, publish to Dockerhub and PyPi.

### Deploy CLI
1. ssh to the login-node
2. Install the master branch
```shell
    bash /home/proj/production/servers/resources/hasta.scilifelab.se/update-tool-prod.sh -e P_cg -t cg -b master -a
```
### Deploy APP
1. Use the action **[Deploy release to production environment](https://github.com/Clinical-Genomics/cg/actions/workflows/deploy_prod.yml)** to deploy your branch. Make sure to provide the **release-tag** and NOT master to the action.
2. Check [the production deployment page](https://github.com/Clinical-Genomics/cg/deployments/production) to ensure the deployment was successful.


## Deploying a branch to stage
Before deploying, ensure that all GitHub actions related to the last push have finished.
### Deploy CLI
1. ssh to the login-node
2. Install your branch
```shell
    bash /home/proj/production/servers/resources/hasta.scilifelab.se/update-tool-stage.sh -e S_cg -t cg -b [YOUR-BRANCH-NAME] -a
```
### Deploy APP
1. Use the action **[Deploy branch to staging environment](https://github.com/Clinical-Genomics/cg/actions/workflows/deploy_stage.yml)** to deploy your branch.
2. Check [the stage deployment page](https://github.com/Clinical-Genomics/cg/deployments/stage) to ensure the deployment was successful.