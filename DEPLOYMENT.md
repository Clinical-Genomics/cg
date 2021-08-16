# Steps

When all tests done and successful and PR is approved by codeowners, follow these steps:

1. Select "Squash and merge" to merge branch into default branch (master/main)


2. A prompt for writing merge commit message will pop up


3. Find the title of the pull request already pre-filled in the merge commit title, or copy and paste 
the title if not.


4. Append version increment value `( major | minor | patch )` to specify what kind of release is to be created.


5. Fill in mkdown formatted changelog in merge commit comment details:

` ### Added `

` ### Changed `

` ### Fixed `

6. Review the details once again and merge the branch into master.


7. Wait for GitHub actions to process the event, bump version, create release, publish to Dockerhub and PyPi


8. Deploy master to stage:

    1. `us`
    2. Request stage environment `paxa` and follow instructions
    3. `bash update-cg-stage.sh master`
    4. make sure that installation was successful
   

10. Deploy master to production
     1. `up`
     2. `bash update-cg-prod.sh`
     3. make sure that installation was successful


11. Take a screenshot or copy log text and post as a comment on the PR. Screenshot should include environment and that it succeeded

