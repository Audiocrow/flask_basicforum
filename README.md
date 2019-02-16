# Forum Project for CPSC476 Web Back-End
A forum with very basic functionality using Flask and sqlite with users, threads, and posts. Authentication is performed with basic HTTPAuth, but passwords are plaintext. 

There are 3 branches for this project (Project1, Project2, Project3). Project2 and Project3 are variations of Project1 with higher scalability.   
## Overview
| Route                          | Description                                       | Methods   | Requires Auth? |
|--------------------------------|---------------------------------------------------|-----------|----------------|
| /forums                        | View or create forums.                            | GET, POST | Yes for POST   |
| /forums/<forum_id>             | View or create threads under the specified forum. | GET, POST | Yes for POST   |
| /forums/<forum_id>/<thread_id> | View or create posts in the specified thread.     | GET, POST | Yes for POST   |
| /users                         | Create a new user, or update the user's password. | POST, PUT | Yes for PUT    |  
  
Forums, posts, and threads cannot be deleted or edited. Users cannot be deleted but their passwords can be modified. 
### Project 1 Branch  
The first implementation of the site.  
### Project 2 Branch  
Uses clustering on thread_id to improve write-scalability. Since this is a simple practice project and not intended to be a perfectly functional website, the different clusters of sqlite servers are all hosted locally.  
This required the implementation of GUIDs to identify forums, threads, and posts amongst different clusters.
### Project 3 Branch
Uses ScyllaDB (a Python wrapper for Cassandra) instead of sqlite - for NoSQL practice. For practice this was a branch of Project 1 and not Project 2, but NoSQL typically only becomes worthwhile when clustering because joins become inviable.

