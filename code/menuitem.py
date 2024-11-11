from dataclasses import dataclass, asdict

@dataclass
class MenuItem:
    # these are built-in properties
    category: str
    name: str
    price: float
    description: str

    # convert to a dictionary
    def to_dict(self):
        return asdict(self)

    @staticmethod
    def from_dict(data):
        return MenuItem(**data)
    
if __name__=='__main__':
    # example of howto use the dataclass

    # create a new MenuItem    
    mozz = MenuItem(name = "Mozzarella Sticks", 
                    price = 8.99, 
                    category="Apps", 
                    description="Fried cheese sticks served with marinara sauce.")

    # can assign a new category
    mozz.category = "Appetizers"
    print(mozz)
    # convert back to a dictionary
    print(mozz.to_dict())

    # create a new MenuItem from a dictionary
    burger = MenuItem.from_dict({"name": "Burger", 
                                 "price": 9.99, 
                                 "description": "A delicious burger.", 
                                 "category": "Entrees"})
    print(burger)

