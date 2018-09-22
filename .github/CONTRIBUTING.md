# How to contribute to this code

Welcome!

First off: I'm glad you're reading this. All contributions are greatly appreciated :)

## TL;DR

I have new code I want to add, what do I need to do?

- Create a PR
- Get the PR reviewed and approved ... but don't merge yet
  - Get someone to review your code
  - Is the code the python way?
  - Where is the unit test?
  - Did any signatures of existing functions or methods change?
- Test the PR on stage by deploying your branch
  - Do this with your reviewer
  - Delete current stage
  - Clone prod to stage
  - Install branch into stage with the tool's update script
- If it passes, merge the PR into master
- Delete the branch
- Bumpversion on master
- Add change to change log
- Test the installation of the new master on stage
  - Delete current stage
  - Clone prod to stage
  - Only test if installation succeeds
- If it passes, deploy on prod!
  - Announce on stand up
  - Take backup of prod
  - Install with the tool's update script
