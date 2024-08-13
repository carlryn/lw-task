# Script for creating a DynamoDB table and populating it with data.

import boto3
from botocore.exceptions import ClientError
import logging

logger = logging.getLogger(__name__)


class CustomerInformation:
    """Encapsulates an Amazon DynamoDB table of customer data."""

    def __init__(self, dyn_resource):
        """
        :param dyn_resource: A Boto3 DynamoDB resource.
        """
        self.dyn_resource = dyn_resource
        # The table variable is set during the scenario in the call to
        # 'exists' if the table exists. Otherwise, it is set by 'create_table'.
        self.table = None

    def create_table(self, table_name: str):
        """
        Creates an Amazon DynamoDB table that can be used to store movie data.
        The table uses the release year of the movie as the partition key and the
        title as the sort key.

        :param table_name: The name of the table to create.
        :return: The newly created table.
        """
        try:
            self.table = self.dyn_resource.create_table(
                TableName=table_name,
                KeySchema=[
                    {"AttributeName": "customer", "KeyType": "HASH"},  # Partition key
                    {"AttributeName": "domain", "KeyType": "RANGE"},  # Sort key
                ],
                AttributeDefinitions=[
                    {"AttributeName": "customer", "AttributeType": "S"},
                    {"AttributeName": "domain", "AttributeType": "S"},
                ],
                BillingMode="PAY_PER_REQUEST",
            )
            self.table.wait_until_exists()
            print("Table created: ", table_name)
        except ClientError as err:
            logger.error(
                "Couldn't create table %s. Here's why: %s: %s",
                table_name,
                err.response["Error"]["Code"],
                err.response["Error"]["Message"],
            )
            raise
        else:
            return self.table


def create_table(dyn_resource, table_name: str) -> None:
    # Creates a dynamodb table
    customer_information = CustomerInformation(dyn_resource)
    customer_information.create_table(table_name)


def insert_data(dyn_resource, table_name, file_path) -> None:
    # Inserts example data into dynamo db from file.
    with open(file_path, "r") as file:
        content = file.read()

    table = dyn_resource.Table(table_name)
    table.put_item(Item={"customer": "Shoby", "domain": "advertisement", "info": content})


if __name__ == "__main__":
    table_name = "CustomerInformation"
    dyn_client = boto3.client("dynamodb")
    dyn_resource = boto3.resource("dynamodb")
    try:
        table = create_table(dyn_client, table_name)
    except dyn_client.exceptions.ResourceInUseException:
        print("Table exists, continuing")

    # Let's insert data
    print("Inserting data")
    insert_data(dyn_resource, table_name, "shoby_brand_info.txt")
