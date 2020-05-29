# Steps

When all tests done and successful and PR is approved, follow these steps:

1. Merge branch to master
1. Bumpversion according to specifications, eg. `bumpversion <patch/minor/major>`
1. Push commit directly to master `git push`
1. Push commit directly to master `git push --tag`
1. Log into relevant serves with `ssh <hasta/clinical-db>`
1. Deploy master to stage
    1.`us`
    1. `bash update-cg-stage.sh master`
    1. make sure that installation was successful
1. Deploy master to stage
    1.`up`
    1. `bash update-cg-prod.sh`
    1. make sure that installation was successful
1. Take a screenshot and post as a comment on the PR. Screenshot should include environment and that it succeeded

