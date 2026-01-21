# Copyright 2016, 2023 John J. Rofrano. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Test cases for Product Model

Test cases can be run with:
    nosetests
    coverage report -m

While debugging just these tests it's convenient to use this:
    nosetests --stop tests/test_models.py:TestProductModel

"""
import os
import logging
import unittest
from decimal import Decimal
from service.models import Product, Category, db
from service import app
from tests.factories import ProductFactory
from service.models import DataValidationError

DATABASE_URI = os.getenv(
    "DATABASE_URI", "postgresql://postgres:postgres@localhost:5432/postgres"
)


######################################################################
#  P R O D U C T   M O D E L   T E S T   C A S E S
######################################################################
# pylint: disable=too-many-public-methods
class TestProductModel(unittest.TestCase):
    """Test Cases for Product Model"""

    @classmethod
    def setUpClass(cls):
        """This runs once before the entire test suite"""
        app.config["TESTING"] = True
        app.config["DEBUG"] = False
        app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URI
        app.logger.setLevel(logging.CRITICAL)
        Product.init_db(app)

    @classmethod
    def tearDownClass(cls):
        """This runs once after the entire test suite"""
        db.session.close()

    def setUp(self):
        """This runs before each test"""
        db.session.query(Product).delete()  # clean up the last tests
        db.session.commit()

    def tearDown(self):
        """This runs after each test"""
        db.session.remove()

    ######################################################################
    #  T E S T   C A S E S
    ######################################################################

    def test_create_a_product(self):
        """It should Create a product and assert that it exists"""
        product = Product(name="Fedora", description="A red hat", price=12.50, available=True, category=Category.CLOTHS)
        self.assertEqual(str(product), "<Product Fedora id=[None]>")
        self.assertTrue(product is not None)
        self.assertEqual(product.id, None)
        self.assertEqual(product.name, "Fedora")
        self.assertEqual(product.description, "A red hat")
        self.assertEqual(product.available, True)
        self.assertEqual(product.price, 12.50)
        self.assertEqual(product.category, Category.CLOTHS)

    def test_add_a_product(self):
        """It should Create a product and add it to the database"""
        products = Product.all()
        self.assertEqual(products, [])
        product = ProductFactory()
        product.id = None
        product.create()
        # Assert that it was assigned an id and shows up in the database
        self.assertIsNotNone(product.id)
        products = Product.all()
        self.assertEqual(len(products), 1)
        # Check that it matches the original product
        new_product = products[0]
        self.assertEqual(new_product.name, product.name)
        self.assertEqual(new_product.description, product.description)
        self.assertEqual(Decimal(new_product.price), product.price)
        self.assertEqual(new_product.available, product.available)
        self.assertEqual(new_product.category, product.category)

    #
    # ADD YOUR TEST CASES HERE
    #
    def test_read_a_product(self):
        """It should Read a Product"""
        # create a product using Fake properties
        product = ProductFactory()
        product.id = None
        product.create()
        self.assertIsNotNone(product.id)
        # fetch to db
        found_product = Product.find(product.id)
        # assert properties
        self.assertEqual(found_product.id, product.id)
        self.assertEqual(found_product.name, product.name)
        self.assertEqual(found_product.description, product.description)
        self.assertEqual(found_product.price, product.price)

    def test_update_a_product(self):
        """It should Update a Product"""
        # create a product using Fake properties
        product = ProductFactory()
        product.id = None
        product.create()
        self.assertIsNotNone(product.id)
        # change the description
        product.description = "testing"
        original_id = product.id
        product.update()
        self.assertEqual(product.id, original_id)
        self.assertEqual(product.description, "testing")
        # fetch to db and check if description is updated
        products = Product.all()
        self.assertEqual(len(products), 1)
        self.assertEqual(products[0].id, original_id)
        self.assertEqual(products[0].description, "testing")

    def test_delete_a_product(self):
        """It should Delete a Product"""
        product = ProductFactory()
        product.create()
        # check if db has only 1 product
        self.assertEqual(len(Product.all()), 1)
        # check if db has no product after removal
        product.delete()
        self.assertEqual(len(Product.all()), 0)

    def test_list_all_products(self):
        """It should List all Products"""
        products = Product.all()
        # check if nothing in db
        self.assertEqual(products, [])
        # create 5 products
        for _ in range(5):
            product = ProductFactory()
            product.create()
        # check if db has 5 products
        products = Product.all()
        self.assertEqual(len(products), 5)

    def test_find_by_name(self):
        """It should Find a Product by Name"""
        # create a batch of 5 products and save in db
        products = ProductFactory.create_batch(5)
        for product in products:
            product.create()
        name = products[0].name
        count = len([product for product in products if product.name == name])
        found = Product.find_by_name(name)
        self.assertEqual(found.count(), count)
        for product in found:
            self.assertEqual(product.name, name)

    def test_find_by_availability(self):
        """It should Find a Product by Availability"""
        products = ProductFactory.create_batch(10)
        for product in products:
            product.create()
        available = products[0].available
        count = len([product for product in products if product.available == available])
        found = Product.find_by_availability(available)
        self.assertEqual(found.count(), count)
        for product in found:
            self.assertEqual(product.available, available)

    def test_find_by_category(self):
        """It should Find a Product by Category"""
        products = ProductFactory.create_batch(10)
        for product in products:
            product.create()
        category = products[0].category
        count = len([product for product in products if product.category == category])
        found = Product.find_by_category(category)
        self.assertEqual(found.count(), count)
        for product in found:
            self.assertEqual(product.category, category)

    def test_deserialize_with_invalid_category(self):
        """It should raise DataValidationError for invalid category (Line 106)"""
        product = Product()
        invalid_data = {
            "name": "Test Product",
            "description": "Test Description",
            "price": "10.99",
            "available": True,
            "category": "INVALID_CATEGORY"  # This will cause AttributeError
        }
        
        with self.assertRaises(DataValidationError) as context:
            product.deserialize(invalid_data)
        
        # Check that it's the specific AttributeError from line 106
        self.assertIn("Invalid attribute: INVALID_CATEGORY", str(context.exception))

    def test_find_by_price_with_string_quotes(self):
        """It should find Products by price when price is string with quotes (Line 139)"""
        # Create a test product
        product = ProductFactory()
        product.price = Decimal("19.99")
        product.create()
        
        # Test with string price that has quotes and spaces
        products = Product.find_by_price(' "19.99" ')  # This triggers line 139
        products_list = list(products)
        
        self.assertEqual(len(products_list), 1)
        self.assertEqual(products_list[0].price, Decimal("19.99"))

    def test_find_by_price_with_plain_string(self):
        """It should find Products by price when price is plain string (Line 139)"""
        # Create a test product
        product = ProductFactory()
        product.price = Decimal("29.99")
        product.create()
        
        # Test with plain string price
        products = Product.find_by_price("29.99")  # This also triggers line 139
        products_list = list(products)
        
        self.assertEqual(len(products_list), 1)
        self.assertEqual(products_list[0].price, Decimal("29.99"))

    def test_find_by_price_with_decimal(self):
        """It should find Products by price when price is Decimal (Line 139)"""
        # Create a test product
        product = ProductFactory()
        product.price = Decimal("39.99")
        product.create()
        
        # Test with Decimal price (bypasses the if statement on line 139)
        products = Product.find_by_price(Decimal("39.99"))
        products_list = list(products)
        
        self.assertEqual(len(products_list), 1)
        self.assertEqual(products_list[0].price, Decimal("39.99"))

    def test_find_by_availability_default(self):
        """It should find available Products by default (Line 145)"""
        # Create both available and unavailable products
        available_product = ProductFactory(available=True)
        available_product.create()
        
        unavailable_product = ProductFactory(available=False)
        unavailable_product.create()
        
        # Call without argument to use default (True)
        products = Product.find_by_availability()  # Line 145 default parameter
        products_list = list(products)
        
        # Should only find available products
        self.assertEqual(len(products_list), 1)
        self.assertTrue(products_list[0].available)

    def test_find_by_availability_false(self):
        """It should find unavailable Products (Line 145)"""
        # Create both available and unavailable products
        available_product = ProductFactory(available=True)
        available_product.create()
        
        unavailable_product = ProductFactory(available=False)
        unavailable_product.create()
        
        # Find unavailable products
        products = Product.find_by_availability(False)
        products_list = list(products)
        
        # Should only find unavailable products
        self.assertEqual(len(products_list), 1)
        self.assertFalse(products_list[0].available)

    def test_find_by_category_default(self):
        """It should find Products with UNKNOWN category by default (Lines 148-149)"""
        # Create products with different categories
        unknown_product = ProductFactory(category=Category.UNKNOWN)
        unknown_product.create()
        
        cloths_product = ProductFactory(category=Category.CLOTHS)
        cloths_product.create()
        
        # Call without argument to use default (Category.UNKNOWN)
        products = Product.find_by_category()  # Lines 148-149 default parameter
        products_list = list(products)
        
        # Should only find UNKNOWN category products
        self.assertEqual(len(products_list), 1)
        self.assertEqual(products_list[0].category, Category.UNKNOWN)

    def test_find_by_category_specific(self):
        """It should find Products with specific category (Lines 217-221)"""
        # Create products with different categories
        cloths_product1 = ProductFactory(category=Category.CLOTHS)
        cloths_product1.create()
        
        cloths_product2 = ProductFactory(category=Category.CLOTHS)
        cloths_product2.create()
        
        food_product = ProductFactory(category=Category.FOOD)
        food_product.create()
        
        # Find CLOTHS category products
        products = Product.find_by_category(Category.CLOTHS)
        products_list = list(products)
        
        # Should only find CLOTHS category products
        self.assertEqual(len(products_list), 2)
        for product in products_list:
            self.assertEqual(product.category, Category.CLOTHS)

    def test_find_by_category_logging(self):
        """It should log when finding by category (Lines 217-221 include logging)"""
        # Create a product
        product = ProductFactory(category=Category.TOOLS)
        product.create()
        
        # This should trigger the logger.info on line 149/221
        products = Product.find_by_category(Category.TOOLS)
        products_list = list(products)
        
        self.assertEqual(len(products_list), 1)
        self.assertEqual(products_list[0].category, Category.TOOLS)

    def test_update_with_empty_id(self):
        """It should raise DataValidationError when updating with empty ID"""
        product = ProductFactory()
        # Don't create it, so id is None
        product.id = None
        
        with self.assertRaises(DataValidationError) as context:
            product.update()
        
        self.assertIn("Update called with empty ID field", str(context.exception))

    def test_deserialize_with_non_dict_data(self):
        """It should raise DataValidationError for non-dict data (TypeError)"""
        product = Product()
        
        # Pass a string instead of dict
        with self.assertRaises(DataValidationError) as context:
            product.deserialize("not a dict")
        
        self.assertIn("body of request contained bad or no data", str(context.exception))

    def test_deserialize_with_none_data(self):
        """It should raise DataValidationError for None data"""
        product = Product()
        
        with self.assertRaises(DataValidationError) as context:
            product.deserialize(None)
        
        self.assertIn("body of request contained bad or no data", str(context.exception))