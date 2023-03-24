<!--
The original challenge brief, preserved verbatim from the repository's initial
state so that the work in this repository can be checked against what was
actually asked. The project README now documents the implementation.
-->

## Instructions
For this project, you will complete the following coding challenges. Each challenge is a standalone problem and should function independently of the other challenges. When adding code to this repository, assume this is a production codebase: use best practices and style accordingly. Clone this repository then push it to your github **(DO NOT FORK)** and send us a link to the project. Create a unique branch for each problem you are solving. The branches should use the title of the challenge named with the following convention: "challenge-#-name" (eg "challenge-1-inventory-dates", "challenge-2-deactivate-order" etc.). Your code should be free of basic linting errors and shouldn't have any unused imports. **If you are doing any formatting, it should happen on a different commit than where you commited your answers to the challenge.** Do not add any other packages to this project to complete the work. You will be expected to write basic tests so we can validate your code is functioning with the correct inputs and outputs. Once you complete each challenge you will make a PR to your repository on your github for the branch/challenge you completed.

## Setup (For Linux/Unix terminals)
1. Ensure that you have Docker Desktop installed on your computer
2. Ensure that you have venv installed globally
3. From the top level directory of this project (where manage.py is located), type: 
    1. `docker compose --file docker-compose.dev.yml up -d`
    2. `chmod +x start.sh`
    3. `./start.sh`
    4. `source .venv/bin/activate`

## Setup (For Windows Powershell)
1. Ensure that you have Docker Desktop installed on your computer
2. Ensure that you have Python and venv installed on your system, and both are accessible from your system's PATH.
3. From the top level directory of this project (where manage.py is located), type: 
    1. `docker-compose --file docker-compose.dev.yml up -d`
4. Run the start.bat file
5. Activate your venv `.venv\Scripts\Activate.ps1`


### Challenge 1 Inventory Dates:
Create a view that lists inventory items created after a certain day.

### Challenge 2 Deactivate Order:
Write a view "DeactivateOrderView" that sets the is_active state on an order.

### Challenge 3 Embargo Date:
Write an endpoint that lists orders that are between a particular start and embargo date.

### Challenge 4 Profile Model:
Add an app "profiles". The following should be a production ready model. Create a model "UserProfile" that contains: username, email, password, first name, last name, date joined, last login, is staff, is superuser, is admin, is active. On this model the username field should be set to use the email address for authenticating. This model should also at minimum include functions: get_full_name(), get_username(), is_authenticated(). You should also add a field "avatar" that will contain a thumbnail image of a user's avatar. Set the UserProfile model as the default Django user model.

Finally, create a basic admin section for order and inventory apps.

### Challenge 5 Inventory Pagination:
Add pagination to InventoryListView that displays 3 items per request. Pagination should use an offset and a limit.

### Challenge 6 Tags on Orders:
Create an endpoint that lists all tags associated with an order.

### Challenge 7 Orders on Tag:
Create an endpoint that lists all the orders associated with a particular tag.

### Challenge 8 Create Inventory Item:
Create a file "challenge_8_explanation.md" in the top level folder of this project. Pretend you are working with a junior developer. They are stuck and you are going to explain how they would solve the problem they are working on. They should be able to walk away from your explanation with functional code. Here is what they are trying to do:
- Add an item to Inventory through the API
- Their metadata should include these fields (year, actors, imdb_rating, rotten_tomatoes_rating, film_locations)
