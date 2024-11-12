if __name__ == "__main__":
    import sys
    sys.path.append('code')
    from menuitem import MenuItem
else:
    from code.menuitem import MenuItem


def clean_price(price:str) -> float:
    pass # TODO  replace with code

def clean_scraped_text(scraped_text: str) -> list[str]:
    pass # TODO  replace with code

def extract_menu_item(title:str, scraped_text: str) -> MenuItem:
    pass # TODO  replace with code



if __name__=='__main__':
    pass
