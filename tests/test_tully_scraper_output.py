import pytest
import os
import pandas as pd

#
# TODO RUN YOUR SCRAPER BEFORE RUNNING THESE TESTS!
#

FILE = "cache/tullys_menu.csv"

def test_should_pass():
    print("\nAlways True!")
    assert True

def test_tullyscraper_menu_csv_file_exists():
    print(f"Expect {FILE} to exist!")
    assert os.path.exists(FILE) 

def test_tullyscraper_menu_csv_file_proper_rows_and_cols():
    df = pd.read_csv(FILE)
    print("We expect 113 rows and 4 columns")
    assert df.shape == (113, 4)
    

# IF YOU NEED TO DEBUG A TEST
# 1. Place a breakpoint on the line below
# 2. call the function you want to debug below the if statement
# Run this file with debugging
if __name__ == "__main__":
    test_should_pass()
