import pytest 
from code.menuitem import MenuItem
from code.menuitemextractor import clean_scraped_text, clean_price, extract_menu_item


TEST_DATA = [
        '''
NEW!

Tully Tots

$11.79

Made from scratch with shredded potatoes, cheddar-jack cheese and Romano cheese all rolled up and deep-fried. Served with a spicy cheese sauce.
        ''',

        '''Super Nachos

$15.49
GS

Tortilla chips topped with a mix of spicy beef and refried beans, nacho cheese sauce, olives, pico de gallo, jalapeños, scallions and shredded lettuce. Sour cream and salsa on the side. Add guacamole $2.39

        ''',
        '''Veggie Quesadilla

$11.99
V

A flour tortilla packed with cheese, tomatoes, jalapeños, black olives and scallions. Served with sour cream and pico de gallo.
Add chicken $2.99 | Add guacamole $2.39
''',
'''Kid's Burger & Fries

$6.99
'''
]

UNWANTED = ["NEW", "NEW!", "GS", "V", "P", "S"]

def test_should_pass():
    print("\nAlways True!")
    assert True

def test_clean_price():
    text_expects = [
        ("$11.79", 11.79),
        ("$15,000", 15000),
        ("$.99", .99),
        ("6.99", 6.99),
        ("$6", 6)
    ]
    for text, expect in text_expects:
        actual = clean_price(text)
        print(f"For text {text}, Expect: {expect}, Actual: {actual}")
        assert expect == actual


def test_clean_scraped_text_no_empties():
    for text in TEST_DATA:
        cleaned = clean_scraped_text(text)
        print("CLEANED", cleaned)
        print("Checking there are no empties in cleaned..")
        assert len([item for item in cleaned if len(item)==0]) == 0


def test_clean_scraped_text_no_unwanted():
    for text in TEST_DATA:
        cleaned = clean_scraped_text(text)
        print("CLEANED", cleaned)
        for u in UNWANTED:
            print(f"Checking there are no {u} unwanted items in cleaned")
            assert u not in cleaned

def test_clean_scraped_text_at_least_2_items():
    for text in TEST_DATA:
        cleaned = clean_scraped_text(text)
        print("CLEANED", cleaned)
        print("Checking there are at least 2 items in cleaned")
        assert len(cleaned) >= 2


def test_extract_menu_item_expect_type_MenuItem():
    for text in TEST_DATA:
        item = extract_menu_item("TEST", text)
        print(f"Expect: {item} to be a MenuItem type")
        assert isinstance(item, MenuItem)        

def test_extract_menu_item_expect_No_desciption_available():
    text = TEST_DATA[-1] # this one has no description
    item = extract_menu_item("TEST", text)
    print(f"Expect: {item} to be a MenuItem type")
    assert item.description.lower().startswith("no description available")

def test_extract_menu_item_expect_price_1549():
    text = TEST_DATA[1] # this one has a price of 15.49
    item = extract_menu_item("TEST", text)
    print(f"Expect: 15.49 to be a {item.price}")
    assert item.price == 15.49



# IF YOU NEED TO DEBUG A TEST
# 1. Place a breakpoint on the line below
# 2. call the function you want to debug below the if statement
# Run this file with debugging
if __name__ == "__main__":
    test_should_pass()
