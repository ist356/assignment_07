# IST356 Assignment 07 (assignment_07)

## Meta Section

### Prerequisites 

Before starting this assignment you must get the requirements installed. 

**NOTE: This should be done already as part of the scraping unit.**

Install the assignemnt python requirements:

1. From VS Code, open a terminal: Menu => Terminal => New Terminal
2. In the terminal, type and enter: `pip install -r requirements.txt`
3. Get playwright running with the chromium browser: `python -m playwright install`

### Running Tests

There are some code and tests already working in this assignment. These are sanity checks to ensure VS Code is configured properly.

1. Open **Testing** in the activity bar: Menu => View => Testing
2. Open the **>** by clicking on it next to **assignment_06**. Keep clicking on **>** until you see **test_should_pass** in each  **test_????.py** file
4. Click the Play button `|>` next to **test_should_pass** to execute the test. 
5. A green check means the test code ran and the test has passed.
6. A red X means the test code ran but the test has failed. When a test fails you will be given an error message and stack trace with line numbers.

### Debugging

Odds are you will need to use some debugging strategies in this assignment. 

- To debug a test:
    - call the test function in the `if __name__ == '__main__':` block at the bottom of the test file.
    - then set a breakpoint in the test function and run the test as you would any other python program.
    - run the file with debugging: Menu => Run => Start Debugging

- You will not need streamlit for this assignment.

## Assignment: Scraping a Restaurant Menu

Ever wonder how services like Google and Yelp are able to show restaraunt menu items? They use web scraping, of course.

In this assignment you will scrape the menu items from a restaurant website. The website we will scrape is Tully's Good Times.

[https://www.tullysgoodtimes.com/menus/](https://www.tullysgoodtimes.com/menus/)

To future proof this assignment, I've captured the site at the time of assignment creation using the Wayback Machine. You can access the site here:

[https://web.archive.org/web/20241111165815/https://www.tullysgoodtimes.com/menus/](https://web.archive.org/web/20241111165815/https://www.tullysgoodtimes.com/menus/)

This will ensure any solution code will still work in the future! 

### The objective 

Scrape the menu off the site, and build a CSV file consisting of the menu items. The CSV file should have the following columns:

- category: where the item sits in the menu e.g. "Burgers"
- name: of the item
- price: of the item
- description: of the item

The input is the webpage, and the output is a CSV of all the menu items on the page. There are no interactions. Consider this just a data extraction task.

## The Approach

Once again, we will take a bottom up approach. Commit your code after each part. Push when you are done with the code and the reflection.

### Part 0: check out menuitem.py

The `menuitem.py` introduces a Python Dataclass [https://docs.python.org/3/library/dataclasses.html](https://docs.python.org/3/library/dataclasses.html) to represent a menu item. Think of a dataclass like a Python dictionary but with a fixed structure. It's a great way to represent structured data in Python where the elements in the structure are required and should obey a specific data types, like a float type for prices.

Review and play around with the main code in the file, running the examples. Before you proceed, make sure you have a good understanding how to create a menu item using the dataclass and convert it back to a dictionary. You will need to know how to do this!

### Part 1: Complete the functions in menuitemextractor.py

Next, work on the functions in `menuitemextractor.py` these functions will get the menu text extracted from the website and convert it to a `MenuItem` dataclass object.

There are three functions to implement:

#### 1. `clean_price(price: str) --> float:`

This function should take a string price "$9.99" and returns a float 9.99. The price string may have a dollar sign or commas that need to be removed before the conversion. We have written something similar before.

#### 2. `clean_scraped_text(scraped_text: str) --> list[str]:`

This function should take the scraped text and clean it up, by removing any unwanted data.  First split the text on a newline `"\n"` so you have a list of strings, you will only add the desired lines to the cleaned list. "Unwanted" lines that should be omitted include:
  - empty lines of text
  - lines of text that are just "NEW!" or "NEW"
  - lines of text that are indications of Spicy, Vegan, Gluten-free, or peanut items "S", "V", "GS", "P"

what should be returned back should be a list of only the desired text. There should be 2-3 items in the list.

  - first item will be the name of the item
  - second item will be the price of the item
  - third item will be the description of the item (if there is a description)

See `TEST_DATA` in the `test_menuitemextractor.py` file for examples of the text you will be working with.

#### 3. `extract_menu_items( title: str, scraped_text: str) --> MenuItem`

This function builds a `MenuItem` dataclass object from what was scraped.
  - The title is the scraped menu category, e.g. "Pastas"
  - The scraped_text is the text of the menu item. Again, refer to `TEST_DATA` in the `test_menuitemextractor.py` file for examples of the text you will be working with.

In the function body, you should call `clean_scraped_text` to get the cleaned text for each item, then create a `MenuItem` object for each item. Do not forget to call `clean_price` to get the price as a float. Finally  check to see if there is a menu description (cleaned list of text has more than 2 items), when there is no description, use "No desciption available" as the description.

Use the tests in `tests/test_menuitemextractor.py` to verify your code is correct and in most cases, help you figure out what to do.

### Part 2: tully_scraper.py

The `tully_scraper.py` file is your main program. This is where you will use playwright to scrape the menu items from the website and create the CSV file.

#### CSS Selectors

What is scraping without CSS selectors? 

CSS selectors you'll need to identify:

1. `title` a selector for the menu section title.

Example inner_text():

  Starters & Snacks

2. `item` a selector for the text of the food item. This will conain the name, price, and description of the item.

Example inner_text()::

    NEW!

    Tully Tots

    $11.79

    Made from scratch with shredded potatoes, cheddar-jack cheese and Romano...

#### Algorithm

Here's a working strategy for the scraper:

  go to the website (or wayback machine version)
  for each `title` (menu section) selected on the page
    go down two elements to get the element that contains the menu items (its a `<div class="row">` tag)
    for each item in the all the selected `menu` items
      get the text of the item
      call `extract_menu_items` to get a `MenuItem` object
      add the dict version `MenuItem` to a list

   after the for loops, you have a list of dict for all the menu items on the page.
   create a pandas dataframe from the list of dict
   write the dataframe to a CSV file `cache/tullys_menu.csv`
   
#### Running test_tully_scraper_output.py

After you get the scraper working, you can run the tests in `test_tully_scraper.py` to verify your code is correct.

NOTE: Those tests do not execute the tully scraper, the only check for the CSV file. You will need to run the scraper to generate the CSV file before running the tests!!!


## Turning it in 

### Commit Requirements

If you followed directions, you should have your 2 git commits minimum. Its okay to have more, but you should have at least 2.


- Make sure tests pass and code works as expected
- Write your reflection in `reflection.md`
- Commit your changes: VS Code -> menu -> View -> Source Control -> Enter Commit message -> Click "Commit"
- Push your changes: VS Code -> menu -> View -> Source Control -> Click "Sync Changes"

## Grading 

🤖 Beep, Boop. This assignment is bot-graded! When you push your code to GitHub, my graderbot is notified there is something to grade. The bot then takes the following actions:

1. Your assignment repository is cloned from Github
2. The bot checks your code and commits according to guidelines outlined in `assignment-criteria.json` (it runs tests, checking code correctness, etc.)
3. The bot reads your `reflection.md` and provides areas for improvement (based on the instructions in the file).
4. A grade is assigned by the bot. Feedback is generated including justification for the grade given.
5. The grade and feedback are posted to Blackboard.

You are welcome to review the bot's feedback and improve your submission as often as you like.

**NOTE: ** Consider this an experiment in the future of education. The graderbot is an AI teaching assistant. Like a human grader, it will make mistakes. Please feel free to question the bots' feedback! Do not feel as if you should gamify the bot. Talk to me! Like a person, we must teach it how to do its job effectively. 
